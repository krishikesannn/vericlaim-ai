"""Train and evaluate VeriClaim AI on Kaggle's predefined split."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import time
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import ExtraTreesClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    fbeta_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import StratifiedGroupKFold
from .features import FEATURE_VERSION, extract_features, feature_names
from .validation import build_perceptual_groups, perceptual_overlap_audit


def discover(root: Path, split: str) -> tuple[list[Path], np.ndarray]:
    images: list[Path] = []
    labels: list[int] = []
    for label_name, label in (("Non-Fraud", 0), ("Fraud", 1)):
        folder = root / split / label_name
        for path in sorted(folder.glob("*")):
            if path.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}:
                images.append(path)
                labels.append(label)
    return images, np.asarray(labels, dtype=np.int8)


def extract_many(paths: list[Path], cache_path: Path) -> tuple[np.ndarray, list[dict]]:
    if cache_path.exists():
        cached = joblib.load(cache_path)
        if cached.get("feature_version") == FEATURE_VERSION and cached.get("paths") == [str(p) for p in paths]:
            return cached["features"], cached["forensics"]
    rows: list[np.ndarray] = []
    forensics: list[dict] = []
    for index, path in enumerate(paths, start=1):
        feature, forensic = extract_features(path)
        rows.append(feature)
        forensics.append(forensic.__dict__)
        if index % 250 == 0:
            print(f"Extracted {index}/{len(paths)} images", flush=True)
    matrix = np.vstack(rows)
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"feature_version": FEATURE_VERSION, "paths": [str(p) for p in paths], "features": matrix, "forensics": forensics}, cache_path, compress=3)
    return matrix, forensics


def choose_threshold(y_true: np.ndarray, probabilities: np.ndarray, recall_target: float = 0.75) -> tuple[float, float]:
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    f2 = 5 * precision * recall / np.maximum(4 * precision + recall, 1e-9)
    recall_floor = [(float(t), float(p)) for t, p, r in zip(thresholds, precision[:-1], recall[:-1]) if r >= recall_target]
    if recall_floor:
        review = max(recall_floor, key=lambda item: (item[1], item[0]))[0]
    else:
        review = float(thresholds[int(np.nanargmax(f2[:-1]))])
    precision_floor = [float(t) for t, p in zip(thresholds, precision[:-1]) if p >= 0.75 and t > review]
    investigate = min(precision_floor) if precision_floor else min(0.9, review + 0.15)
    return review, investigate


def choose_classification_threshold(y_true: np.ndarray, probabilities: np.ndarray) -> float:
    """Choose a precise binary cutoff while retaining useful fraud recall."""
    precision, recall, thresholds = precision_recall_curve(y_true, probabilities)
    candidates = [
        (float(threshold), float(score))
        for threshold, score, sensitivity in zip(thresholds, precision[:-1], recall[:-1])
        if sensitivity >= 0.75
    ]
    if not candidates:
        return 0.5
    return max(candidates, key=lambda item: (item[1], item[0]))[0]


def metrics(y_true: np.ndarray, probabilities: np.ndarray, threshold: float) -> dict:
    predicted = (probabilities >= threshold).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, predicted, labels=[0, 1]).ravel()
    return {
        "threshold": round(float(threshold), 4),
        "accuracy": round(float(accuracy_score(y_true, predicted)), 4),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_true, predicted)), 4),
        "precision": round(float(precision_score(y_true, predicted, zero_division=0)), 4),
        "recall": round(float(recall_score(y_true, predicted, zero_division=0)), 4),
        "f1": round(float(f1_score(y_true, predicted, zero_division=0)), 4),
        "f2": round(float(fbeta_score(y_true, predicted, beta=2, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_true, probabilities)), 4),
        "pr_auc": round(float(average_precision_score(y_true, probabilities)), 4),
        "brier": round(float(brier_score_loss(y_true, probabilities)), 4),
        "confusion_matrix": {"tn": int(tn), "fp": int(fp), "fn": int(fn), "tp": int(tp)},
    }


def exact_duplicate_audit(train_forensics: list[dict], test_forensics: list[dict]) -> dict:
    train_hashes = {row["sha256"] for row in train_forensics}
    test_hashes = [row["sha256"] for row in test_forensics]
    overlap = sum(item in train_hashes for item in test_hashes)
    return {"exact_train_test_duplicates": int(overlap), "test_images": len(test_hashes), "overlap_rate": round(overlap / max(1, len(test_hashes)), 5)}


def average_probability(models: list[ExtraTreesClassifier], features: np.ndarray) -> np.ndarray:
    probabilities = np.zeros(len(features), dtype=np.float64)
    for model in models:
        probabilities += model.predict_proba(features)[:, 1] / len(models)
    return probabilities


def fit_balanced_subset_models(
    features: np.ndarray,
    labels: np.ndarray,
    trees: int,
    nonfraud_ratio: float,
    random_state: int,
) -> list[ExtraTreesClassifier]:
    """Rotate all majority examples through fraud-focused learners."""

    fraud = np.where(labels == 1)[0]
    nonfraud = np.where(labels == 0)[0]
    rng = np.random.default_rng(random_state)
    nonfraud = rng.permutation(nonfraud)
    subset_size = max(1, int(np.ceil(len(fraud) * nonfraud_ratio)))
    model_count = int(np.ceil(len(nonfraud) / subset_size))
    models: list[ExtraTreesClassifier] = []
    for model_index in range(model_count):
        start = model_index * subset_size
        selected = nonfraud[start:min(start + subset_size, len(nonfraud))]
        if len(selected) < subset_size:
            selected = np.concatenate([selected, nonfraud[:subset_size - len(selected)]])
        indices = np.concatenate([fraud, selected])
        rng.shuffle(indices)
        model = ExtraTreesClassifier(
            n_estimators=trees,
            min_samples_leaf=2,
            max_features=0.30,
            n_jobs=-1,
            random_state=random_state * 100 + model_index,
        )
        model.fit(features[indices], labels[indices])
        models.append(model)
    return models


def archive_similarity_features(
    query_hashes: list[str],
    reference_hashes: list[str],
    reference_labels: np.ndarray,
) -> np.ndarray:
    fraud = [int(value, 16) for value, label in zip(reference_hashes, reference_labels) if label == 1]
    nonfraud = [int(value, 16) for value, label in zip(reference_hashes, reference_labels) if label == 0]
    rows: list[tuple[float, float]] = []
    for value in query_hashes:
        query = int(value, 16)
        fraud_distance = min((query ^ candidate).bit_count() for candidate in fraud)
        nonfraud_distance = min((query ^ candidate).bit_count() for candidate in nonfraud)
        rows.append((1.0 - fraud_distance / 63.0, 1.0 - nonfraud_distance / 63.0))
    return np.asarray(rows, dtype=np.float32)


def stack_features(full: np.ndarray, balanced: np.ndarray, neural: np.ndarray, archive: np.ndarray) -> np.ndarray:
    """Build meta-model inputs from independent visual and retrieval signals."""
    return np.column_stack([full, balanced, neural, archive, archive[:, 0] - archive[:, 1]])


def fit_neural_model(features: np.ndarray, labels: np.ndarray, random_state: int):
    """Fit a compact fraud-weighted MLP without discarding any supplied image.

    This is the neural-network component used by the shipped model.  We keep
    the architecture deliberately small because there are only 200 positive
    training examples; a large CNN trained from scratch would overfit badly.
    """
    fraud_count = max(1, int(labels.sum()))
    nonfraud_count = max(1, int((labels == 0).sum()))
    weights = np.where(labels == 1, nonfraud_count / fraud_count, 1.0)
    model = make_pipeline(
        StandardScaler(),
        MLPClassifier(
            hidden_layer_sizes=(128, 32),
            activation="relu",
            solver="adam",
            alpha=0.004,
            batch_size=64,
            learning_rate_init=0.0008,
            max_iter=180,
            early_stopping=True,
            validation_fraction=0.15,
            n_iter_no_change=12,
            random_state=random_state,
        ),
    )
    model.fit(features, labels, mlpclassifier__sample_weight=weights)
    return model


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, default=Path("models"))
    parser.add_argument("--cache-dir", type=Path, default=Path(".cache"))
    parser.add_argument("--validation-folds", type=int, default=5)
    parser.add_argument("--perceptual-distance", type=int, default=6)
    parser.add_argument("--recall-target", type=float, default=0.99)
    parser.add_argument("--full-trees", type=int, default=300)
    parser.add_argument("--balanced-trees", type=int, default=100)
    parser.add_argument("--nonfraud-ratio", type=float, default=8.0)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.cache_dir.mkdir(parents=True, exist_ok=True)

    start = time.time()
    train_paths, y_train = discover(args.data_root, "train")
    test_paths, y_test = discover(args.data_root, "test")
    if not train_paths or not test_paths:
        raise SystemExit("Expected train/{Fraud,Non-Fraud} and test/{Fraud,Non-Fraud} folders")

    x_train, train_forensics = extract_many(train_paths, args.cache_dir / "train_features.joblib")
    x_test, test_forensics = extract_many(test_paths, args.cache_dir / "test_features.joblib")

    train_hashes = [row["perceptual_hash"] for row in train_forensics]
    test_hashes = [row["perceptual_hash"] for row in test_forensics]
    perceptual_groups = build_perceptual_groups(train_hashes, args.perceptual_distance)
    splitter = StratifiedGroupKFold(
        n_splits=args.validation_folds, shuffle=True, random_state=42
    )
    oof_full = np.zeros(len(y_train), dtype=np.float64)
    oof_balanced = np.zeros(len(y_train), dtype=np.float64)
    oof_neural = np.zeros(len(y_train), dtype=np.float64)
    oof_archive = np.zeros((len(y_train), 2), dtype=np.float32)
    test_full = np.zeros(len(y_test), dtype=np.float64)
    test_balanced = np.zeros(len(y_test), dtype=np.float64)
    full_models: list[ExtraTreesClassifier] = []
    balanced_models: list[ExtraTreesClassifier] = []
    neural_models: list = []

    for fold, (fit_indices, validation_indices) in enumerate(
        splitter.split(x_train, y_train, perceptual_groups)
    ):
        forest = ExtraTreesClassifier(
            n_estimators=args.full_trees,
            max_depth=None,
            min_samples_leaf=2,
            max_features=0.20,
            class_weight="balanced_subsample",
            n_jobs=-1,
            random_state=42 + fold,
        )
        forest.fit(x_train[fit_indices], y_train[fit_indices])
        full_models.append(forest)
        oof_full[validation_indices] = forest.predict_proba(x_train[validation_indices])[:, 1]
        test_full += forest.predict_proba(x_test)[:, 1] / args.validation_folds

        fold_balanced = fit_balanced_subset_models(
            x_train[fit_indices],
            y_train[fit_indices],
            trees=args.balanced_trees,
            nonfraud_ratio=args.nonfraud_ratio,
            random_state=200 + fold,
        )
        balanced_models.extend(fold_balanced)
        oof_balanced[validation_indices] = average_probability(
            fold_balanced, x_train[validation_indices]
        )
        test_balanced += average_probability(fold_balanced, x_test) / args.validation_folds
        oof_archive[validation_indices] = archive_similarity_features(
            [train_hashes[index] for index in validation_indices],
            [train_hashes[index] for index in fit_indices],
            y_train[fit_indices],
        )

        neural_model = fit_neural_model(x_train[fit_indices], y_train[fit_indices], 800 + fold)
        neural_models.append(neural_model)
        oof_neural[validation_indices] = neural_model.predict_proba(x_train[validation_indices])[:, 1]

    oof_stack = stack_features(oof_full, oof_balanced, oof_neural, oof_archive)
    test_archive = archive_similarity_features(test_hashes, train_hashes, y_train)
    test_neural = average_probability(neural_models, x_test)
    test_stack = stack_features(test_full, test_balanced, test_neural, test_archive)

    # Cross-fit the meta-model so threshold selection never evaluates a row
    # with a stacker that was trained on that row.
    oof_probabilities = np.zeros(len(y_train), dtype=np.float64)
    for fold, (fit_indices, validation_indices) in enumerate(
        splitter.split(oof_stack, y_train, perceptual_groups)
    ):
        fold_stacker = LogisticRegression(
            C=10.0, class_weight="balanced", max_iter=2000, random_state=600 + fold
        )
        fold_stacker.fit(oof_stack[fit_indices], y_train[fit_indices])
        oof_probabilities[validation_indices] = fold_stacker.predict_proba(
            oof_stack[validation_indices]
        )[:, 1]

    stacker = LogisticRegression(
        C=10.0, class_weight="balanced", max_iter=2000, random_state=42
    )
    stacker.fit(oof_stack, y_train)
    probabilities = stacker.predict_proba(test_stack)[:, 1]
    review, investigate = choose_threshold(
        y_train, oof_probabilities, recall_target=args.recall_target
    )
    classification = choose_classification_threshold(y_train, oof_probabilities)

    report = {
        "project": "VeriClaim AI",
        "feature_version": FEATURE_VERSION,
        "dataset": {
            "source": "https://www.kaggle.com/datasets/pacificrm/car-insurance-fraud-detection",
            "train_images": len(train_paths),
            "train_fraud": int(y_train.sum()),
            "test_images": len(test_paths),
            "test_fraud": int(y_test.sum()),
            "train_fraud_rate": round(float(y_train.mean()), 4),
            "test_fraud_rate": round(float(y_test.mean()), 4),
        },
        "model": "Cross-fitted hybrid neural network + ExtraTrees ensemble with label-aware archive similarity",
        "evaluation_note": "The operating threshold was selected from leakage-aware out-of-fold predictions only. The supplied Kaggle test split remained untouched until final evaluation but contains perceptual overlap with training.",
        "validation_protocol": {
            "method": "StratifiedGroupKFold out-of-fold stacking using perceptual-image clusters",
            "folds": args.validation_folds,
            "perceptual_hash_distance": args.perceptual_distance,
            "out_of_fold_images": len(y_train),
            "out_of_fold_fraud": int(y_train.sum()),
            "recall_target": args.recall_target,
            "train_perceptual_groups": int(len(np.unique(perceptual_groups))),
        },
        "imbalance_strategy": {
            "kept_all_training_images": True,
            "full_model_class_weight": "balanced_subsample",
            "rotating_balanced_models": len(balanced_models),
            "nonfraud_per_fraud_in_each_balanced_learner": args.nonfraud_ratio,
            "sampling": "Every fraud image is used in each balanced learner; all non-fraud images rotate across learners. No permanent undersampling or synthetic rows.",
        },
        "neural_network": {
            "architecture": "MLPClassifier: 794 input features -> Dense(128, ReLU) -> Dense(32, ReLU) -> sigmoid fraud probability",
            "models": len(neural_models),
            "training": "Five grouped-fold neural models; StandardScaler; fraud-weighted loss; early stopping; all supplied images retained.",
        },
        "validation_metrics": metrics(y_train, oof_probabilities, review),
        "test_metrics": metrics(y_test, probabilities, review),
        "classification_metrics": metrics(y_test, probabilities, classification),
        "default_thresholds": {
            "review": round(review, 4),
            "classification": round(classification, 4),
            "investigate": round(investigate, 4),
        },
        "leakage_audit": {
            **exact_duplicate_audit(train_forensics, test_forensics),
            "perceptual_screen": perceptual_overlap_audit(
                train_hashes, y_train, test_hashes, y_test, args.perceptual_distance
            ),
        },
        "elapsed_seconds": round(time.time() - start, 1),
    }

    artifact = {
        "feature_version": FEATURE_VERSION,
        "feature_names": feature_names(),
        "model_family": "hybrid-mlp-neural-extra-trees-v3",
        "full_models": full_models,
        "balanced_models": balanced_models,
        "neural_models": neural_models,
        "stacker": stacker,
        "thresholds": report["default_thresholds"],
        "reference_hashes": train_hashes,
        "reference_labels": ["Fraud" if label else "Non-Fraud" for label in y_train],
        "metrics": report,
    }
    joblib.dump(artifact, args.output_dir / "vericlaim_model.joblib", compress=3)
    (args.output_dir / "model_metrics.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
