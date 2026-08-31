from __future__ import annotations

import unittest
from pathlib import Path

from test_features import synthetic_image
from vericlaim.model import VeriClaimModel


ROOT = Path(__file__).resolve().parents[1]


class ModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = VeriClaimModel.load(ROOT / "models" / "vericlaim_model.joblib")

    def test_rigorous_ensemble_is_loaded(self):
        self.assertEqual(self.model.artifact.get("model_family"), "rigorous-stacked-ensemble-v2")
        self.assertEqual(len(self.model.full_models), 5)
        self.assertGreaterEqual(len(self.model.balanced_models), 20)
        self.assertIsNotNone(self.model.stacker)

    def test_end_to_end_score(self):
        image = self.model.analyze_image(synthetic_image())
        claim = self.model.score_claim([image], claim_amount=120000)
        self.assertGreaterEqual(claim["risk_score"], 0)
        self.assertLessEqual(claim["risk_score"], 100)
        self.assertIn(claim["risk_tier"], {"low", "medium", "high"})
        self.assertIn("decision_margin", claim)
        self.assertIn("fraud_archive_similarity", claim["signals"])
        self.assertTrue(claim["policy"]["human_in_the_loop"])

    def test_binary_image_result_uses_classification_threshold(self):
        image = self.model.analyze_image(synthetic_image())
        threshold = self.model.thresholds.get("classification", self.model.thresholds["review"])
        self.assertEqual(
            image["review_threshold_met"],
            image["visual_fraud_probability"] >= threshold,
        )

    def test_legitimate_archive_match_does_not_raise_fraud_risk(self):
        base = self.model.analyze_image(synthetic_image())
        base["visual_fraud_probability"] = 0.0
        base["forensics"]["tamper_signal"] = 0.0
        base["forensics"]["quality_score"] = 100.0
        base["nearest_reference"] = {"distance": 0, "similarity": 1.0, "label": "Non-Fraud"}
        legitimate = self.model.score_claim([base], claim_amount=None)
        base["nearest_reference"] = {"distance": 0, "similarity": 1.0, "label": "Fraud"}
        fraud = self.model.score_claim([base], claim_amount=None)
        self.assertLess(legitimate["risk_score"], fraud["risk_score"])

    def test_one_suspicious_view_is_not_diluted_by_other_images(self):
        suspicious = self.model.analyze_image(synthetic_image())
        suspicious["visual_fraud_probability"] = self.model.thresholds.get(
            "classification", self.model.thresholds["review"]
        ) + 0.05
        ordinary = self.model.analyze_image(synthetic_image())
        ordinary["visual_fraud_probability"] = 0.0

        claim = self.model.score_claim([suspicious, ordinary, ordinary], claim_amount=None)

        self.assertGreaterEqual(
            claim["signals"]["visual_model"],
            self.model.thresholds.get("classification", self.model.thresholds["review"]) * 100,
        )
        self.assertNotEqual(claim["risk_tier"], "low")


if __name__ == "__main__":
    unittest.main()
