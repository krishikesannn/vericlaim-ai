from __future__ import annotations

import unittest

import numpy as np

from vericlaim.validation import build_perceptual_groups, grouped_holdout_indices, perceptual_overlap_audit


class ValidationTests(unittest.TestCase):
    def test_close_hashes_share_a_group(self):
        hashes = ["0000000000000000", "0000000000000001", "ffffffffffffffff"]
        groups = build_perceptual_groups(hashes, max_distance=1)
        self.assertEqual(groups[0], groups[1])
        self.assertNotEqual(groups[0], groups[2])

    def test_grouped_holdout_has_no_overlap(self):
        labels = np.asarray([0, 0, 0, 0, 1, 1, 1, 1, 0, 1])
        groups = np.arange(len(labels))
        fit, validation = grouped_holdout_indices(labels, groups, folds=2)
        self.assertFalse(set(groups[fit]) & set(groups[validation]))

    def test_perceptual_audit_counts_matches(self):
        report = perceptual_overlap_audit(
            ["0000000000000000", "ffffffffffffffff"],
            np.asarray([0, 1]),
            ["0000000000000001", "0f0f0f0f0f0f0f0f"],
            np.asarray([0, 0]),
            max_distance=1,
        )
        self.assertEqual(report["test_images_with_close_train_match"], 1)
        self.assertEqual(report["cross_label_close_matches"], 0)


if __name__ == "__main__":
    unittest.main()
