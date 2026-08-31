# Data and Validation Engineer

## Mission

Own dataset understanding, data-quality checks, perceptual grouping, leakage analysis and repeatable validation evidence.

## How to use this packet

Read the chapters in order. For each chapter, first explain the idea in your own words, then inspect the copied project files, and finally complete one small practical task. Do not make changes in the copied files; modify the canonical project only after the team agrees.

## Project guardrails

- This system prioritizes a claim for human review; it does not prove fraud or automatically reject a claim.
- Use only the supplied insurance dataset for claim-specific training. ImageNet pretraining is disclosed as generic visual pretraining.
- Preserve the leakage caveat: close visual relationships between supplied train/test images can make metrics optimistic.
- Report recall, precision, PR AUC and review workload with accuracy.

# Chapters

## 1. Dataset schema

The target is binary: Fraud = 1 and Non-Fraud = 0. The training split contains 5,200 images: 200 fraud and 5,000 non-fraud. The supplied test split contains 1,416 images: 93 fraud and 1,323 non-fraud. Learn the folder convention expected by discover().

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 2. Data-quality audit

Check file count, target count, unreadable images, extension distribution, dimensions, color channels, duplicate names and missing folders. Record all checks in a reproducible report; never silently skip a corrupt file without reporting it.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 3. Why imbalance matters

Fraud is 3.85% of training data. An always-non-fraud model can look accurate while finding no fraud. Data engineering supports the model by making class counts and class-specific metrics impossible to ignore.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 4. Visual forensics features

Read features.py. Understand that image statistics and perceptual hashes are features or evidence signals, not truth. Document every feature version because model artifacts must be compatible with it.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 5. Duplicates and near duplicates

Exact file hash checks find byte-identical files. Perceptual hashes find visually close files even when resizing or compression changed bytes. The existing audit found 53.7% close visual matches across supplied train/test and 261 identical pHashes; explain why this can inflate results.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 6. Grouped validation

Read validation.py and the use of StratifiedGroupKFold. Stratified preserves class proportions as much as possible. Grouped splitting keeps perceptually related training photos together, reducing leakage between fit and validation folds.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 7. Data contracts

Write the inputs that every downstream component expects: image path, binary label for training only, three-channel decoding, feature version and perceptual hash. Add checks that fail loudly if a contract breaks.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 8. Validation report

Produce train/test class counts, perceptual group count, duplicate audit, fold composition, metrics source and known limitations. Clearly label out-of-fold validation separately from supplied-test evaluation.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

# Deliverables

- Dataset audit report
- Duplicate/perceptual-overlap report
- Grouped-fold validation protocol
- Data dictionary and version record

# Reviewer questions to master

- Why are exact duplicates and near duplicates different?
- Why is random splitting unsafe here?
- What does a perceptual distance threshold control?

# Files copied into this packet

- `project_files/README.md`
- `project_files/docs/architecture.md`
- `project_files/docs/model_card.md`
- `project_files/docs/roadmap_and_estimate.md`
- `project_files/docs/demo_script.md`
- `project_files/src/vericlaim/features.py`
- `project_files/src/vericlaim/validation.py`
- `project_files/src/vericlaim/train.py`
- `project_files/tests/test_features.py`
- `project_files/tests/test_validation.py`
- `project_files/scripts/download_dataset.py`

# Canonical project locations

- Dataset: `dataset1/Insurance-Fraud-Detection/Insurance-Fraud-Detection/` (not copied to avoid duplicate large data).
- Current model artifacts: `models/efficientnet_hybrid/` (not copied; use the canonical active artifact).
- Full project: the parent `vericlaim-ai/` folder.
