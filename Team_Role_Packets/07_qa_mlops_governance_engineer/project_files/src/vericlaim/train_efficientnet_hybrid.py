"""Train the production-candidate EfficientNetV2B0 hybrid.

The CNN is used as a frozen ImageNet-pretrained visual backbone. Grouped-fold
sigmoid heads produce leakage-aware out-of-fold probabilities. Those signals
are fused with the existing ExtraTrees, MLP and label-aware archive signals,
then calibrated with Platt scaling. No external claim images are introduced.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedGroupKFold

from .features import FEATURE_VERSION, feature_names
from .train import (
    archive_similarity_features,
    average_probability,
    choose_classification_threshold,
    choose_threshold,
    discover,
    exact_duplicate_audit,
    extract_many,
    fit_balanced_subset_models,
    fit_neural_model,
    metrics,
)
from .validation import build_perceptual_groups, perceptual_overlap_audit


CNN_VERSION = "efficientnetv2b0-imagenet-frozen-v1"


def extract_embeddings(paths: list[Path], cache_path: Path, backbone, image_size: int) -> np.ndarray:
    expected_paths = [str(path) for path in paths]
    if cache_path.exists():
        cached = joblib.load(cache_path)
        if cached.get("version") == CNN_VERSION and cached.get("paths") == expected_paths and cached.get("image_size") == image_size:
            return cached["embeddings"]

    import tensorflow as tf

    def decode(path):
        image = tf.io.decode_image(tf.io.read_file(path), channels=3, expand_animations=False)
        image.set_shape([None, None, 3])
        image = tf.image.resize_with_pad(image, image_size, image_size)
        return tf.cast(image, tf.float32)

    dataset = tf.data.Dataset.from_tensor_slices(expected_paths)
    dataset = dataset.map(decode, num_parallel_calls=tf.data.AUTOTUNE).batch(32).prefetch(tf.data.AUTOTUNE)
    embeddings = backbone.predict(dataset, verbose=1).astype(np.float32)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"version": CNN_VERSION, "paths": expected_paths, "image_size": image_size, "embeddings": embeddings}, cache_path, compress=3)
    return embeddings


def stack_features(full, balanced, neural, cnn, archive):
    return np.column_stack([full, balanced, neural, cnn, archive, archive[:, 0] - archive[:, 1]])


def fit_cnn_head(embeddings: np.ndarray, labels: np.ndarray, random_state: int):
    # A sigmoid Dense(1) head is mathematically logistic regression. Class
    # weighting prevents the 3.85% minority class from being ignored.
    model = LogisticRegression(C=0.35, class_weight="balanced", max_iter=2500, random_state=random_state)
    model.fit(embeddings, labels)
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("models/efficientnet_hybrid"))
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache"))
    parser.add_argument("--image-size", type=int, default=224)
    parser.add_argument("--validation-folds", type=int, default=5)
    parser.add_argument("--perceptual-distance", type=int, default=6)
    parser.add_argument("--recall-target", type=float, default=0.99)
    parser.add_argument("--full-trees", type=int, default=300)
    parser.add_argument("--balanced-trees", type=int, default=100)
    parser.add_argument("--nonfraud-ratio", type=float, default=8.0)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    start = time.time()

    import tensorflow as tf

    train_paths, y_train = discover(args.data_root, "train")
    test_paths, y_test = discover(args.data_root, "test")
    if not train_paths or not test_paths:
        raise SystemExit("Expected train/{Fraud,Non-Fraud} and test/{Fraud,Non-Fraud} folders")

    x_train, train_forensics = extract_many(train_paths, args.cache_dir / "train_features.joblib")
    x_test, test_forensics = extract_many(test_paths, args.cache_dir / "test_features.joblib")
    train_hashes = [row["perceptual_hash"] for row in train_forensics]
    test_hashes = [row["perceptual_hash"] for row in test_forensics]
    groups = build_perceptual_groups(train_hashes, args.perceptual_distance)

    backbone = tf.keras.applications.EfficientNetV2B0(
        include_top=False,
        weights="imagenet",
        input_shape=(args.image_size, args.image_size, 3),
        pooling="avg",
        include_preprocessing=True,
    )
    backbone.trainable = False
    backbone_path = args.output_dir / "efficientnetv2b0_backbone.keras"
    backbone.save(backbone_path)
    cnn_train = extract_embeddings(train_paths, args.cache_dir / f"cnn_train_{args.image_size}.joblib", backbone, args.image_size)
    cnn_test = extract_embeddings(test_paths, args.cache_dir / f"cnn_test_{args.image_size}.joblib", backbone, args.image_size)

    splitter = StratifiedGroupKFold(n_splits=args.validation_folds, shuffle=True, random_state=42)
    oof_full = np.zeros(len(y_train), dtype=np.float64)
    oof_balanced = np.zeros(len(y_train), dtype=np.float64)
    oof_neural = np.zeros(len(y_train), dtype=np.float64)
    oof_cnn = np.zeros(len(y_train), dtype=np.float64)
    oof_archive = np.zeros((len(y_train), 2), dtype=np.float32)
    test_full = np.zeros(len(y_test), dtype=np.float64)
    test_balanced = np.zeros(len(y_test), dtype=np.float64)
    test_neural = np.zeros(len(y_test), dtype=np.float64)
    test_cnn = np.zeros(len(y_test), dtype=np.float64)
    full_models: list = []
    balanced_models: list = []
    neural_models: list = []
    cnn_models: list = []

    splits = list(splitter.split(x_train, y_train, groups))
    for fold, (fit_indices, validation_indices) in enumerate(splits):
        forest = ExtraTreesClassifier(
            n_estimators=args.full_trees, min_samples_leaf=2, max_features=0.20,
            class_weight="balanced_subsample", n_jobs=-1, random_state=42 + fold,
        )
        forest.fit(x_train[fit_indices], y_train[fit_indices])
        full_models.append(forest)
        oof_full[validation_indices] = forest.predict_proba(x_train[validation_indices])[:, 1]
        test_full += forest.predict_proba(x_test)[:, 1] / args.validation_folds

        fold_balanced = fit_balanced_subset_models(
            x_train[fit_indices], y_train[fit_indices], args.balanced_trees,
            args.nonfraud_ratio, 200 + fold,
        )
        balanced_models.extend(fold_balanced)
        oof_balanced[validation_indices] = average_probability(fold_balanced, x_train[validation_indices])
        test_balanced += average_probability(fold_balanced, x_test) / args.validation_folds

        neural = fit_neural_model(x_train[fit_indices], y_train[fit_indices], 800 + fold)
        neural_models.append(neural)
        oof_neural[validation_indices] = neural.predict_proba(x_train[validation_indices])[:, 1]
        test_neural += neural.predict_proba(x_test)[:, 1] / args.validation_folds

        cnn_head = fit_cnn_head(cnn_train[fit_indices], y_train[fit_indices], 1000 + fold)
        cnn_models.append(cnn_head)
        oof_cnn[validation_indices] = cnn_head.predict_proba(cnn_train[validation_indices])[:, 1]
        test_cnn += cnn_head.predict_proba(cnn_test)[:, 1] / args.validation_folds

        oof_archive[validation_indices] = archive_similarity_features(
            [train_hashes[index] for index in validation_indices],
            [train_hashes[index] for index in fit_indices], y_train[fit_indices],
        )

    test_archive = archive_similarity_features(test_hashes, train_hashes, y_train)
    oof_stack = stack_features(oof_full, oof_balanced, oof_neural, oof_cnn, oof_archive)
    test_stack = stack_features(test_full, test_balanced, test_neural, test_cnn, test_archive)

    oof_raw = np.zeros(len(y_train), dtype=np.float64)
    for fold, (fit_indices, validation_indices) in enumerate(splits):
        meta = LogisticRegression(C=10.0, class_weight="balanced", max_iter=2000, random_state=1400 + fold)
        meta.fit(oof_stack[fit_indices], y_train[fit_indices])
        oof_raw[validation_indices] = meta.predict_proba(oof_stack[validation_indices])[:, 1]

    stacker = LogisticRegression(C=10.0, class_weight="balanced", max_iter=2000, random_state=42)
    stacker.fit(oof_stack, y_train)
    test_raw = stacker.predict_proba(test_stack)[:, 1]

    # Platt calibration restores probabilities toward the observed prevalence.
    calibrator = LogisticRegression(C=1_000.0, max_iter=2000, random_state=1700)
    calibrator.fit(oof_raw.reshape(-1, 1), y_train)
    oof_probability = calibrator.predict_proba(oof_raw.reshape(-1, 1))[:, 1]
    test_probability = calibrator.predict_proba(test_raw.reshape(-1, 1))[:, 1]

    review, investigate = choose_threshold(y_train, oof_probability, args.recall_target)
    classification = choose_classification_threshold(y_train, oof_probability)
    cnn_threshold = choose_classification_threshold(y_train, oof_cnn)
    report = {
        "project": "VeriClaim AI",
        "feature_version": FEATURE_VERSION,
        "model": "Calibrated EfficientNetV2B0 CNN + ExtraTrees/MLP + label-aware archive hybrid",
        "dataset": {
            "train_images": len(train_paths), "train_fraud": int(y_train.sum()),
            "test_images": len(test_paths), "test_fraud": int(y_test.sum()),
            "train_fraud_rate": round(float(y_train.mean()), 4), "test_fraud_rate": round(float(y_test.mean()), 4),
        },
        "cnn": {
            "backbone": "EfficientNetV2B0", "weights": "ImageNet transfer learning",
            "image_size": args.image_size, "embedding_dimensions": int(cnn_train.shape[1]),
            "heads": len(cnn_models), "backbone_trainable": False,
            "note": "Pretraining supplies generic visual knowledge; only the supplied claim images train the fraud heads.",
        },
        "fusion": {
            "signals": ["ExtraTrees full-data", "ExtraTrees rotating balanced", "MLP", "EfficientNetV2B0", "fraud archive similarity", "legitimate archive similarity"],
            "meta_model": "class-weighted Logistic Regression", "probability_calibration": "Platt scaling",
        },
        "validation_protocol": {
            "method": "5-fold StratifiedGroupKFold using perceptual-image clusters",
            "perceptual_hash_distance": args.perceptual_distance,
            "train_perceptual_groups": int(len(np.unique(groups))), "recall_target": args.recall_target,
        },
        "imbalance_strategy": {
            "kept_all_training_images": True, "external_claim_data": False,
            "cnn_head_class_weight": "balanced", "mlp_fraud_weighted": True,
            "rotating_balanced_models": len(balanced_models), "nonfraud_per_fraud": args.nonfraud_ratio,
        },
        "cnn_standalone_metrics": metrics(y_test, test_cnn, cnn_threshold),
        "validation_metrics": metrics(y_train, oof_probability, review),
        "test_metrics": metrics(y_test, test_probability, review),
        "classification_metrics": metrics(y_test, test_probability, classification),
        "default_thresholds": {"review": round(review, 4), "classification": round(classification, 4), "investigate": round(investigate, 4)},
        "leakage_audit": {
            **exact_duplicate_audit(train_forensics, test_forensics),
            "perceptual_screen": perceptual_overlap_audit(train_hashes, y_train, test_hashes, y_test, args.perceptual_distance),
        },
        "elapsed_seconds": round(time.time() - start, 1),
    }
    artifact = {
        "feature_version": FEATURE_VERSION, "feature_names": feature_names(),
        "model_family": "calibrated-efficientnetv2b0-hybrid-v1",
        "full_models": full_models, "balanced_models": balanced_models,
        "neural_models": neural_models, "cnn_models": cnn_models,
        "cnn_backbone_path": backbone_path.name, "cnn_image_size": args.image_size,
        "stacker": stacker, "probability_calibrator": calibrator,
        "thresholds": report["default_thresholds"], "reference_hashes": train_hashes,
        "reference_labels": ["Fraud" if label else "Non-Fraud" for label in y_train],
        "metrics": report,
    }
    joblib.dump(artifact, args.output_dir / "vericlaim_model.joblib", compress=3)
    (args.output_dir / "model_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
