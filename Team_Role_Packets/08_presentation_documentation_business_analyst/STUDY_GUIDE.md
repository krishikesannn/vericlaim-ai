# Presentation, Documentation and Business Analyst

## Mission

Own the evidence-backed presentation, requirements traceability, documentation quality, demo narrative and business-value explanation.

## How to use this packet

Read the chapters in order. For each chapter, first explain the idea in your own words, then inspect the copied project files, and finally complete one small practical task. Do not make changes in the copied files; modify the canonical project only after the team agrees.

## Project guardrails

- This system prioritizes a claim for human review; it does not prove fraud or automatically reject a claim.
- Use only the supplied insurance dataset for claim-specific training. ImageNet pretraining is disclosed as generic visual pretraining.
- Preserve the leakage caveat: close visual relationships between supplied train/test images can make metrics optimistic.
- Report recall, precision, PR AUC and review workload with accuracy.

# Chapters

## 1. Build one coherent story

Structure every presentation as problem -> user impact -> data constraint -> solution -> demo -> evidence -> limitations -> roadmap. Do not start with algorithms; start with why claims triage matters.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 2. Requirements traceability

Create a table linking each hackathon requirement to a visible feature, source file, metric or demo step. Examples: neural network objective -> EfficientNetV2B0; imbalance handling -> class weighting plus 1:8 rotations; real-time demo -> Model Lab.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 3. Translate technical terms

CNN becomes visual feature extractor. Embedding becomes numeric visual summary. Calibration becomes making risk scores more interpretable. Threshold becomes rule for routing a review. Keep the accurate technical word plus plain explanation.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 4. Evidence slides

Show dataset imbalance, hybrid architecture diagram, comparison metrics, confusion matrix, Model Lab screenshot, human-review flow, standout features and roadmap. Put leakage caveat next to metrics rather than hiding it.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 5. Demo choreography

Use known local images. State input, expected output and limitation before upload. Show model comparison, probability, threshold, label and archive evidence. Narrate why a human still decides.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 6. Q&A preparation

Prepare concise answers for: why EfficientNet, why ensemble, how imbalance is handled, why two tire images differ, how threshold works, what leakage means, why no external dataset and what is next.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 7. Documentation standard

Every document needs a purpose, audience, current artifact version, source links, date, owner and limitation statement. Keep screenshots/metrics current with the active model artifact.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 8. Business case

Explain value as triage efficiency and investigation support, not guaranteed fraud savings. Discuss false-positive workload, missed-fraud cost, customer trust, human oversight and a phased production roadmap.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

# Deliverables

- Requirements traceability matrix
- Final pitch deck and speaker notes
- Demo script and Q&A bank
- Current project documentation index

# Reviewer questions to master

- What makes this more than a generic image classifier?
- How do you explain high accuracy honestly?
- What is the most credible next step?

# Files copied into this packet

- `project_files/README.md`
- `project_files/docs/architecture.md`
- `project_files/docs/model_card.md`
- `project_files/docs/roadmap_and_estimate.md`
- `project_files/docs/demo_script.md`
- `project_files/VeriClaim_AI_Hackathon_Pitch.pptx`
- `project_files/docs/developer_study_guide.md`
- `project_files/scripts/generate_masterclass_book.py`
- `project_files/scripts/generate_role_engineering_guide.py`
- `project_files/assets/vericlaim-cover.png`

# Canonical project locations

- Dataset: `dataset1/Insurance-Fraud-Detection/Insurance-Fraud-Detection/` (not copied to avoid duplicate large data).
- Current model artifacts: `models/efficientnet_hybrid/` (not copied; use the canonical active artifact).
- Full project: the parent `vericlaim-ai/` folder.
