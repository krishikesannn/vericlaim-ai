# Seven-minute demonstration script

## 0:00–0:45 — The decision problem

“A fraud classifier is not enough. Investigators need to know which claim to open first, what evidence drove the alert and when the model is uncertain.”

Show the public homepage, then explain that customers, claims staff and model testers use one connected local system.

## 0:45–2:30 — Analyze a claim

Open **Model Lab**, upload a damage image and show the clear `FRAUD` / `NOT FRAUD` result, probability and balanced binary threshold. Explain that this sandbox does not create a claim.

Run analysis. Point to:

- probability versus threshold;
- archive similarity;
- image-integrity and evidence-quality signals;
- the human-in-the-loop statement.

## 2:30–3:45 — Show novelty

Sign in as the customer, use the guided claim form and leave incident type blank to demonstrate it is optional. Submit the same evidence. Explain that perceptual hashing can surface near matches even after resizing or recompression.

Mention multi-image consistency and amount-versus-visible-damage mismatch as additional investigative leads.

## 3:45–4:45 — Investigator workflow

Sign in as staff. Open **Fraud alerts**, inspect the claim, complete verification and download the investigation evidence PDF. Explain that cases are prioritized by review need and every recommendation keeps its component signals.

## 4:45–5:45 — Performance and honesty

Open **Analytics & reports**. Lead with balanced accuracy, recall, precision and PR-AUC rather than raw accuracy. State that the Kaggle dataset is small and image-only; the score is an investigative lead, not proof.

## 5:45–6:30 — Architecture and deployment

Explain the local CPU prototype, then the cloud pilot path: object storage, validation worker, calibrated model service, vector search, claims integration and monitoring.

## 6:30–7:00 — Close

“VeriClaim does not replace investigators. It gives them a faster, more consistent and auditable way to decide where human attention should go next.”

Ask for approval to run a shadow pilot on time-separated insurer data.

## Likely judge questions

**Why not accuracy?** The classes are strongly imbalanced; a model can appear accurate while missing fraud. We emphasize PR-AUC, recall, precision, F2 and the confusion matrix.

**Is EXIF absence suspicious?** No. EXIF is one weak signal and is never used alone. Many legitimate apps strip metadata.

**Can the model deny claims?** No. The operating policy requires human disposition.

**What is the strongest novelty?** Evidence-level fusion: fraud pattern, near-duplicate archive retrieval, integrity cues, claim consistency and uncertainty routing in one auditable workflow.

**What would improve performance?** Claim-level grouping, more verified fraud mechanisms, fine-tuned vision embeddings, policy/repair metadata and temporal validation.
