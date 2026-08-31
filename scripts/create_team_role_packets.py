"""Create eight self-contained learning packets for the VeriClaim AI hackathon team.

The packets intentionally copy source, configuration and documentation only.  They
do not copy the large image dataset or trained artifacts; each guide links to the
canonical project paths so every member works from one source of truth.
"""
from __future__ import annotations

import shutil
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "Team_Role_Packets"


COMMON = [
    "README.md", "docs/architecture.md", "docs/model_card.md",
    "docs/roadmap_and_estimate.md", "docs/demo_script.md",
]

ROLES = [
    {
        "folder": "01_project_lead_product_owner",
        "title": "Project Lead and Product Owner",
        "mission": "Own the problem definition, scope, team coordination, customer value and the final evidence-based story.",
        "files": COMMON + ["VeriClaim_AI_Hackathon_Pitch.pptx"],
        "chapters": [
            ("1. Problem and success definition", "Learn the distinction between fraud triage and fraud judgement. The product must prioritize claims for review, never make an automatic accusation or denial. Define success in customer, investigator and business terms: faster review, useful evidence, manageable workload and auditable decisions."),
            ("2. Stakeholders and journeys", "Map the claimant, investigator, operations lead and compliance reviewer. A claimant needs simple claim submission and status clarity. An investigator needs a score, related evidence, explanations and override controls. Compliance needs a model version, threshold and audit trail."),
            ("3. Scope control", "The supplied task is image-based binary triage. Optional damage category is not a required prediction input because the supplied test data does not consistently include it. Do not promise automatic payment decisions, universal fraud detection or production deployment readiness."),
            ("4. Product architecture", "Read docs/architecture.md. Explain the flow: upload -> visual feature extraction -> model and archive signals -> calibrated risk -> human review. Ask each engineering role for a one-sentence contract and one measurable deliverable."),
            ("5. Metrics as product decisions", "Accuracy is insufficient because fraud is rare. Learn recall, precision, F1, F2, PR AUC and review workload. The active threshold changes the queue size; it does not change the underlying model. Demand a threshold rationale tied to staff capacity."),
            ("6. Governance and risk", "Read the model card. Ensure the UI says review recommendation, not proven fraud. Insist on a limitation slide covering labels, near-duplicate leakage risk, false positives, false negatives and the human investigator's final authority."),
            ("7. Leadership operating rhythm", "Run short daily checkpoints: data/validation status, CNN/ensemble status, app integration status, quality status and presentation status. Maintain one experiment log, one decision log and one source of truth for current model metrics."),
            ("8. Judge preparation", "Be able to pitch the project in two minutes: problem, data imbalance, hybrid solution, human-led workflow, results and honest limitation. Ask each member to explain their module without jargon and demonstrate a controlled Model Lab upload."),
        ],
        "deliverables": ["One-page product brief", "Prioritized backlog and role ownership map", "Decision/risk log", "Final narrative and demo run sheet"],
        "questions": ["What customer harm occurs if the model is treated as a verdict?", "Why is a low review threshold intentional?", "What limitation will you disclose before a judge asks?"],
    },
    {
        "folder": "02_data_validation_engineer",
        "title": "Data and Validation Engineer",
        "mission": "Own dataset understanding, data-quality checks, perceptual grouping, leakage analysis and repeatable validation evidence.",
        "files": COMMON + ["src/vericlaim/features.py", "src/vericlaim/validation.py", "src/vericlaim/train.py", "tests/test_features.py", "tests/test_validation.py", "scripts/download_dataset.py"],
        "chapters": [
            ("1. Dataset schema", "The target is binary: Fraud = 1 and Non-Fraud = 0. The training split contains 5,200 images: 200 fraud and 5,000 non-fraud. The supplied test split contains 1,416 images: 93 fraud and 1,323 non-fraud. Learn the folder convention expected by discover()."),
            ("2. Data-quality audit", "Check file count, target count, unreadable images, extension distribution, dimensions, color channels, duplicate names and missing folders. Record all checks in a reproducible report; never silently skip a corrupt file without reporting it."),
            ("3. Why imbalance matters", "Fraud is 3.85% of training data. An always-non-fraud model can look accurate while finding no fraud. Data engineering supports the model by making class counts and class-specific metrics impossible to ignore."),
            ("4. Visual forensics features", "Read features.py. Understand that image statistics and perceptual hashes are features or evidence signals, not truth. Document every feature version because model artifacts must be compatible with it."),
            ("5. Duplicates and near duplicates", "Exact file hash checks find byte-identical files. Perceptual hashes find visually close files even when resizing or compression changed bytes. The existing audit found 53.7% close visual matches across supplied train/test and 261 identical pHashes; explain why this can inflate results."),
            ("6. Grouped validation", "Read validation.py and the use of StratifiedGroupKFold. Stratified preserves class proportions as much as possible. Grouped splitting keeps perceptually related training photos together, reducing leakage between fit and validation folds."),
            ("7. Data contracts", "Write the inputs that every downstream component expects: image path, binary label for training only, three-channel decoding, feature version and perceptual hash. Add checks that fail loudly if a contract breaks."),
            ("8. Validation report", "Produce train/test class counts, perceptual group count, duplicate audit, fold composition, metrics source and known limitations. Clearly label out-of-fold validation separately from supplied-test evaluation."),
        ],
        "deliverables": ["Dataset audit report", "Duplicate/perceptual-overlap report", "Grouped-fold validation protocol", "Data dictionary and version record"],
        "questions": ["Why are exact duplicates and near duplicates different?", "Why is random splitting unsafe here?", "What does a perceptual distance threshold control?"],
    },
    {
        "folder": "03_deep_learning_engineer",
        "title": "Deep-Learning Engineer",
        "mission": "Own image preprocessing, EfficientNetV2B0 transfer learning, CNN fraud heads, augmentation experiments and standalone CNN evaluation.",
        "files": COMMON + ["src/vericlaim/train_efficientnet_hybrid.py", "src/vericlaim/train_deep.py", "src/vericlaim/model.py", "requirements-deep.txt", "tests/test_model.py", "scripts/generate_role_engineering_guide.py"],
        "chapters": [
            ("1. CNN mental model", "A CNN turns pixels into learned feature maps. Early layers respond to edges and textures; deeper layers combine patterns; global average pooling yields a compact visual embedding. Do not say the model understands intent or uses a single hand-written damage rule."),
            ("2. Project preprocessing", "Read extract_embeddings(). Images are decoded into three RGB channels, padded/resized to 224 x 224 with resize_with_pad, converted to float32, batched and prefetched. Training and web inference must apply the same preprocessing."),
            ("3. EfficientNetV2B0", "The project uses an ImageNet-pretrained EfficientNetV2B0 with include_top=False, average pooling and preprocessing included. It creates a 1,280-number embedding. ImageNet gives generic visual knowledge; no external insurance dataset was added."),
            ("4. Frozen transfer learning", "backbone.trainable = False prevents the millions of backbone weights from changing. With only 200 fraud images, this reduces overfitting risk. Fine-tuning is a future experiment only after strict grouped validation."),
            ("5. CNN fraud head", "The current head is class-balanced logistic regression over embeddings. A sigmoid Dense(1) head is mathematically equivalent. Train heads fold by fold and evaluate held-out fold probabilities, never in-fold training scores."),
            ("6. Class weighting", "class_weight='balanced' makes rare fraud errors count more in the CNN head. It is not the same as creating images or SMOTE. Explain how it prevents the easy always-normal solution."),
            ("7. Augmentation experiments", "Augmentation is optional future work. Try conservative brightness/contrast changes and small rotations only in training folds. Inspect transformed images, keep seeds and compare grouped validation, calibration and error examples."),
            ("8. CNN evaluation and debugging", "Report standalone precision, recall, PR AUC, calibration and confusion matrix. Inspect false negatives and false positives. Check tensor shapes, cache versions, color channels, resize behavior and artifact compatibility before blaming the network."),
        ],
        "deliverables": ["Reproducible preprocessing contract", "CNN backbone and head experiment record", "Standalone CNN metrics/error gallery", "Validated augmentation proposal"],
        "questions": ["Why is the backbone frozen?", "Why is 224 x 224 padding used?", "What does a 1,280-number embedding mean?"],
    },
    {
        "folder": "04_ml_ensemble_engineer",
        "title": "ML and Ensemble Engineer",
        "mission": "Own Extra Trees, MLP, archive similarity, leakage-safe stacking, calibration, thresholding and performance comparison.",
        "files": COMMON + ["src/vericlaim/train.py", "src/vericlaim/train_efficientnet_hybrid.py", "src/vericlaim/features.py", "src/vericlaim/validation.py", "src/vericlaim/model.py", "tests/test_model.py", "scripts/generate_role_engineering_guide.py"],
        "chapters": [
            ("1. Why an ensemble", "CNN, MLP, Extra Trees and archive similarity can make different mistakes. A useful ensemble combines complementary signals; it does not add models merely to look advanced. Plan ablation tests to prove each component earns its place."),
            ("2. Full-data Extra Trees", "Read the fold loop in train_efficientnet_hybrid.py. The project uses 300 trees, minimum leaf size 2, 20% max features and balanced_subsample class weighting. Explain variance reduction and feature diversity."),
            ("3. Rotating balanced trees", "fit_balanced_subset_models uses every fraud image with different 1:8 fraud-to-normal subsets. Multiple learners rotate through normal images and average their probabilities. This balances learning without discarding normal data forever."),
            ("4. MLP signal", "The MLP models the existing engineered feature representation. Its value is diversity: it can capture smooth non-linear relationships different from split-based trees and CNN embeddings. Evaluate its out-of-fold value, not just its training score."),
            ("5. Archive similarity", "pHash creates a visual signature. Archive similarity compares a query against fraud and legitimate reference hashes. The stack includes fraud similarity, legitimate similarity and their difference. Similarity is an investigation clue, not proof."),
            ("6. Out-of-fold stacking", "Every base model predicts a fold it did not train on. These out-of-fold scores fill the stacker training table. This prevents stacking leakage, where a fusion model learns from unrealistically optimistic in-fold predictions."),
            ("7. Calibration and threshold", "Platt scaling maps raw stacked scores to better-behaved probabilities. Threshold selection turns a probability into a review policy. The 0.0612 review threshold is recall-first; it is not a probability of guilt."),
            ("8. Comparison dashboard", "Compare previous MLP hybrid, CNN standalone, full trees, rotating trees and full hybrid with identical folds. Report accuracy, balanced accuracy, precision, recall, F1, F2, PR AUC, Brier score, confusion matrix and expected flag volume."),
        ],
        "deliverables": ["Base-model and ablation comparison table", "Leakage-safe stacked artifact", "Calibration/reliability report", "Threshold workload simulation dashboard"],
        "questions": ["What is stacking leakage?", "Why use both fraud and legitimate archive similarity?", "How is calibration different from threshold selection?"],
    },
    {
        "folder": "05_backend_integration_engineer",
        "title": "Backend and Model Integration Engineer",
        "mission": "Own the reliable connection between uploads, saved model artifacts, prediction API responses, application state and local deployment.",
        "files": COMMON + ["server.py", "src/vericlaim/model.py", "src/vericlaim/train_efficientnet_hybrid.py", "Dockerfile", "pyproject.toml", "requirements.txt", "requirements-deep.txt", "tests/test_model.py"],
        "chapters": [
            ("1. Integration responsibility", "A trained model file is not a feature until the server loads the right artifact, validates user input, performs matching preprocessing and returns a safe, traceable response. Your job is reliability, not retraining."),
            ("2. Artifact contract", "The hybrid artifact stores base models, stacker, calibrator, thresholds, reference hashes, labels, metrics, feature version and CNN backbone path. The Keras backbone file must be compatible with joblib artifact, image size and feature version."),
            ("3. Upload validation", "Accept supported image formats, limit file size, reject corrupt data, avoid trusting filename extensions, generate a safe server-side identifier and never execute uploaded content. Treat PDFs/videos as separate workflows rather than forcing them through the image model."),
            ("4. Prediction response", "Return probability, review label, active threshold, model version, archive-evidence summary and explanation caveat. Do not return language claiming a customer is fraudulent. Keep fields stable so frontend tests do not break."),
            ("5. Error handling", "Differentiate invalid upload, unavailable model artifact, preprocessing failure and internal server error. Log technical detail securely; show the user a clear recoverable message. Never silently substitute an old model."),
            ("6. Performance", "Load model artifacts once at startup, avoid reloading per upload, bound image dimensions and use queues or timeouts for expensive work. Cache only non-sensitive, version-safe artifacts."),
            ("7. Integration tests", "Test known fraud/non-fraud examples, corrupt files, very small images, unusual aspect ratios, missing artifacts and model-version mismatch. Assert response schema and label threshold behavior."),
            ("8. Deployment", "Read Dockerfile and requirements. Pin dependencies, expose health checks, separate secrets from source, and log model version at startup. Local demo deployment is not a production security guarantee."),
        ],
        "deliverables": ["Artifact-loading contract", "Prediction API schema", "Upload/error test suite", "Local run and deployment instructions"],
        "questions": ["How do you know the website uses the new artifact?", "What happens if the backbone file is missing?", "Why must input preprocessing be versioned?"],
    },
    {
        "folder": "06_frontend_uiux_engineer",
        "title": "Frontend and UX Engineer",
        "mission": "Own clear, accessible, trustworthy claim and investigation experiences, including Model Lab and model-comparison presentation.",
        "files": COMMON + ["app/static/index.html", "app/static/styles.css", "app/static/app.js", "assets/vericlaim-cover.png", "server.py"],
        "chapters": [
            ("1. UX goal", "Translate a complicated fraud-triage system into understandable actions. Customers should never feel accused by a score. Investigators should see enough evidence and context to act, not just a colored badge."),
            ("2. Information architecture", "Study Home, Claims, Policies, Contact, Login, customer portal, staff portal and Model Lab. Every screen needs a clear primary action and a plain-language explanation of what will happen next."),
            ("3. Claim evidence experience", "Use a step-by-step upload form with image previews, file limits, progress states, save-draft behavior and accessible errors. Damage type is optional because the model does not require it for supplied test data."),
            ("4. Model Lab", "Show uploaded preview, current and previous model comparison, probability, threshold, final review label, archive similarity and caveat. Make it clear that the output is a review recommendation, not a verdict."),
            ("5. Staff dashboard", "Prioritize queue usefulness: score band, confidence, reason/evidence indicators, case status, model version, review history and investigator override. Avoid ranking people as fraudsters; rank cases for evidence review."),
            ("6. Accessibility", "Use semantic headings, keyboard access, visible focus states, good color contrast, text labels in addition to color, error descriptions and responsive layout. Do not encode fraud/non-fraud only through red/green color."),
            ("7. Trust design", "Explain why a claim was prioritized in plain language. Show uncertainty and the next human step. Include privacy notes, support channel and safe language for customers."),
            ("8. UX testing", "Test with first-time users and staff personas. Observe where users misunderstand fraud wording, evidence upload, status tracking or model output. Turn findings into specific interface changes."),
        ],
        "deliverables": ["Responsive UI flows", "Accessible Model Lab comparison", "Customer/staff microcopy guide", "UX test findings and improvements"],
        "questions": ["How do you avoid accusing a customer in the UI?", "What exact information helps an investigator act?", "How does Model Lab communicate model uncertainty?"],
    },
    {
        "folder": "07_qa_mlops_governance_engineer",
        "title": "QA, MLOps and Model Governance Engineer",
        "mission": "Own test strategy, reproducibility, release gates, monitoring, model card quality, auditability and responsible-use controls.",
        "files": COMMON + ["tests/test_features.py", "tests/test_model.py", "tests/test_validation.py", "src/vericlaim/validation.py", "src/vericlaim/train_efficientnet_hybrid.py", "Dockerfile", "pyproject.toml", "requirements.txt"],
        "chapters": [
            ("1. Quality mindset", "QA asks not only 'does it run?' but 'is the result reproducible, safe to interpret and linked to the correct artifact?' MLOps makes model changes traceable. Governance makes limitations visible."),
            ("2. Test layers", "Unit tests cover feature extraction, validation and model logic. Integration tests cover server-to-model behavior. Regression tests use approved known images. Manual tests cover UX and reviewer interpretation."),
            ("3. Reproducibility", "Record code revision, data location/version, seed, package versions, training arguments, folds, feature version, backbone version, thresholds, artifact hashes and metrics. A result without this context cannot be trusted or reproduced."),
            ("4. Release gate", "Require passing tests, data audit, grouped validation, model comparison, calibration check, error review, updated model card, artifact compatibility check and website smoke test. A better single metric is not enough."),
            ("5. Model card", "Read docs/model_card.md. It should state intended use, prohibited use, data description, metrics, thresholds, limitations, fairness risks, leakage findings, monitoring and ownership."),
            ("6. Monitoring", "Track upload volume, fraud flag rate, review workload, confirmed outcomes where available, false positives, false negatives, calibration, out-of-distribution warnings and drift in image characteristics."),
            ("7. Auditability", "Every prediction should be traceable to input identifier, timestamp, artifact version, preprocessing version, score, threshold, evidence summary and human action. Protect sensitive data and avoid retaining unnecessary images."),
            ("8. Incident response", "If a model gives unexpected results, preserve artifacts/logs, stop automatic routing if needed, assess scope, communicate clearly, fix root cause, add a regression test and document the decision."),
        ],
        "deliverables": ["Test and release checklist", "Experiment/reproducibility log", "Updated model card and risk register", "Monitoring and incident-response plan"],
        "questions": ["What evidence proves a new model is actually deployed?", "What is a release blocker?", "How will you detect data drift?"],
    },
    {
        "folder": "08_presentation_documentation_business_analyst",
        "title": "Presentation, Documentation and Business Analyst",
        "mission": "Own the evidence-backed presentation, requirements traceability, documentation quality, demo narrative and business-value explanation.",
        "files": COMMON + ["VeriClaim_AI_Hackathon_Pitch.pptx", "docs/developer_study_guide.md", "scripts/generate_masterclass_book.py", "scripts/generate_role_engineering_guide.py", "assets/vericlaim-cover.png"],
        "chapters": [
            ("1. Build one coherent story", "Structure every presentation as problem -> user impact -> data constraint -> solution -> demo -> evidence -> limitations -> roadmap. Do not start with algorithms; start with why claims triage matters."),
            ("2. Requirements traceability", "Create a table linking each hackathon requirement to a visible feature, source file, metric or demo step. Examples: neural network objective -> EfficientNetV2B0; imbalance handling -> class weighting plus 1:8 rotations; real-time demo -> Model Lab."),
            ("3. Translate technical terms", "CNN becomes visual feature extractor. Embedding becomes numeric visual summary. Calibration becomes making risk scores more interpretable. Threshold becomes rule for routing a review. Keep the accurate technical word plus plain explanation."),
            ("4. Evidence slides", "Show dataset imbalance, hybrid architecture diagram, comparison metrics, confusion matrix, Model Lab screenshot, human-review flow, standout features and roadmap. Put leakage caveat next to metrics rather than hiding it."),
            ("5. Demo choreography", "Use known local images. State input, expected output and limitation before upload. Show model comparison, probability, threshold, label and archive evidence. Narrate why a human still decides."),
            ("6. Q&A preparation", "Prepare concise answers for: why EfficientNet, why ensemble, how imbalance is handled, why two tire images differ, how threshold works, what leakage means, why no external dataset and what is next."),
            ("7. Documentation standard", "Every document needs a purpose, audience, current artifact version, source links, date, owner and limitation statement. Keep screenshots/metrics current with the active model artifact."),
            ("8. Business case", "Explain value as triage efficiency and investigation support, not guaranteed fraud savings. Discuss false-positive workload, missed-fraud cost, customer trust, human oversight and a phased production roadmap."),
        ],
        "deliverables": ["Requirements traceability matrix", "Final pitch deck and speaker notes", "Demo script and Q&A bank", "Current project documentation index"],
        "questions": ["What makes this more than a generic image classifier?", "How do you explain high accuracy honestly?", "What is the most credible next step?"],
    },
]


