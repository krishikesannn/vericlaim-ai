from __future__ import annotations

import io
import unittest

import numpy as np
from PIL import Image

from vericlaim.features import extract_features, feature_names, hamming_distance


def synthetic_image() -> bytes:
    canvas = np.zeros((96, 128, 3), dtype=np.uint8)
    canvas[:, :, 0] = np.linspace(20, 220, 128, dtype=np.uint8)
    canvas[30:65, 40:90] = [210, 210, 215]
    output = io.BytesIO()
    Image.fromarray(canvas).save(output, format="JPEG", quality=90)
    return output.getvalue()


class FeatureTests(unittest.TestCase):
    def test_feature_shape_is_stable(self):
        vector, forensic = extract_features(synthetic_image())
        self.assertEqual(len(vector), len(feature_names()))
        self.assertTrue(np.isfinite(vector).all())
        self.assertEqual(forensic.width, 128)
        self.assertEqual(forensic.height, 96)
        self.assertEqual(len(forensic.sha256), 64)

    def test_perceptual_hash_distance(self):
        _, forensic = extract_features(synthetic_image())
        self.assertEqual(hamming_distance(forensic.perceptual_hash, forensic.perceptual_hash), 0)


if __name__ == "__main__":
    unittest.main()

