# QA, MLOps and Model Governance Engineer

## Mission

Own test strategy, reproducibility, release gates, monitoring, model card quality, auditability and responsible-use controls.

## How to use this packet

Read the chapters in order. For each chapter, first explain the idea in your own words, then inspect the copied project files, and finally complete one small practical task. Do not make changes in the copied files; modify the canonical project only after the team agrees.

## Project guardrails

- This system prioritizes a claim for human review; it does not prove fraud or automatically reject a claim.
- Use only the supplied insurance dataset for claim-specific training. ImageNet pretraining is disclosed as generic visual pretraining.
- Preserve the leakage caveat: close visual relationships between supplied train/test images can make metrics optimistic.
- Report recall, precision, PR AUC and review workload with accuracy.

# Chapters

## 1. Quality mindset

QA asks not only 'does it run?' but 'is the result reproducible, safe to interpret and linked to the correct artifact?' MLOps makes model changes traceable. Governance makes limitations visible.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 2. Test layers

Unit tests cover feature extraction, validation and model logic. Integration tests cover server-to-model behavior. Regression tests use approved known images. Manual tests cover UX and reviewer interpretation.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 3. Reproducibility

Record code revision, data location/version, seed, package versions, training arguments, folds, feature version, backbone version, thresholds, artifact hashes and metrics. A result without this context cannot be trusted or reproduced.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 4. Release gate

Require passing tests, data audit, grouped validation, model comparison, calibration check, error review, updated model card, artifact compatibility check and website smoke test. A better single metric is not enough.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 5. Model card

Read docs/model_card.md. It should state intended use, prohibited use, data description, metrics, thresholds, limitations, fairness risks, leakage findings, monitoring and ownership.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 6. Monitoring

Track upload volume, fraud flag rate, review workload, confirmed outcomes where available, false positives, false negatives, calibration, out-of-distribution warnings and drift in image characteristics.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 7. Auditability

Every prediction should be traceable to input identifier, timestamp, artifact version, preprocessing version, score, threshold, evidence summary and human action. Protect sensitive data and avoid retaining unnecessary images.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 8. Incident response

If a model gives unexpected results, preserve artifacts/logs, stop automatic routing if needed, assess scope, communicate clearly, fix root cause, add a regression test and document the decision.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

# Deliverables

- Test and release checklist
- Experiment/reproducibility log
- Updated model card and risk register
- Monitoring and incident-response plan

# Reviewer questions to master

- What evidence proves a new model is actually deployed?
- What is a release blocker?
- How will you detect data drift?

# Files copied into this packet

- `project_files/README.md`
- `project_files/docs/architecture.md`
- `project_files/docs/model_card.md`
- `project_files/docs/roadmap_and_estimate.md`
- `project_files/docs/demo_script.md`
- `project_files/tests/test_features.py`
- `project_files/tests/test_model.py`
- `project_files/tests/test_validation.py`
- `project_files/src/vericlaim/validation.py`
- `project_files/src/vericlaim/train_efficientnet_hybrid.py`
- `project_files/Dockerfile`
- `project_files/pyproject.toml`
- `project_files/requirements.txt`

# Canonical project locations

- Dataset: `dataset1/Insurance-Fraud-Detection/Insurance-Fraud-Detection/` (not copied to avoid duplicate large data).
- Current model artifacts: `models/efficientnet_hybrid/` (not copied; use the canonical active artifact).
- Full project: the parent `vericlaim-ai/` folder.
