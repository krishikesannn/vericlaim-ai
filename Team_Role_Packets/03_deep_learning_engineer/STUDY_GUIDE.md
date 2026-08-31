# Deep-Learning Engineer

## Mission

Own image preprocessing, EfficientNetV2B0 transfer learning, CNN fraud heads, augmentation experiments and standalone CNN evaluation.

## How to use this packet

Read the chapters in order. For each chapter, first explain the idea in your own words, then inspect the copied project files, and finally complete one small practical task. Do not make changes in the copied files; modify the canonical project only after the team agrees.

## Project guardrails

- This system prioritizes a claim for human review; it does not prove fraud or automatically reject a claim.
- Use only the supplied insurance dataset for claim-specific training. ImageNet pretraining is disclosed as generic visual pretraining.
- Preserve the leakage caveat: close visual relationships between supplied train/test images can make metrics optimistic.
- Report recall, precision, PR AUC and review workload with accuracy.

# Chapters

## 1. CNN mental model

A CNN turns pixels into learned feature maps. Early layers respond to edges and textures; deeper layers combine patterns; global average pooling yields a compact visual embedding. Do not say the model understands intent or uses a single hand-written damage rule.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 2. Project preprocessing

Read extract_embeddings(). Images are decoded into three RGB channels, padded/resized to 224 x 224 with resize_with_pad, converted to float32, batched and prefetched. Training and web inference must apply the same preprocessing.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 3. EfficientNetV2B0

The project uses an ImageNet-pretrained EfficientNetV2B0 with include_top=False, average pooling and preprocessing included. It creates a 1,280-number embedding. ImageNet gives generic visual knowledge; no external insurance dataset was added.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 4. Frozen transfer learning

backbone.trainable = False prevents the millions of backbone weights from changing. With only 200 fraud images, this reduces overfitting risk. Fine-tuning is a future experiment only after strict grouped validation.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 5. CNN fraud head

The current head is class-balanced logistic regression over embeddings. A sigmoid Dense(1) head is mathematically equivalent. Train heads fold by fold and evaluate held-out fold probabilities, never in-fold training scores.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 6. Class weighting

class_weight='balanced' makes rare fraud errors count more in the CNN head. It is not the same as creating images or SMOTE. Explain how it prevents the easy always-normal solution.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 7. Augmentation experiments

Augmentation is optional future work. Try conservative brightness/contrast changes and small rotations only in training folds. Inspect transformed images, keep seeds and compare grouped validation, calibration and error examples.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 8. CNN evaluation and debugging

Report standalone precision, recall, PR AUC, calibration and confusion matrix. Inspect false negatives and false positives. Check tensor shapes, cache versions, color channels, resize behavior and artifact compatibility before blaming the network.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

# Deliverables

- Reproducible preprocessing contract
- CNN backbone and head experiment record
- Standalone CNN metrics/error gallery
- Validated augmentation proposal

# Reviewer questions to master

- Why is the backbone frozen?
- Why is 224 x 224 padding used?
- What does a 1,280-number embedding mean?

# Files copied into this packet

- `project_files/README.md`
- `project_files/docs/architecture.md`
- `project_files/docs/model_card.md`
- `project_files/docs/roadmap_and_estimate.md`
- `project_files/docs/demo_script.md`
- `project_files/src/vericlaim/train_efficientnet_hybrid.py`
- `project_files/src/vericlaim/train_deep.py`
- `project_files/src/vericlaim/model.py`
- `project_files/requirements-deep.txt`
- `project_files/tests/test_model.py`
- `project_files/scripts/generate_role_engineering_guide.py`

# Canonical project locations

- Dataset: `dataset1/Insurance-Fraud-Detection/Insurance-Fraud-Detection/` (not copied to avoid duplicate large data).
- Current model artifacts: `models/efficientnet_hybrid/` (not copied; use the canonical active artifact).
- Full project: the parent `vericlaim-ai/` folder.
