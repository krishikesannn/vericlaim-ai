# Project Lead and Product Owner

## Mission

Own the problem definition, scope, team coordination, customer value and the final evidence-based story.

## How to use this packet

Read the chapters in order. For each chapter, first explain the idea in your own words, then inspect the copied project files, and finally complete one small practical task. Do not make changes in the copied files; modify the canonical project only after the team agrees.

## Project guardrails

- This system prioritizes a claim for human review; it does not prove fraud or automatically reject a claim.
- Use only the supplied insurance dataset for claim-specific training. ImageNet pretraining is disclosed as generic visual pretraining.
- Preserve the leakage caveat: close visual relationships between supplied train/test images can make metrics optimistic.
- Report recall, precision, PR AUC and review workload with accuracy.

# Chapters

## 1. Problem and success definition

Learn the distinction between fraud triage and fraud judgement. The product must prioritize claims for review, never make an automatic accusation or denial. Define success in customer, investigator and business terms: faster review, useful evidence, manageable workload and auditable decisions.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 2. Stakeholders and journeys

Map the claimant, investigator, operations lead and compliance reviewer. A claimant needs simple claim submission and status clarity. An investigator needs a score, related evidence, explanations and override controls. Compliance needs a model version, threshold and audit trail.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 3. Scope control

The supplied task is image-based binary triage. Optional damage category is not a required prediction input because the supplied test data does not consistently include it. Do not promise automatic payment decisions, universal fraud detection or production deployment readiness.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 4. Product architecture

Read docs/architecture.md. Explain the flow: upload -> visual feature extraction -> model and archive signals -> calibrated risk -> human review. Ask each engineering role for a one-sentence contract and one measurable deliverable.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 5. Metrics as product decisions

Accuracy is insufficient because fraud is rare. Learn recall, precision, F1, F2, PR AUC and review workload. The active threshold changes the queue size; it does not change the underlying model. Demand a threshold rationale tied to staff capacity.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 6. Governance and risk

Read the model card. Ensure the UI says review recommendation, not proven fraud. Insist on a limitation slide covering labels, near-duplicate leakage risk, false positives, false negatives and the human investigator's final authority.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 7. Leadership operating rhythm

Run short daily checkpoints: data/validation status, CNN/ensemble status, app integration status, quality status and presentation status. Maintain one experiment log, one decision log and one source of truth for current model metrics.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 8. Judge preparation

Be able to pitch the project in two minutes: problem, data imbalance, hybrid solution, human-led workflow, results and honest limitation. Ask each member to explain their module without jargon and demonstrate a controlled Model Lab upload.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

# Deliverables

- One-page product brief
- Prioritized backlog and role ownership map
- Decision/risk log
- Final narrative and demo run sheet

# Reviewer questions to master

- What customer harm occurs if the model is treated as a verdict?
- Why is a low review threshold intentional?
- What limitation will you disclose before a judge asks?

# Files copied into this packet

- `project_files/README.md`
- `project_files/docs/architecture.md`
- `project_files/docs/model_card.md`
- `project_files/docs/roadmap_and_estimate.md`
- `project_files/docs/demo_script.md`
- `project_files/VeriClaim_AI_Hackathon_Pitch.pptx`

# Canonical project locations

- Dataset: `dataset1/Insurance-Fraud-Detection/Insurance-Fraud-Detection/` (not copied to avoid duplicate large data).
- Current model artifacts: `models/efficientnet_hybrid/` (not copied; use the canonical active artifact).
- Full project: the parent `vericlaim-ai/` folder.
