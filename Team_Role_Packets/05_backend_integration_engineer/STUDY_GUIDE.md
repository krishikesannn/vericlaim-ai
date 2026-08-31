# Backend and Model Integration Engineer

## Mission

Own the reliable connection between uploads, saved model artifacts, prediction API responses, application state and local deployment.

## How to use this packet

Read the chapters in order. For each chapter, first explain the idea in your own words, then inspect the copied project files, and finally complete one small practical task. Do not make changes in the copied files; modify the canonical project only after the team agrees.

## Project guardrails

- This system prioritizes a claim for human review; it does not prove fraud or automatically reject a claim.
- Use only the supplied insurance dataset for claim-specific training. ImageNet pretraining is disclosed as generic visual pretraining.
- Preserve the leakage caveat: close visual relationships between supplied train/test images can make metrics optimistic.
- Report recall, precision, PR AUC and review workload with accuracy.

# Chapters

## 1. Integration responsibility

A trained model file is not a feature until the server loads the right artifact, validates user input, performs matching preprocessing and returns a safe, traceable response. Your job is reliability, not retraining.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 2. Artifact contract

The hybrid artifact stores base models, stacker, calibrator, thresholds, reference hashes, labels, metrics, feature version and CNN backbone path. The Keras backbone file must be compatible with joblib artifact, image size and feature version.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 3. Upload validation

Accept supported image formats, limit file size, reject corrupt data, avoid trusting filename extensions, generate a safe server-side identifier and never execute uploaded content. Treat PDFs/videos as separate workflows rather than forcing them through the image model.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 4. Prediction response

Return probability, review label, active threshold, model version, archive-evidence summary and explanation caveat. Do not return language claiming a customer is fraudulent. Keep fields stable so frontend tests do not break.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 5. Error handling

Differentiate invalid upload, unavailable model artifact, preprocessing failure and internal server error. Log technical detail securely; show the user a clear recoverable message. Never silently substitute an old model.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 6. Performance

Load model artifacts once at startup, avoid reloading per upload, bound image dimensions and use queues or timeouts for expensive work. Cache only non-sensitive, version-safe artifacts.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 7. Integration tests

Test known fraud/non-fraud examples, corrupt files, very small images, unusual aspect ratios, missing artifacts and model-version mismatch. Assert response schema and label threshold behavior.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 8. Deployment

Read Dockerfile and requirements. Pin dependencies, expose health checks, separate secrets from source, and log model version at startup. Local demo deployment is not a production security guarantee.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

# Deliverables

- Artifact-loading contract
- Prediction API schema
- Upload/error test suite
- Local run and deployment instructions

# Reviewer questions to master

- How do you know the website uses the new artifact?
- What happens if the backbone file is missing?
- Why must input preprocessing be versioned?

# Files copied into this packet

- `project_files/README.md`
- `project_files/docs/architecture.md`
- `project_files/docs/model_card.md`
- `project_files/docs/roadmap_and_estimate.md`
- `project_files/docs/demo_script.md`
- `project_files/server.py`
- `project_files/src/vericlaim/model.py`
- `project_files/src/vericlaim/train_efficientnet_hybrid.py`
- `project_files/Dockerfile`
- `project_files/pyproject.toml`
- `project_files/requirements.txt`
- `project_files/requirements-deep.txt`
- `project_files/tests/test_model.py`

# Canonical project locations

- Dataset: `dataset1/Insurance-Fraud-Detection/Insurance-Fraud-Detection/` (not copied to avoid duplicate large data).
- Current model artifacts: `models/efficientnet_hybrid/` (not copied; use the canonical active artifact).
- Full project: the parent `vericlaim-ai/` folder.
