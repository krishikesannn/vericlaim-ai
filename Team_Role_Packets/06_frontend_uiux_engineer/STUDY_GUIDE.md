# Frontend and UX Engineer

## Mission

Own clear, accessible, trustworthy claim and investigation experiences, including Model Lab and model-comparison presentation.

## How to use this packet

Read the chapters in order. For each chapter, first explain the idea in your own words, then inspect the copied project files, and finally complete one small practical task. Do not make changes in the copied files; modify the canonical project only after the team agrees.

## Project guardrails

- This system prioritizes a claim for human review; it does not prove fraud or automatically reject a claim.
- Use only the supplied insurance dataset for claim-specific training. ImageNet pretraining is disclosed as generic visual pretraining.
- Preserve the leakage caveat: close visual relationships between supplied train/test images can make metrics optimistic.
- Report recall, precision, PR AUC and review workload with accuracy.

# Chapters

## 1. UX goal

Translate a complicated fraud-triage system into understandable actions. Customers should never feel accused by a score. Investigators should see enough evidence and context to act, not just a colored badge.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 2. Information architecture

Study Home, Claims, Policies, Contact, Login, customer portal, staff portal and Model Lab. Every screen needs a clear primary action and a plain-language explanation of what will happen next.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 3. Claim evidence experience

Use a step-by-step upload form with image previews, file limits, progress states, save-draft behavior and accessible errors. Damage type is optional because the model does not require it for supplied test data.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 4. Model Lab

Show uploaded preview, current and previous model comparison, probability, threshold, final review label, archive similarity and caveat. Make it clear that the output is a review recommendation, not a verdict.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 5. Staff dashboard

Prioritize queue usefulness: score band, confidence, reason/evidence indicators, case status, model version, review history and investigator override. Avoid ranking people as fraudsters; rank cases for evidence review.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 6. Accessibility

Use semantic headings, keyboard access, visible focus states, good color contrast, text labels in addition to color, error descriptions and responsive layout. Do not encode fraud/non-fraud only through red/green color.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 7. Trust design

Explain why a claim was prioritized in plain language. Show uncertainty and the next human step. Include privacy notes, support channel and safe language for customers.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

## 8. UX testing

Test with first-time users and staff personas. Observe where users misunderstand fraud wording, evidence upload, status tracking or model output. Turn findings into specific interface changes.

### Learn by doing

- Identify the related copied source or documentation file.
- Write a two-sentence explanation for a non-technical teammate.
- Record one risk, assumption or test you would add.

# Deliverables

- Responsive UI flows
- Accessible Model Lab comparison
- Customer/staff microcopy guide
- UX test findings and improvements

# Reviewer questions to master

- How do you avoid accusing a customer in the UI?
- What exact information helps an investigator act?
- How does Model Lab communicate model uncertainty?

# Files copied into this packet

- `project_files/README.md`
- `project_files/docs/architecture.md`
- `project_files/docs/model_card.md`
- `project_files/docs/roadmap_and_estimate.md`
- `project_files/docs/demo_script.md`
- `project_files/app/static/index.html`
- `project_files/app/static/styles.css`
- `project_files/app/static/app.js`
- `project_files/assets/vericlaim-cover.png`
- `project_files/server.py`

# Canonical project locations

- Dataset: `dataset1/Insurance-Fraud-Detection/Insurance-Fraud-Detection/` (not copied to avoid duplicate large data).
- Current model artifacts: `models/efficientnet_hybrid/` (not copied; use the canonical active artifact).
- Full project: the parent `vericlaim-ai/` folder.
