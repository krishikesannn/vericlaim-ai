# Model artifacts

The repository keeps only the artifacts needed by the running demo:

- `efficientnet_hybrid/` - deployed EfficientNetV2B0 + Extra Trees + MLP +
  archive-similarity ensemble, calibration data and metrics;
- `neural_candidate/` - previous comparison model used by Model Lab.

Large fold checkpoints and superseded experiments are deliberately ignored.
Their metric JSON files remain useful for audit and model comparison, while
the checkpoints can be reproduced from the training commands documented in
the root README.

Do not replace the deployed model merely because a candidate reports higher
accuracy. Promotion requires grouped validation improvements in fraud recall,
PR-AUC, calibration and false-positive workload.

