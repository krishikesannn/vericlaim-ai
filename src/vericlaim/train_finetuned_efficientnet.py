"""Leakage-aware fine-tuning experiment for VeriClaim's image model.

This script deliberately creates a *candidate* artifact and never overwrites
the deployed model.  It keeps the supplied claim images only, uses safe image
augmentation, class-balanced focal loss, and perceptual-group folds.  Promote
the candidate only after its grouped validation and holdout results improve.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedGroupKFold

from .train import choose_classification_threshold, discover, metrics
from .validation import build_perceptual_groups
from .features import extract_features


def image_paths_dataset(paths: list[Path], labels: np.ndarray, image_size: int, training: bool):
    import tensorflow as tf

    def decode(path, label):
        raw = tf.io.read_file(path)
        image = tf.io.decode_image(raw, channels=3, expand_animations=False)
        image.set_shape([None, None, 3])
        image = tf.image.resize_with_pad(image, image_size, image_size)
        return tf.cast(image, tf.float32), tf.cast(label, tf.float32)

    dataset = tf.data.Dataset.from_tensor_slices(([str(path) for path in paths], labels))
    if training:
        dataset = dataset.shuffle(len(paths), seed=42, reshuffle_each_iteration=True)
    return dataset.map(decode, num_parallel_calls=tf.data.AUTOTUNE).batch(16).prefetch(tf.data.AUTOTUNE)


def class_balanced_focal_loss(fraud_count: int, nonfraud_count: int, beta: float = 0.9999, gamma: float = 2.0):
    """Binary focal loss with effective-number class weights (Cui et al.)."""
    import tensorflow as tf

    counts = np.asarray([nonfraud_count, fraud_count], dtype=np.float64)
    effective = 1.0 - np.power(beta, counts)
    weights = (1.0 - beta) / np.clip(effective, 1e-12, None)
    weights = weights / weights.sum() * 2.0
    nonfraud_weight, fraud_weight = map(float, weights)

    def loss(y_true, y_pred):
        y_true = tf.cast(y_true, tf.float32)
        y_pred = tf.clip_by_value(tf.cast(y_pred, tf.float32), 1e-6, 1.0 - 1e-6)
        p_t = tf.where(y_true > 0.5, y_pred, 1.0 - y_pred)
        alpha = tf.where(y_true > 0.5, fraud_weight, nonfraud_weight)
        return tf.reduce_mean(-alpha * tf.pow(1.0 - p_t, gamma) * tf.math.log(p_t))

    loss.__name__ = "class_balanced_focal_loss"
    return loss


def build_model(image_size: int, fine_tune_layers: int, learning_rate: float):
    import tensorflow as tf

    augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.05),
        tf.keras.layers.RandomZoom(0.10, 0.10),
        tf.keras.layers.RandomContrast(0.10),
    ], name="safe_claim_augmentation")
    backbone = tf.keras.applications.EfficientNetV2B0(
        include_top=False, weights="imagenet", input_shape=(image_size, image_size, 3),
        pooling="avg", include_preprocessing=True,
    )
    backbone.trainable = True
    # Fine-tune only the last portion to avoid overfitting the small minority.
    for layer in backbone.layers[:-fine_tune_layers]:
        layer.trainable = False
    # Frozen batch-normalisation is materially more stable for small batches.
    for layer in backbone.layers:
        if isinstance(layer, tf.keras.layers.BatchNormalization):
            layer.trainable = False
    inputs = tf.keras.Input((image_size, image_size, 3), name="claim_image")
    x = augmentation(inputs)
    x = backbone(x, training=False)
    x = tf.keras.layers.Dropout(0.35)(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid", name="fraud_probability")(x)
    model = tf.keras.Model(inputs, outputs, name="vericlaim_finetuned_efficientnetv2b0")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss=None,  # set per fold because the class counts differ by fold
        metrics=[tf.keras.metrics.AUC(curve="PR", name="pr_auc"), tf.keras.metrics.AUC(name="roc_auc")],
    )
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("models/finetuned_efficientnet_candidate"))
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--folds", type=int, default=5)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--patience", type=int, default=3)
    parser.add_argument("--fine-tune-layers", type=int, default=30)
    parser.add_argument("--learning-rate", type=float, default=1e-5)
    parser.add_argument("--perceptual-distance", type=int, default=6)
    parser.add_argument("--beta", type=float, default=0.9999)
    parser.add_argument("--gamma", type=float, default=2.0)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    started = time.time()

    import tensorflow as tf

    tf.keras.utils.set_random_seed(42)
    train_paths, y_train = discover(args.data_root, "train")
    test_paths, y_test = discover(args.data_root, "test")
    if not train_paths or not test_paths:
        raise SystemExit("Expected train/{Fraud,Non-Fraud} and test/{Fraud,Non-Fraud}")
    hashes = [extract_features(path)[1].perceptual_hash for path in train_paths]
    groups = build_perceptual_groups(hashes, args.perceptual_distance)
    splitter = StratifiedGroupKFold(n_splits=args.folds, shuffle=True, random_state=42)
    oof = np.zeros(len(y_train), dtype=np.float32)
    test_scores = np.zeros(len(y_test), dtype=np.float32)
    folds: list[dict] = []

    for fold, (fit, validation) in enumerate(splitter.split(train_paths, y_train, groups), start=1):
        tf.keras.backend.clear_session()
        model = build_model(args.image_size, args.fine_tune_layers, args.learning_rate)
        fraud = int(y_train[fit].sum())
        loss = class_balanced_focal_loss(fraud, len(fit) - fraud, args.beta, args.gamma)
        model.compile(
            optimizer=tf.keras.optimizers.Adam(learning_rate=args.learning_rate), loss=loss,
            metrics=[tf.keras.metrics.AUC(curve="PR", name="pr_auc"), tf.keras.metrics.AUC(name="roc_auc")],
        )
        checkpoint = args.output_dir / f"fold_{fold}.keras"
        callbacks = [
            tf.keras.callbacks.EarlyStopping(monitor="val_pr_auc", mode="max", patience=args.patience, restore_best_weights=True),
            tf.keras.callbacks.ModelCheckpoint(checkpoint, monitor="val_pr_auc", mode="max", save_best_only=True),
        ]
        model.fit(
            image_paths_dataset([train_paths[i] for i in fit], y_train[fit], args.image_size, True),
            validation_data=image_paths_dataset([train_paths[i] for i in validation], y_train[validation], args.image_size, False),
            epochs=args.epochs, verbose=2, callbacks=callbacks,
        )
        best = tf.keras.models.load_model(checkpoint, compile=False)
        oof[validation] = best.predict(image_paths_dataset([train_paths[i] for i in validation], y_train[validation], args.image_size, False), verbose=0).ravel()
        test_scores += best.predict(image_paths_dataset(test_paths, y_test, args.image_size, False), verbose=0).ravel() / args.folds
        folds.append({"fold": fold, "model": checkpoint.name, "fit_images": int(len(fit)), "validation_images": int(len(validation)), "fit_fraud": fraud})

    threshold = choose_classification_threshold(y_train, oof)
    report = {
        "project": "VeriClaim AI", "candidate": True,
        "model": "Fine-tuned EfficientNetV2B0 with safe augmentation and class-balanced focal loss",
        "dataset_policy": "Only supplied claim images; no external claim dataset or synthetic images.",
        "validation": {"method": "5-fold StratifiedGroupKFold using perceptual image groups", "groups": int(len(np.unique(groups)))},
        "training": {"fine_tune_layers": args.fine_tune_layers, "learning_rate": args.learning_rate, "augmentation": ["horizontal flip", "small rotation", "small zoom", "small contrast"], "loss": "class-balanced focal", "beta": args.beta, "gamma": args.gamma},
        "folds": folds, "classification_threshold": float(threshold),
        "oof_metrics": metrics(y_train, oof, threshold), "test_metrics": metrics(y_test, test_scores, threshold),
        "elapsed_seconds": round(time.time() - started, 1),
    }
    (args.output_dir / "candidate_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
