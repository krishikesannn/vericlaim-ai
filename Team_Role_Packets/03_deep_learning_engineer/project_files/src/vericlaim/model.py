"""Training and inference utilities for VeriClaim AI."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import joblib
import numpy as np
from PIL import Image, ImageOps

from .features import FEATURE_VERSION, ImageForensics, extract_features, feature_names, hamming_distance


class VeriClaimModel:
    def __init__(self, artifact: dict):
        if artifact.get("feature_version") != FEATURE_VERSION:
            raise ValueError("Model and feature extractor versions do not match")
        self.artifact = artifact
        self.forest = artifact.get("forest")
        self.full_models = artifact.get("full_models", [])
        self.balanced_models = artifact.get("balanced_models", [])
        self.neural_models = artifact.get("neural_models", [])
        self.cnn_models = artifact.get("cnn_models", [])
        self.probability_calibrator = artifact.get("probability_calibrator")
        self.cnn_backbone_path: Path | None = None
        self._cnn_backbone = None
        self.stacker = artifact.get("stacker")
        self.thresholds = artifact["thresholds"]
        self.reference_hashes = artifact.get("reference_hashes", [])
        self.reference_labels = artifact.get("reference_labels", [])

    @classmethod
    def load(cls, path: str | Path) -> "VeriClaimModel":
        model = cls(joblib.load(path))
        backbone_name = model.artifact.get("cnn_backbone_path")
        if backbone_name:
            model.cnn_backbone_path = Path(path).resolve().parent / backbone_name
        return model

    @staticmethod
    def _mean_probability(models: list, matrix: np.ndarray) -> float:
        return float(np.mean([model.predict_proba(matrix)[0, 1] for model in models]))

    def reference_class_similarities(self, perceptual_hash: str) -> dict[str, float]:
        fraud_distances = [
            hamming_distance(perceptual_hash, candidate)
            for candidate, label in zip(self.reference_hashes, self.reference_labels)
            if label == "Fraud"
        ]
        nonfraud_distances = [
            hamming_distance(perceptual_hash, candidate)
            for candidate, label in zip(self.reference_hashes, self.reference_labels)
            if label == "Non-Fraud"
        ]
        fraud_similarity = max(0.0, 1.0 - min(fraud_distances) / 63.0) if fraud_distances else 0.0
        nonfraud_similarity = max(0.0, 1.0 - min(nonfraud_distances) / 63.0) if nonfraud_distances else 0.0
        return {
            "fraud_similarity": float(fraud_similarity),
            "legitimate_similarity": float(nonfraud_similarity),
        }

    def _cnn_probability(self, source) -> float | None:
        if not self.cnn_models or self.cnn_backbone_path is None:
            return None
        if self._cnn_backbone is None:
            import tensorflow as tf
            self._cnn_backbone = tf.keras.models.load_model(self.cnn_backbone_path, compile=False)
        if isinstance(source, (str, Path)):
            image = Image.open(source)
        elif isinstance(source, bytes):
            import io
            image = Image.open(io.BytesIO(source))
        else:
            import io
            raw = source.read()
            source.seek(0)
            image = Image.open(io.BytesIO(raw))
        size = int(self.artifact.get("cnn_image_size", 224))
        contained = ImageOps.contain(image.convert("RGB"), (size, size), Image.Resampling.BILINEAR)
        padded = Image.new("RGB", (size, size))
        padded.paste(contained, ((size - contained.width) // 2, (size - contained.height) // 2))
        pixels = np.asarray(padded, dtype=np.float32)
        embedding = self._cnn_backbone.predict(pixels[None, ...], verbose=0)
        return self._mean_probability(self.cnn_models, embedding)

    def predict_feature(self, feature: np.ndarray, perceptual_hash: str | None = None, cnn_probability: float | None = None) -> float:
        matrix = feature.reshape(1, -1)
        if self.stacker is not None and self.full_models and self.balanced_models and perceptual_hash:
            full = self._mean_probability(self.full_models, matrix)
            balanced = self._mean_probability(self.balanced_models, matrix)
            neural = self._mean_probability(self.neural_models, matrix) if self.neural_models else None
            similarities = self.reference_class_similarities(perceptual_hash)
            fraud_similarity = similarities["fraud_similarity"]
            legitimate_similarity = similarities["legitimate_similarity"]
            stacked_values = [full, balanced]
            if neural is not None:
                stacked_values.append(neural)
            if self.cnn_models and cnn_probability is not None:
                stacked_values.append(cnn_probability)
            stacked_values.extend([
                fraud_similarity,
                legitimate_similarity,
                fraud_similarity - legitimate_similarity,
            ])
            stacked = np.asarray([stacked_values], dtype=np.float32)
            probability = float(self.stacker.predict_proba(stacked)[0, 1])
            if self.probability_calibrator is not None:
                probability = float(self.probability_calibrator.predict_proba([[probability]])[0, 1])
            return float(np.clip(probability, 0, 1))
        return float(np.clip(self.forest.predict_proba(matrix)[0, 1], 0, 1))

    def nearest_reference(self, perceptual_hash: str) -> dict[str, object]:
        if not self.reference_hashes:
            return {"distance": None, "similarity": 0.0, "label": None}
        distances = np.asarray([hamming_distance(perceptual_hash, candidate) for candidate in self.reference_hashes])
        index = int(np.argmin(distances))
        distance = int(distances[index])
        class_similarities = self.reference_class_similarities(perceptual_hash)
        return {
            "distance": distance,
            "similarity": round(max(0.0, 1.0 - distance / 63.0), 3),
            "label": self.reference_labels[index],
            "fraud_similarity": round(class_similarities["fraud_similarity"], 3),
            "legitimate_similarity": round(class_similarities["legitimate_similarity"], 3),
        }

    def analyze_image(self, source) -> dict[str, object]:
        feature, forensic = extract_features(source)
        cnn_probability = self._cnn_probability(source)
        probability = self.predict_feature(feature, forensic.perceptual_hash, cnn_probability)
        nearest = self.nearest_reference(forensic.perceptual_hash)
        review_threshold = float(self.thresholds["review"])
        return {
            "visual_fraud_probability": round(probability, 4),
            "cnn_fraud_probability": round(cnn_probability, 4) if cnn_probability is not None else None,
            "image_classification": "Fraud pattern detected" if probability >= review_threshold else "Below fraud-review threshold",
            "review_threshold_met": bool(probability >= review_threshold),
            "forensics": asdict(forensic),
            "nearest_reference": nearest,
            "feature_summary": {
                "visual_complexity": round(float(feature[2]) * 100, 1),
                "edge_density": round(float(feature[5]) * 100, 1),
                "focus_signal": round(float(np.clip(feature[7] / 0.45, 0, 1)) * 100, 1),
            },
        }

    def score_claim(self, image_results: list[dict], claim_amount: float | None = None) -> dict[str, object]:
        if not image_results:
            raise ValueError("At least one image is required")
        image_probabilities = [float(r["visual_fraud_probability"]) for r in image_results]
        # Claim triage is a screening task: one suspicious view must not be
        # cancelled out by several ordinary views of the same vehicle.
        visual_probability = float(max(image_probabilities))
        mean_visual_probability = float(np.mean(image_probabilities))
        tamper = float(max(r["forensics"]["tamper_signal"] for r in image_results))
        fraud_duplicate = float(max(
            r["nearest_reference"].get(
                "fraud_similarity",
                r["nearest_reference"].get("similarity", 0.0)
                if r["nearest_reference"].get("label") == "Fraud" else 0.0,
            )
            for r in image_results
        ))
        legitimate_duplicate = float(max(
            r["nearest_reference"].get(
                "legitimate_similarity",
                r["nearest_reference"].get("similarity", 0.0)
                if r["nearest_reference"].get("label") == "Non-Fraud" else 0.0,
            )
            for r in image_results
        ))
        quality = float(np.mean([r["forensics"]["quality_score"] for r in image_results]))

        within_claim_similarity = 0.0
        if len(image_results) > 1:
            hashes = [r["forensics"]["perceptual_hash"] for r in image_results]
            similarities = [1 - hamming_distance(hashes[i], hashes[j]) / 63 for i in range(len(hashes)) for j in range(i + 1, len(hashes))]
            within_claim_similarity = float(max(similarities)) if similarities else 0.0

        amount_mismatch = 0.0
        if claim_amount is not None and claim_amount > 0:
            normalized_amount = np.clip(np.log1p(claim_amount) / np.log1p(2_000_000), 0, 1)
            damage_proxy = np.clip(np.mean([r["feature_summary"]["edge_density"] for r in image_results]) / 35.0, 0, 1)
            amount_mismatch = float(max(0, normalized_amount - damage_proxy))

        model_review = float(self.thresholds["review"])
        model_investigate = float(self.thresholds["investigate"])
        if visual_probability <= model_review:
            visual_risk_index = 0.40 * visual_probability / max(model_review, 1e-6)
        elif visual_probability <= model_investigate:
            visual_risk_index = 0.40 + 0.35 * (visual_probability - model_review) / max(model_investigate - model_review, 1e-6)
        else:
            visual_risk_index = 0.75 + 0.25 * (visual_probability - model_investigate) / max(1 - model_investigate, 1e-6)
        visual_risk_index = float(np.clip(visual_risk_index, 0, 1))

        # Only a match to a labeled fraud reference can raise archive risk.
        # Evidence quality and claim-amount consistency remain visible review
        # signals; they are not treated as proof of fraud in the fused score.
        risk = float(np.clip(0.74 * visual_risk_index + 0.08 * tamper + 0.18 * fraud_duplicate, 0, 1))
        review_threshold = 0.40
        investigate_threshold = 0.67
        if visual_probability >= model_investigate:
            risk = max(risk, 0.70)
        elif visual_probability >= model_review:
            risk = max(risk, 0.45)
        if risk >= investigate_threshold:
            decision = "Priority investigation"
            tier = "high"
        elif risk >= review_threshold:
            decision = "Manual review"
            tier = "medium"
        else:
            decision = "No strong image-only fraud signal"
            tier = "low"

        factors = []
        if visual_probability >= model_review:
            factors.append("Visual pattern resembles labeled fraudulent submissions")
        if tamper >= 0.4:
            factors.append("Editing or image-integrity signal requires verification")
        if fraud_duplicate >= 0.92:
            factors.append("Near-duplicate image resembles a labeled fraud reference")
        if legitimate_duplicate >= 0.92:
            factors.append("Near-duplicate image resembles a legitimate reference; verify claim linkage")
        if within_claim_similarity >= 0.94:
            factors.append("Multiple uploads may show substantially the same view")
        if amount_mismatch >= 0.35:
            factors.append("Claim amount appears high relative to visible damage proxy")
        if quality < 35:
            factors.append("Low image quality reduces model confidence")
        if not factors:
            factors.append("No dominant image-only fraud signal detected; this is not proof of a legitimate claim")

        decision_margin = float(np.clip(abs(risk - review_threshold) / max(review_threshold, 1 - review_threshold) * 100, 0, 100))
        return {
            "risk_score": round(risk * 100, 1),
            "risk_tier": tier,
            "decision": decision,
            "decision_margin": round(decision_margin, 1),
            "signals": {
                "visual_model": round(visual_probability * 100, 1),
                "mean_visual_model": round(mean_visual_probability * 100, 1),
                "visual_risk_index": round(visual_risk_index * 100, 1),
                "image_integrity": round(tamper * 100, 1),
                "fraud_archive_similarity": round(fraud_duplicate * 100, 1),
                "legitimate_archive_similarity": round(legitimate_duplicate * 100, 1),
                "amount_mismatch": round(amount_mismatch * 100, 1),
                "evidence_quality": round(quality, 1),
                "within_claim_similarity": round(within_claim_similarity * 100, 1),
            },
            "factors": factors,
            "policy": {
                "review_threshold": round(review_threshold * 100, 1),
                "investigate_threshold": round(investigate_threshold * 100, 1),
                "model_review_threshold": round(model_review * 100, 1),
                "human_in_the_loop": True,
                "statement": "Decision-support only; an investigator owns the final claim disposition.",
            },
        }


def load_metrics(path: str | Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))
