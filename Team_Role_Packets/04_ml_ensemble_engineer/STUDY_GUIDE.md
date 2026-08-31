# ML and Ensemble Engineer

## Mission

Own Extra Trees, MLP, archive similarity, leakage-safe stacking, calibration, thresholding and performance comparison.

## How to use this packet

Read the chapters in order. For each chapter, first explain the idea in your own words, then inspect the copied project files, and finally complete one small practical task. Do not make changes in the copied files; modify the canonical project only after the team agrees.

## Project guardrails

- This system prioritizes a claim for human review; it does not prove fraud or automatically reject a claim.
- Use only the supplied insurance dataset for claim-specific training. ImageNet pretraining is disclosed as generic visual pretraining.
- Preserve the leakage caveat: close visual relationships between supplied train/test images can make metrics optimistic.
- Report recall, precision, PR AUC and review workload with accuracy.

# Chapters

## 1. Why an ensemble

CNN, MLP, Extra Trees and archive similarity can make different mistakes. A useful ensemble combines complementary signals; it does not add models merely to look advanced. Plan ablation tests to prove each component earns its place.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 2. Full-data Extra Trees

Read the fold loop in train_efficientnet_hybrid.py. The project uses 300 trees, minimum leaf size 2, 20% max features and balanced_subsample class weighting. Explain variance reduction and feature diversity.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 3. Rotating balanced trees

fit_balanced_subset_models uses every fraud image with different 1:8 fraud-to-normal subsets. Multiple learners rotate through normal images and average their probabilities. This balances learning without discarding normal data forever.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 4. MLP signal

The MLP models the existing engineered feature representation. Its value is diversity: it can capture smooth non-linear relationships different from split-based trees and CNN embeddings. Evaluate its out-of-fold value, not just its training score.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 5. Archive similarity

pHash creates a visual signature. Archive similarity compares a query against fraud and legitimate reference hashes. The stack includes fraud similarity, legitimate similarity and their difference. Similarity is an investigation clue, not proof.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 6. Out-of-fold stacking

Every base model predicts a fold it did not train on. These out-of-fold scores fill the stacker training table. This prevents stacking leakage, where a fusion model learns from unrealistically optimistic in-fold predictions.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 7. Calibration and threshold

Platt scaling maps raw stacked scores to better-behaved probabilities. Threshold selection turns a probability into a review policy. The 0.0612 review threshold is recall-first; it is not a probability of guilt.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 8. Comparison dashboard

Compare previous MLP hybrid, CNN standalone, full trees, rotating trees and full hybrid with identical folds. Report accuracy, balanced accuracy, precision, recall, F1, F2, PR AUC, Brier score, confusion matrix and expected flag volume.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

# Deliverables

- Base-model and ablation comparison table
- Leakage-safe stacked artifact
- Calibration/reliability report
- Threshold workload simulation dashboard

# Reviewer questions to master

- What is stacking leakage?
- Why use both fraud and legitimate archive similarity?
- How is calibration different from threshold selection?

# Files copied into this packet

- `project_files/README.md`
- `project_files/docs/architecture.md`
- `project_files/docs/model_card.md`
- `project_files/docs/roadmap_and_estimate.md`
- `project_files/docs/demo_script.md`
- `project_files/src/vericlaim/train.py`
- `project_files/src/vericlaim/train_efficientnet_hybrid.py`
- `project_files/src/vericlaim/features.py`
- `project_files/src/vericlaim/validation.py`
- `project_files/src/vericlaim/model.py`
- `project_files/tests/test_model.py`
- `project_files/scripts/generate_role_engineering_guide.py`

# Canonical project locations

- Dataset: `dataset1/Insurance-Fraud-Detection/Insurance-Fraud-Detection/` (not copied to avoid duplicate large data).
- Current model artifacts: `models/efficientnet_hybrid/` (not copied; use the canonical active artifact).
- Full project: the parent `vericlaim-ai/` folder.
