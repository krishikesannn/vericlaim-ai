"""Optional transfer-learning path for a GPU/cloud training run.

The shipped CPU model keeps the demo dependable. This module implements the
neural-network alternative requested by the use case when TensorFlow is
available. Install requirements-deep.txt before running it.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np

from .train import choose_threshold, discover, extract_many, metrics
from .validation import build_perceptual_groups, grouped_holdout_indices


def main() -> None:
    try:
        import tensorflow as tf
    except ImportError as exc:
        raise SystemExit("Install requirements-deep.txt to run transfer learning") from exc

    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("models/deep"))
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--epochs", type=int, default=18)
    parser.add_argument("--fraud-batch-share", type=float, default=0.35)
    parser.add_argument("--validation-folds", type=int, default=5)
    parser.add_argument("--perceptual-distance", type=int, default=6)
    parser.add_argument("--recall-target", type=float, default=0.75)
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache"))
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    if not 0.05 <= args.fraud_batch_share <= 0.50:
        raise SystemExit("--fraud-batch-share must be between 0.05 and 0.50")

    train_paths, y_train = discover(args.data_root, "train")
    test_paths, y_test = discover(args.data_root, "test")
    if not train_paths or not test_paths:
        raise SystemExit("Expected train/{Fraud,Non-Fraud} and test/{Fraud,Non-Fraud} folders")
    _, train_forensics = extract_many(train_paths, args.cache_dir / "train_features.joblib")
    hashes = [row["perceptual_hash"] for row in train_forensics]
    groups = build_perceptual_groups(hashes, args.perceptual_distance)
    fit_indices, validation_indices = grouped_holdout_indices(
        y_train, groups, folds=args.validation_folds, random_state=42
    )

    def decode(path, label):
        image = tf.io.decode_jpeg(tf.io.read_file(path), channels=3)
        image = tf.image.resize_with_pad(image, args.image_size, args.image_size)
        return tf.cast(image, tf.float32), tf.cast(label, tf.float32)

    def repeated_class_dataset(paths: list[str], label: float):
        dataset = tf.data.Dataset.from_tensor_slices(paths)
        dataset = dataset.shuffle(len(paths), seed=42, reshuffle_each_iteration=True).repeat()
        return dataset.map(lambda path: decode(path, label), num_parallel_calls=tf.data.AUTOTUNE)

    fit_fraud = [str(train_paths[i]) for i in fit_indices if y_train[i] == 1]
    fit_nonfraud = [str(train_paths[i]) for i in fit_indices if y_train[i] == 0]
    fraud_stream = repeated_class_dataset(fit_fraud, 1.0)
    nonfraud_stream = repeated_class_dataset(fit_nonfraud, 0.0)
    train = tf.data.Dataset.sample_from_datasets(
        [nonfraud_stream, fraud_stream],
        weights=[1.0 - args.fraud_batch_share, args.fraud_batch_share],
        seed=42,
    ).batch(args.batch_size).prefetch(tf.data.AUTOTUNE)

    def evaluation_dataset(paths: list[Path], labels: np.ndarray):
        dataset = tf.data.Dataset.from_tensor_slices(([str(path) for path in paths], labels.astype(np.float32)))
        return dataset.map(decode, num_parallel_calls=tf.data.AUTOTUNE).batch(args.batch_size).prefetch(tf.data.AUTOTUNE)

    validation_paths = [train_paths[i] for i in validation_indices]
    validation_labels = y_train[validation_indices]
    validation = evaluation_dataset(validation_paths, validation_labels)
    test = evaluation_dataset(test_paths, y_test)
    steps_per_epoch = math.ceil(len(fit_indices) / args.batch_size)

    augmentation = tf.keras.Sequential([
        tf.keras.layers.RandomFlip("horizontal"),
        tf.keras.layers.RandomRotation(0.06),
        tf.keras.layers.RandomZoom(0.10),
        tf.keras.layers.RandomContrast(0.18),
        tf.keras.layers.RandomBrightness(0.15),
    ], name="evidence_augmentation")
    backbone = tf.keras.applications.EfficientNetV2B0(
        include_top=False,
        weights="imagenet",
        input_shape=(args.image_size, args.image_size, 3),
        pooling="avg",
    )
    backbone.trainable = False
    inputs = tf.keras.Input((args.image_size, args.image_size, 3), name="claim_image")
    x = augmentation(inputs)
    x = tf.keras.applications.efficientnet_v2.preprocess_input(x)
    x = backbone(x, training=False)
    x = tf.keras.layers.Dropout(0.35)(x)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid", name="fraud_probability")(x)
    model = tf.keras.Model(inputs, outputs, name="vericlaim_efficientnet_v2")

    model.compile(
        optimizer=tf.keras.optimizers.AdamW(learning_rate=2e-3, weight_decay=1e-4),
        loss=tf.keras.losses.BinaryFocalCrossentropy(gamma=2.0, apply_class_balancing=False),
        metrics=[
            tf.keras.metrics.AUC(curve="PR", name="pr_auc"),
            tf.keras.metrics.AUC(curve="ROC", name="roc_auc"),
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ],
    )
    callbacks = [
        tf.keras.callbacks.EarlyStopping(monitor="val_pr_auc", mode="max", patience=4, restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_pr_auc", mode="max", patience=2, factor=0.25, min_lr=1e-6),
        tf.keras.callbacks.ModelCheckpoint(args.output_dir / "best.keras", monitor="val_pr_auc", mode="max", save_best_only=True),
    ]
    history_head = model.fit(
        train,
        validation_data=validation,
        epochs=args.epochs,
        steps_per_epoch=steps_per_epoch,
        callbacks=callbacks,
    )

    backbone.trainable = True
    for layer in backbone.layers[:-35]:
        layer.trainable = False
    model.compile(
        optimizer=tf.keras.optimizers.AdamW(learning_rate=2e-5, weight_decay=1e-5),
        loss=tf.keras.losses.BinaryFocalCrossentropy(gamma=2.0),
        metrics=[
            tf.keras.metrics.AUC(curve="PR", name="pr_auc"),
            tf.keras.metrics.AUC(curve="ROC", name="roc_auc"),
            tf.keras.metrics.Precision(name="precision"),
            tf.keras.metrics.Recall(name="recall"),
        ],
    )
    history_fine = model.fit(
        train,
        validation_data=validation,
        epochs=max(5, args.epochs // 2),
        steps_per_epoch=steps_per_epoch,
        callbacks=callbacks,
    )
    validation_probabilities = model.predict(validation, verbose=0).reshape(-1)
    review_threshold, investigate_threshold = choose_threshold(
        validation_labels, validation_probabilities, recall_target=args.recall_target
    )
    test_probabilities = model.predict(test, verbose=0).reshape(-1)
    model.save(args.output_dir / "vericlaim_efficientnet_v2.keras")
    report = {
        "architecture": "EfficientNetV2B0 transfer learning",
        "class_mapping": {"Non-Fraud": 0, "Fraud": 1},
        "training_strategy": {
            "kept_all_training_images": True,
            "fraud_batch_share": args.fraud_batch_share,
            "loss": "Binary focal cross-entropy",
            "perceptual_group_distance": args.perceptual_distance,
            "validation_folds": args.validation_folds,
            "fit_images": len(fit_indices),
            "validation_images": len(validation_indices),
        },
        "thresholds": {
            "review": float(review_threshold),
            "investigate": float(investigate_threshold),
            "recall_target": args.recall_target,
        },
        "validation_metrics": metrics(validation_labels, validation_probabilities, review_threshold),
        "test_metrics": metrics(y_test, test_probabilities, review_threshold),
        "head_history": {k: [float(v) for v in values] for k, values in history_head.history.items()},
        "fine_tune_history": {k: [float(v) for v in values] for k, values in history_fine.history.items()},
        "warning": "The supplied test split has perceptual overlap with training; use leakage-aware validation for model selection.",
    }
    (args.output_dir / "metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps({"validation_metrics": report["validation_metrics"], "test_metrics": report["test_metrics"]}, indent=2))


if __name__ == "__main__":
    main()