def copy_files(packet: Path, relative_paths: list[str]) -> list[str]:
    copied = []
    files_dir = packet / "project_files"
    for relative in relative_paths:
        source = ROOT / relative
        if not source.exists():
            continue
        destination = files_dir / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)
        copied.append(relative)
    return copied


def write_guide(packet: Path, role: dict, copied: list[str]) -> None:
    lines = [
        f"# {role['title']}", "", "## Mission", "", role["mission"], "",
        "## How to use this packet", "",
        "Read the chapters in order. For each chapter, first explain the idea in your own words, then inspect the copied project files, and finally complete one small practical task. Do not make changes in the copied files; modify the canonical project only after the team agrees.", "",
        "## Project guardrails", "",
        "- This system prioritizes a claim for human review; it does not prove fraud or automatically reject a claim.",
        "- Use only the supplied insurance dataset for claim-specific training. ImageNet pretraining is disclosed as generic visual pretraining.",
        "- Preserve the leakage caveat: close visual relationships between supplied train/test images can make metrics optimistic.",
        "- Report recall, precision, PR AUC and review workload with accuracy.", "",
        "# Chapters", "",
    ]
    for heading, text in role["chapters"]:
        lines += [f"## {heading}", "", text, "", "### Learn by doing", "", "- Identify the related copied source or documentation file.", "- Write a two-sentence explanation for a non-technical teammate.", "- Record one risk, assumption or test you would add.", ""]
    lines += ["# Deliverables", ""] + [f"- {item}" for item in role["deliverables"]] + ["", "# Reviewer questions to master", ""] + [f"- {item}" for item in role["questions"]] + ["", "# Files copied into this packet", ""] + [f"- `project_files/{item}`" for item in copied] + ["", "# Canonical project locations", "", "- Dataset: `dataset1/Insurance-Fraud-Detection/Insurance-Fraud-Detection/` (not copied to avoid duplicate large data).", "- Current model artifacts: `models/efficientnet_hybrid/` (not copied; use the canonical active artifact).", "- Full project: the parent `vericlaim-ai/` folder.", ""]
    (packet / "STUDY_GUIDE.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    PACKETS.mkdir(parents=True, exist_ok=True)
    overview = ["# VeriClaim AI Team Role Packets", "", "This folder contains eight learning packets. Each packet has a chapter-based study guide and copies of relevant source/docs. Large dataset and model artifacts remain in the canonical project to prevent conflicting copies.", "", "## Team map", ""]
    for index, role in enumerate(ROLES, start=1):
        packet = PACKETS / role["folder"]
        packet.mkdir(parents=True, exist_ok=True)
        copied = copy_files(packet, role["files"])
        write_guide(packet, role, copied)
        (packet / "README.md").write_text(f"# {role['title']} Packet\n\nStart with [STUDY_GUIDE.md](STUDY_GUIDE.md).\n\nThis packet contains read-only working copies of relevant project files. Use the canonical project for implementation changes.\n", encoding="utf-8")
        overview.append(f"{index}. [{role['title']}]({role['folder']}/STUDY_GUIDE.md) - {role['mission']}")
    overview += ["", "## Shared handoff rule", "", "Every role must record artifact version, data/validation assumptions, tests run, metrics observed, known limitations and the next owner. No role should change the active model or website without a reproducible record.", ""]
    (PACKETS / "README.md").write_text("\n".join(overview), encoding="utf-8")
    print(PACKETS)


if __name__ == "__main__":
    main()
