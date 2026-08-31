# Model card — VeriClaim Vision v1

## Intended use

Prioritize vehicle-damage image submissions for human fraud review. The score supports triage; it must not be used as the sole basis for denial, cancellation, pricing, law-enforcement referral or an allegation of fraud.

## Training data

- Source: https://www.kaggle.com/datasets/pacificrm/car-insurance-fraud-detection
- Train: 5,200 images (200 labeled fraud)
- Test: 1,416 images (93 labeled fraud)
- Label granularity: image-level binary label

## Model

The deployed model is a calibrated EfficientNetV2B0 hybrid. A frozen ImageNet-pretrained EfficientNetV2B0 backbone produces 1,280-dimensional image embeddings. Five grouped fraud-weighted sigmoid heads are fused with five MLPs, five full-data class-weighted ExtraTrees models, 20 rotating balanced ExtraTrees models and label-aware archive similarity. A cross-fitted logistic meta-model performs fusion and Platt scaling calibrates the final probability.
covering color, texture, composition, frequency structure and oriented
gradients. Five full-data class-weighted learners are combined with 20
fraud-focused learners. Every fraud image is used in every balanced learner;
all non-fraud images rotate across learners. All 5,200 training images are
retained, and no synthetic claim rows or additional insurance dataset are used. Standard ImageNet transfer weights initialize the CNN. Label-aware
archive similarity is included in the stack. Validation uses perceptual-image
clusters so closely related images cannot cross folds.

## Evaluation

At the balanced binary threshold, the supplied test split achieved 96.12%
accuracy, 94.42% balanced accuracy, 92.47% fraud recall, 64.18% precision and
0.9048 PR-AUC (86 TP, 7 FN, 48 FP, 1,275 TN). At the high-sensitivity screening
threshold it achieved 97.85% recall (91 TP, 2 FN). This operating point deliberately
accepts substantially more manual reviews to reduce missed fraud. The supplied test result
must still be interpreted with caution because perceptual screening found
close training fingerprints for 761 of 1,416 test images, although exact byte
overlap is zero. See `models/model_metrics.json` for the reproducible report.

## Limitations

- An image can depict real damage while the associated claim is still fraudulent, or depict unusual damage in a legitimate claim.
- Labels do not explain the fraud mechanism or adjudication evidence.
- The dataset does not include policy history, repair estimates, claimant links or temporal context.
- Handcrafted CPU features are a deployable baseline, not the performance ceiling.
- EXIF absence is common and must not be treated as evidence of fraud.
- Similarity retrieval can identify reused imagery but not the intent behind reuse.
- Subgroup fairness cannot be evaluated without appropriate, lawful audit data.

## Production validation

1. Use a time-separated, insurer-owned holdout with claim-level grouping.
2. Calibrate probabilities and thresholds to investigator capacity and error costs.
3. Run in shadow mode and measure override reasons.
4. Audit performance across vehicle types, lighting, device types, regions and repair severity.
5. Monitor drift, evidence-quality mix, false positives, false negatives and calibration.
6. Maintain rollback, model registry and threshold approval controls.
