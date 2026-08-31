"""Generate eight equal-contribution VeriClaim AI role and speaking guides."""
from __future__ import annotations

import html
from pathlib import Path

from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "eight_member_team_guides"
ARCH = ROOT / "assets" / "diagrams" / "vericlaim-hybrid-fraud-triage-architecture.png"

NAVY = colors.HexColor("#0B1F4D")
INDIGO = colors.HexColor("#30228F")
TEAL = colors.HexColor("#087E8B")
CYAN = colors.HexColor("#66C7D5")
ORANGE = colors.HexColor("#E8753D")
INK = colors.HexColor("#172B4D")
MUTED = colors.HexColor("#52616B")
PALE = colors.HexColor("#F3F7FA")
LIGHT = colors.HexColor("#DCE8EE")
WHITE = colors.white


COMMON_FACTS = [
    ["Training data", "5,200 images: 200 Fraud and 5,000 Non-Fraud (3.85% Fraud)"],
    ["Supplied test", "1,416 images: 93 Fraud and 1,323 Non-Fraud (6.57% Fraud)"],
    ["Deployed visual route", "Frozen ImageNet EfficientNetV2B0, 224 x 224 RGB input, 1,280-dimensional embedding, five grouped heads"],
    ["Non-neural route", "Five full Extra Trees, twenty rotating 1:8 balanced Extra Trees, five MLPs, archive similarity"],
    ["Fusion", "Cross-fitted class-weighted logistic stacker followed by Platt probability calibration"],
    ["Balanced threshold", "6.12% score threshold: 96.12% accuracy, 92.47% Fraud recall, 64.18% precision, 90.48% PR-AUC"],
    ["Confusion matrix", "TN 1,275; FP 48; FN 7; TP 86"],
    ["Leakage caution", "0 exact byte duplicates, but 761 of 1,416 test images have a close perceptual training match"],
    ["Decision policy", "The model prioritizes human review; it never proves fraud and never automatically denies a claim"],
]


ROLES = [
    {
        "num": 1,
        "slug": "deployment_product_integration_engineer",
        "title": "Deployment and Product Integration Engineer",
        "tagline": "Own local, container and cloud deployment, runtime configuration, health checks, rollback coordination and production integration.",
        "major": "Build a reproducible CPU-first local deployment and a free-tier-aware Azure container path that safely serves the approved model with explicit operational guardrails.",
        "foundation": [
            ("Deployment layers", "The same approved model must behave consistently in three layers: a local Python service for development, a Docker container for portability, and an Azure-hosted service for demonstration. Each layer preserves the same preprocessing, artifact version, thresholds and API contract."),
            ("Containerization", "The Dockerfile packages the server, dependencies, static frontend and model-serving code into a repeatable runtime. A container reduces machine-specific failures and gives cloud platforms one defined start command, port and dependency environment."),
            ("Free-tier cloud strategy", "Azure deployment is designed for a low-cost demonstration path with scale-to-zero when the site is not needed. The engineer explains cold starts, quota limits and the difference between a demonstrable deployment and a production insurance service."),
            ("Operational readiness", "Health endpoints, model-card metadata, environment configuration, logs, artifact compatibility and rollback criteria are part of deployment. Deployment is successful only when the correct model loads, requests are traceable and failures are recoverable."),
        ],
        "implementation": [
            "Package the application with the Dockerfile and pin runtime dependencies through pyproject.toml and requirements files.",
            "Use azure.yaml to map the VeriClaim web service to the container deployment configuration.",
            "Maintain deploy-azure-free.ps1 for cloud build, deployment, scale controls and cost-aware shutdown instructions.",
            "Start the service through server.py, verify the configured host and port, then exercise health and model-card endpoints.",
            "Check that the deployed model artifact, preprocessing version and decision thresholds match the approved evaluation evidence.",
            "Document production upgrades: HTTPS, managed identity, secret storage, durable database/blob storage, monitoring and rollback automation.",
        ],
        "insight": "Deployment is an operational contract, not merely a public URL. The current Azure application may be stopped to conserve free-tier quota, while the checked-in container and deployment configuration remain reproducible. Production readiness additionally requires managed identity, durable storage, HTTPS, monitoring and insurer security review.",
        "risks": [
            "Free-tier quota exhaustion, unexpected cost or long cold starts after scale-to-zero.",
            "Loss of SQLite state when an ephemeral cloud container is replaced or restarted.",
            "Serving the wrong model artifact, preprocessing version or threshold configuration.",
            "Secrets embedded in code, scripts, images or deployment logs.",
            "Treating a hackathon deployment as production-ready without insurer security and temporal validation.",
        ],
        "inputs": "Approved model artifact, dependency manifests, server entry point, API contract, environment configuration, health criteria and release checklist.",
        "outputs": "Runnable local service, portable container image, Azure deployment configuration, deployment runbook, health evidence and rollback procedure.",
        "demo": [
            "Show the local start command and confirm the service health endpoint responds.",
            "Explain how the Dockerfile creates the same repeatable runtime for local and cloud execution.",
            "Walk through azure.yaml and the free-tier deployment script without exposing credentials.",
            "Submit one Model Lab request and connect the API response to the approved model version and threshold.",
            "Explain scale-to-zero, cold start, durable-storage limitations and the production hardening roadmap.",
        ],
        "script": "I own deployment and product integration. My responsibility begins after the approved model artifact is selected: I make sure the same preprocessing, thresholds and API behavior run locally, inside Docker and on Azure. The Dockerfile defines a repeatable CPU-first runtime, azure.yaml maps the service for cloud provisioning, and our PowerShell deployment script automates build, deployment and scale controls for a free-tier-aware demonstration. I verify the server start command, health endpoint, model-card metadata and one real inference request before release. I also protect the project from deployment-specific risks. Scale-to-zero saves quota but causes cold starts, and local SQLite storage is not durable when a cloud container is replaced. Therefore our production roadmap moves secrets to managed storage, claims and token history to a durable database, evidence to blob storage, and monitoring to a centralized service. The public URL is not the accomplishment; reproducible, observable and reversible model serving is. I now hand over to our Data and Validation Engineer, who will explain why the model evidence served by this deployment can be trusted and where it remains limited.",
        "qa": [
            ("What exactly is deployed?", "One Python web service that serves the static portals, API routes, approved hybrid model, Model Lab, Claim Passport and Evidence DNA workflow."),
            ("Why use Docker?", "It packages code and dependencies into one repeatable runtime, reducing differences between developer laptops and cloud hosts."),
            ("Does free tier mean production-ready?", "No. It is suitable for a controlled demo; production requires durable storage, managed identity, HTTPS, monitoring, scaling and insurer security review."),
            ("What happens after scale-to-zero?", "The service consumes less quota while stopped, but the first later request may wait for a cold start."),
            ("How do you prevent a model-version mismatch?", "Verify artifact checksum, preprocessing version, feature contract, model-card metadata and thresholds during the release check."),
            ("What is the most important cloud limitation?", "SQLite and local evidence files may be lost on container replacement, so persistent database and blob storage are required for production."),
        ],
        "files": ["Dockerfile", "azure.yaml", "scripts/deploy-azure-free.ps1", "server.py", "pyproject.toml", "requirements.txt", "docs/azure_free_tier_deployment.md"],
    },
    {
        "num": 2,
        "slug": "data_validation_engineer",
        "title": "Data and Validation Engineer",
        "tagline": "Own dataset understanding, quality checks, leakage control, grouped folds and trustworthy evaluation evidence.",
        "major": "Discover and control perceptual-image relationships so near-duplicate images do not leak across validation folds.",
        "foundation": [
            ("Dataset schema", "The supplied dataset is an image-folder binary classification dataset. Each image inherits Fraud or Non-Fraud from its directory. It does not contain claimant history, policy details, repair estimates, timestamps, adjudication reasons or lawful fairness attributes."),
            ("Imbalance", "Fraud is 3.85% of training data. A model that predicts Non-Fraud for every training image would appear highly accurate while detecting no Fraud. The data engineer therefore establishes class counts and the metric policy before modeling begins."),
            ("Data quality", "Validation checks file readability, format, size, color channels, duplicate bytes, perceptual similarity, corrupted files and stable label mapping. Website evidence validation is a different runtime concern and must not be confused with training-data validation."),
            ("Leakage-aware grouping", "Perceptual hashes are clustered using a distance threshold of six. All related images remain in the same StratifiedGroupKFold group. This is stronger than random stratification because visual relatives cannot appear in both training and validation folds."),
        ],
        "implementation": [
            "Inventory train/test folders and produce class distribution tables before feature extraction.",
            "Decode every image and report unreadable, unexpected-mode or inconsistent-size cases.",
            "Compute SHA-256 for exact duplicates and pHash for perceptual relationships.",
            "Construct 3,692 training perceptual groups and feed them into five-fold StratifiedGroupKFold.",
            "Audit the supplied test split: zero exact byte overlap but 761 close perceptual matches, including 261 identical pHashes.",
            "Freeze split assignments and seeds so every model is compared on identical held-out groups.",
        ],
        "insight": "The most important validation insight is that the supplied test set is not visually independent. The reported 90.48% PR-AUC is real for that split, but it may be optimistic. Disclosing this makes the project technically stronger, not weaker.",
        "risks": [
            "Random split leakage from resized, compressed or near-duplicate images.",
            "Fitting preprocessing, thresholds or feature selection on test labels.",
            "Using image-level folds when multiple images may belong to the same underlying event.",
            "Treating perceptual similarity as confirmed duplication without visual or geometric verification.",
        ],
        "inputs": "Raw image folders, labels, image bytes, seed policy and evaluation requirements.",
        "outputs": "Data manifest, EDA tables, quality report, perceptual groups, frozen folds, leakage audit and reusable split IDs.",
        "demo": [
            "Show the class distribution and explain the misleading always-normal baseline.",
            "Display the pHash grouping idea with two transformed images.",
            "Explain five-fold grouped out-of-fold validation in plain language.",
            "Present the exact and perceptual train/test overlap audit.",
            "Hand frozen folds to both neural and ensemble engineers.",
        ],
        "script": "My responsibility begins before training. I verified 5,200 training images with only 200 Fraud examples and 1,416 test images with 93 Fraud examples. That imbalance makes accuracy unsafe as the primary metric. I then checked exact and perceptual relationships. SHA-256 found no exact byte overlap between train and test, but perceptual screening found 761 test images with a close training match. To prevent the same problem inside validation, I formed 3,692 perceptual groups and used five-fold StratifiedGroupKFold, keeping each visual family inside one fold. Every base model therefore produces out-of-fold predictions on images it did not train on. I freeze those fold IDs and give the same split to the CNN, Extra Trees, MLP and stacker. This is the foundation for a fair comparison. The supplied-test score is useful, but I clearly disclose that perceptual overlap may make it optimistic. I now hand over to the Deep-Learning Engineer, who uses these folds to train the EfficientNet visual route safely.",
        "qa": [
            ("Why not use a random stratified split?", "It balances labels but can still place visually related images on both sides, producing leakage."),
            ("Does pHash prove two images are duplicates?", "No. It is a screening signature; close matches require visual or geometric confirmation."),
            ("Why not remove all similar images?", "Similarity may be legitimate dataset structure. We group related images for validation and disclose test overlap rather than deleting evidence without justification."),
            ("What does out-of-fold mean?", "Each training image receives a prediction from a model that was trained on the other folds, not on that image."),
            ("What would production validation change?", "Use insurer-owned, time-separated, claim-level splits and audit performance across operational conditions."),
        ],
        "files": ["src/vericlaim/validation.py", "src/vericlaim/features.py", "tests/test_validation.py", "models/efficientnet_hybrid/model_metrics.json", "output/VeriClaim_AI_Analytics_Submission_Notebook.ipynb"],
    },
    {
        "num": 3,
        "slug": "deep_learning_engineer",
        "title": "Deep-Learning Engineer",
        "tagline": "Own EfficientNetV2B0 preprocessing, transfer learning, visual embeddings, fraud heads, experiments and Grad-CAM.",
        "major": "Build the neural-network route required by the objective while controlling overfitting on only 200 Fraud training images.",
        "foundation": [
            ("CNN mental model", "A convolutional neural network learns hierarchical visual filters. Early layers detect edges and textures; deeper layers combine parts and patterns. Global average pooling compresses the final feature maps into a numeric embedding."),
            ("EfficientNetV2B0", "EfficientNetV2 scales depth, width and input resolution efficiently. The B0 variant is compact enough for the dataset and demo while still providing strong ImageNet visual features. It is a better fit than a very large network that could overfit or become difficult to deploy."),
            ("Transfer learning", "The backbone starts with ImageNet weights, which contain generic knowledge of edges, shapes and objects. No outside insurance-claim dataset is added. The backbone is frozen and the supplied labels train five Fraud-weighted heads on the 1,280-number embedding."),
            ("Grad-CAM", "Grad-CAM combines gradients and convolutional feature maps to highlight regions influencing the CNN score. It explains only the CNN component; it is not a damage detector and does not explain Extra Trees, MLP, archive similarity or policy rules."),
        ],
        "implementation": [
            "Decode to three-channel RGB, resize with padding to 224 x 224 and apply the same preprocessing during training and inference.",
            "Use EfficientNetV2B0 with include_top=False and global average pooling to obtain 1,280-dimensional embeddings.",
            "Keep the deployed backbone frozen because only 200 Fraud images are available.",
            "Train five grouped, class-balanced sigmoid-style heads using leakage-safe folds.",
            "Cache embeddings with a versioned preprocessing contract so downstream models cannot mix incompatible features.",
            "Compare the CNN standalone score against the complete hybrid using identical test labels and thresholds.",
        ],
        "insight": "The CNN alone reached 91.40% Fraud recall and 88.63% PR-AUC, but precision was 55.19%. It learns useful visual representation, yet the hybrid improves ranking and workload by combining complementary evidence.",
        "risks": [
            "Overfitting from unfreezing too many layers on a tiny minority class.",
            "Training/inference mismatch in RGB conversion, resize, padding or preprocessing.",
            "Aggressive augmentation that changes claim meaning or hides forensic artifacts.",
            "Overinterpreting Grad-CAM as proof of damage or fraud reasoning.",
        ],
        "inputs": "Validated RGB images, frozen perceptual-group folds, labels and preprocessing/version contract.",
        "outputs": "1,280-dimensional embeddings, five CNN component scores, standalone metrics, attention map and reproducible model artifacts.",
        "demo": [
            "Show one input becoming a 224 x 224 padded RGB tensor.",
            "Explain backbone, pooling, embedding and sigmoid head without neural-network jargon.",
            "Compare CNN standalone metrics with the final hybrid.",
            "Generate a Grad-CAM heatmap and state its limitation.",
            "Explain why the GPU candidate was evaluated but not promoted.",
        ],
        "script": "I own the required neural-network component. Each claim image is decoded to RGB and resized with padding to 224 by 224, exactly the same way in training and inference. EfficientNetV2B0 then converts the pixels into a 1,280-number visual embedding. We use ImageNet transfer learning for generic visual knowledge, but no additional insurance dataset. Because the training set contains only 200 Fraud images, the deployed backbone is frozen to reduce overfitting. Five grouped, Fraud-weighted heads learn the binary task using folds supplied by our validation engineer. The standalone CNN achieved 91.40% Fraud recall and 88.63% PR-AUC. It is strong, but its 55.19% precision shows that visual evidence alone creates more false alerts. The final system therefore passes its out-of-fold CNN scores into the ensemble stacker. Grad-CAM shows regions influencing the CNN score, but it is not proof of fraud. I now hand over to our ML and Ensemble Engineer, who combines this visual signal with non-neural evidence and calibrates the final probability.",
        "qa": [
            ("Why EfficientNetV2B0?", "It offers a strong accuracy-efficiency tradeoff and is less likely to overfit or burden deployment than a much larger backbone."),
            ("Is ImageNet an extra dataset?", "It is generic pretraining, not an additional insurance-claim dataset; only supplied claim labels train the Fraud heads."),
            ("Why freeze the backbone?", "There are only 200 Fraud training images, so freezing reduces variance and catastrophic overfitting."),
            ("Is the CNN the final classifier?", "It is a required and important base learner. Its out-of-fold score is fused with Extra Trees, MLP and archive similarity."),
            ("What does the embedding contain?", "A learned numeric representation of visual patterns, not a human-readable list of damage rules."),
        ],
        "files": ["src/vericlaim/train_efficientnet_hybrid.py", "src/vericlaim/train_gpu_efficientnet_candidate.py", "src/vericlaim/explainability.py", "requirements-deep.txt", "models/efficientnet_hybrid/model_metrics.json"],
    },
    {
        "num": 4,
        "slug": "ml_ensemble_engineer",
        "title": "ML and Ensemble Engineer",
        "tagline": "Own handcrafted features, Extra Trees, MLP, rotating balance, stacking, calibration, thresholds and model comparison.",
        "major": "Turn several imperfect learners into one leakage-safe, calibrated model that improves Fraud ranking and controls review workload.",
        "foundation": [
            ("Extra Trees", "Extremely Randomized Trees create many decision trees using random feature subsets and random split points. Averaging reduces variance. They are effective for non-linear relationships in handcrafted image features and require little feature scaling."),
            ("MLP", "A multilayer perceptron is a small feed-forward neural network operating on engineered numeric features. It learns smooth interactions that differ from tree splits. It is not the image CNN; its role is model diversity."),
            ("Rotating balanced ensemble", "Every Fraud image appears in each of twenty balanced learners. Different 1:8 Fraud-to-Non-Fraud subsets rotate through majority examples. This focuses learning without permanently discarding normal diversity and without creating synthetic rows."),
            ("Stacking and calibration", "Base models generate out-of-fold probabilities. A class-weighted logistic meta-model learns their combination. Platt scaling then maps the combined score to a better-behaved probability. Threshold selection is a separate operational decision."),
        ],
        "implementation": [
            "Extract color, texture, composition, frequency and oriented-gradient features.",
            "Train five 300-tree full-data Extra Trees models with class weighting and minimum leaf size two.",
            "Train twenty 100-tree rotating balanced Extra Trees models at approximately 1:8 Fraud to Non-Fraud.",
            "Train five Fraud-weighted MLPs on engineered features.",
            "Add Fraud archive similarity, legitimate archive similarity and their difference as separate signals.",
            "Fit the stacker only on out-of-fold base scores, then apply Platt calibration and select three operating thresholds.",
        ],
        "insight": "The hybrid raises precision from 55.19% to 64.18%, recall from 91.40% to 92.47%, F1 from 68.83% to 75.77% and PR-AUC from 88.63% to 90.48% compared with the standalone CNN.",
        "risks": [
            "Stacking leakage from training the meta-model on in-fold base predictions.",
            "Treating calibrated probability as probability of guilt.",
            "Selecting thresholds repeatedly on the supplied test labels.",
            "Adding weak models without ablation evidence that they improve out-of-fold performance.",
        ],
        "inputs": "Frozen folds, engineered features, CNN out-of-fold scores, archive signatures and labels.",
        "outputs": "Base-model scores, fitted stacker, Platt calibrator, threshold policy, comparison table and serialized hybrid artifact.",
        "demo": [
            "Explain one randomized Extra Tree and how many trees vote together.",
            "Use a simple rotating-subset example to show that no class is permanently discarded.",
            "Draw the out-of-fold stacking table and explain leakage prevention.",
            "Show CNN-versus-hybrid metric improvement.",
            "Demonstrate broad, balanced and high-confidence thresholds as workload choices.",
        ],
        "script": "My role is to combine complementary evidence without leaking labels. Extra Trees learn randomized non-linear rules from handcrafted color, texture, composition, frequency and gradient features. Five full-data models retain all 5,200 images with class weighting. Twenty additional Extra Trees models use every Fraud image and rotate through different 1:8 subsets of Non-Fraud images. This is rotating balanced undersampling: it creates no synthetic data and does not throw away majority examples forever. Five Fraud-weighted MLPs learn a different smooth representation, and archive similarity contributes separate Fraud and legitimate-reference signals. Every base model predicts a fold it did not train on. The logistic stacker learns from these out-of-fold scores, then Platt scaling calibrates the output. At the balanced threshold the hybrid reaches 92.47% Fraud recall, 64.18% precision and 90.48% PR-AUC, outperforming the standalone CNN. I now hand over to the Backend and Integration Engineer, who makes sure this exact artifact and preprocessing contract run safely inside the application.",
        "qa": [
            ("Why not use only equal numbers of Fraud and Non-Fraud?", "It would discard most majority diversity. Rotating subsets preserve focus while covering different normal images across models."),
            ("Why not SMOTE?", "SMOTE is poorly suited to raw image semantics and can create unrealistic feature-space samples. The project uses real supplied images only."),
            ("What is the difference between calibration and thresholding?", "Calibration improves score meaning; thresholding chooses an operational action based on cost and capacity."),
            ("Why both MLP and CNN?", "The CNN learns directly from pixels; the MLP learns interactions in engineered numeric features. Their errors can be complementary."),
            ("What proves the ensemble helps?", "Identical-split comparison and ablation metrics, especially PR-AUC, recall, precision, Brier score and review workload."),
        ],
        "files": ["src/vericlaim/features.py", "src/vericlaim/model.py", "src/vericlaim/train.py", "src/vericlaim/train_efficientnet_hybrid.py", "models/efficientnet_hybrid/model_metrics.json"],
    },
    {
        "num": 5,
        "slug": "backend_security_integration_engineer",
        "title": "Backend, Security and Integration Engineer",
        "tagline": "Own model serving, API contracts, persistent claim state, Claim Passport, Evidence DNA and safe module integration.",
        "major": "Connect the trained model to a durable, security-aware claims workflow without changing preprocessing, thresholds or governance semantics.",
        "foundation": [
            ("Inference contract", "The API must decode an uploaded image, validate it, reproduce training preprocessing, call the saved model once, and return component scores, calibrated risk, route, warnings and model version in a stable JSON schema."),
            ("Secure Claim Passport", "A repeat claim receives a short-lived, one-time token bound to account and policy. Only a SHA-256 token digest is stored. Rotation revokes earlier unused tokens; atomic consumption detects replay and survives server restart through SQLite."),
            ("Evidence DNA", "Exact SHA-256, perceptual hashes, transformed variants, multi-scale patches, color descriptors and edge descriptors search previous evidence after crop, rotation, flip, inversion, resize or compression. A match forces review but never proves fraud."),
            ("Persistence and audit", "Accounts, cases, messages, token history and evidence manifests are persisted in SQLite. Every result must record model version, thresholds, component signals, warnings and investigator action."),
        ],
        "implementation": [
            "Load the active PKL/model artifact at startup and fail health checks clearly if incompatible.",
            "Reject unsupported types, excessive sizes and undecodable images before inference.",
            "Expose health, model-card, analyze, cases and decision endpoints through the Python service.",
            "Keep claim submission, token consumption and claim persistence in one transaction.",
            "Return Fraud/No fraud alert separately from operational broad/manual/high routing.",
            "Preserve original evidence and attach Evidence DNA match details for investigator verification.",
        ],
        "insight": "Security signals verify submission integrity and evidence reuse; they do not modify the meaning of the neural score into proof. Keeping these controls separate improves both safety and explainability.",
        "risks": [
            "Preprocessing mismatch between training and web inference.",
            "Token replay, wrong-account use, wrong-policy use or non-atomic claim creation.",
            "Untrusted file parsing, oversized payloads and unsafe metadata handling.",
            "A stale model artifact served with new metrics or thresholds.",
        ],
        "inputs": "Validated uploads, authenticated session, policy identifier, active artifact, threshold configuration and previous evidence manifests.",
        "outputs": "Versioned JSON assessment, claim record, token audit record, Evidence DNA match package and health/monitoring data.",
        "demo": [
            "Call the health and model-card endpoints before analysis.",
            "Upload one image and show component scores plus calibrated route.",
            "Issue a repeat-claim passport, consume it once and demonstrate replay rejection.",
            "Upload a cropped or rotated previous image and show the linked earlier claim.",
            "Restart the server and show that claim/token history remains available.",
        ],
        "script": "I own the boundary between trained AI and the claims workflow. The server loads one approved artifact and exposes a stable analysis contract. Before inference it validates type, size and decodability, then applies the exact RGB and 224-pixel preprocessing used in training. The response separates component evidence, calibrated risk, routing thresholds and limitations. For repeat claims, Secure Claim Passport issues a random ten-minute, one-time token bound to the authenticated account and policy. Only its SHA-256 digest is stored. Rotation revokes an older unused token, and atomic consumption detects replay even after restart. Evidence DNA separately searches previous submissions using exact hashes, perceptual transforms and regional descriptors, so crops, flips, inversions, rotations, resizing and compression can be detected. A match creates a human-review alert, not a fraud verdict. I now hand over to the Frontend and UX Engineer, who presents these complex signals to customers and investigators without misleading them.",
        "qa": [
            ("Does a valid Claim Passport prove a claim is legitimate?", "No. It proves an authenticated repeat-claim submission path for an account and policy."),
            ("Does an Evidence DNA match prove fraud?", "No. It shows likely evidence reuse and links the prior claim for human verification."),
            ("How does replay detection survive restart?", "Token digests and status transitions are persisted in SQLite."),
            ("Why use atomic token consumption?", "It prevents a token from being marked used without a claim, or a claim being created without consuming the one-time token."),
            ("What changes for production?", "Managed identity, HTTPS, object storage, malware scanning, encrypted databases, queues, secrets management and centralized monitoring."),
        ],
        "files": ["server.py", "src/vericlaim/evidence_matching.py", "src/vericlaim/model.py", "tests/test_evidence_matching.py", "docs/architecture.md"],
    },
    {
        "num": 6,
        "slug": "frontend_uiux_engineer",
        "title": "Frontend and UI/UX Engineer",
        "tagline": "Own customer and staff journeys, Model Lab, clear risk communication, accessibility and trustworthy interaction design.",
        "major": "Convert complex model output into understandable actions while preventing users from reading a review alert as a fraud conviction.",
        "foundation": [
            ("Two-audience design", "Customers need claim submission, status, notifications, messaging and support. Staff need prioritized queues, evidence comparison, explanations, verification checklists, decisions and audit context. The interfaces must share data but not expose the same controls."),
            ("Risk language", "Use No fraud alert, Manual review and High-confidence priority rather than Safe, Guilty or Confirmed Fraud. Always show that human review owns the final decision."),
            ("Model Lab", "The lab provides separate previous-model/current-model testing, binary output, calibrated score, component evidence, image quality, Grad-CAM and Evidence DNA matches. Optional incident type prevents unsupported metadata from becoming mandatory."),
            ("Accessibility and trust", "Keyboard navigation, labels, contrast, readable progress, error recovery and explicit upload requirements are part of model safety because poor UX changes evidence quality and user interpretation."),
        ],
        "implementation": [
            "Design navigation for Home, Claims, Policies, Contact, Login and role-specific workspaces.",
            "Build guided claim steps with auto-save, evidence preview, validation feedback and optional incident type.",
            "Show claim timeline: Submitted, Under Review, Approved/Rejected and Settled.",
            "Present component scores and limitations with plain-language explanations in Model Lab.",
            "Expose Evidence DNA match type and previous claim link only to authorized staff where appropriate.",
            "Keep authentication state, draft state and API errors understandable without revealing security secrets.",
        ],
        "insight": "The interface is a governance control. Correct labels, uncertainty display and evidence receipts reduce both customer anxiety and investigator overreliance on a single model score.",
        "risks": [
            "A red Fraud badge appearing more certain than the calibrated evidence supports.",
            "Requiring incident metadata that the dataset does not contain.",
            "Hiding invalid-image reasons or losing claim drafts on errors.",
            "Exposing staff-only evidence history or security details to customers.",
        ],
        "inputs": "API schema, role permissions, thresholds, component explanations, accessibility requirements and customer/staff workflow requirements.",
        "outputs": "Responsive portal, Model Lab, status tracker, evidence intake, staff review workbench, support flows and usability test evidence.",
        "demo": [
            "File a claim through the guided customer flow and show auto-save.",
            "Upload invalid evidence and explain the specific recovery message.",
            "Use Model Lab to compare previous and current model outputs.",
            "Show Grad-CAM and Evidence DNA with limitation labels.",
            "Switch to staff view and complete a verification decision with an audit reason.",
        ],
        "script": "I own how model evidence becomes a safe user experience. The customer flow supports guided claim filing, mixed evidence, optional incident type, auto-saved drafts, status tracking, notifications and secure messages. The staff portal presents pending claims, Fraud alerts, evidence verification and approval workflow. In Model Lab, I separate the binary alert from the operational route and show the calibrated score, component signals, image quality and limitations. We avoid words such as guilty or confirmed fraud because the model only prioritizes review. Grad-CAM is labeled as CNN attention, not damage localization, and Evidence DNA is labeled as a previous-evidence match requiring verification. The interface also explains invalid uploads and preserves drafts, because evidence quality affects model reliability. My major contribution is making transparency and human control visible rather than hiding them in documentation. I now hand over to QA, MLOps and Governance, who verify that the full system remains reproducible, monitored and safe.",
        "qa": [
            ("Why show both Fraud/Not Fraud and risk bands?", "The binary alert supports model testing; risk bands communicate operational priority and uncertainty."),
            ("Why is incident type optional?", "The supplied test data does not reliably provide it, so mandatory input would create unsupported assumptions."),
            ("How does UX improve model quality?", "Clear upload guidance, validation feedback and previews reduce unusable or unintended evidence."),
            ("How do you prevent automation bias?", "Use limitation text, component evidence, neutral language and explicit investigator decision controls."),
            ("What accessibility checks matter?", "Keyboard flow, labels, focus state, contrast, readable errors and non-color-only status communication."),
        ],
        "files": ["app/static/index.html", "app/static/app.js", "app/static/styles.css", "server.py", "docs/demo_script.md"],
    },
    {
        "num": 7,
        "slug": "qa_mlops_governance_engineer",
        "title": "QA, MLOps and Model Governance Engineer",
        "tagline": "Own reproducibility, tests, release gates, artifact lineage, monitoring, responsible use and deployment readiness.",
        "major": "Create a promotion gate that rejects a stronger-looking model unless it improves minority performance, calibration and operational workload.",
        "foundation": [
            ("QA layers", "Unit tests cover feature extraction, validation, model interfaces and Evidence DNA. Integration tests cover API-to-model and token transactions. End-to-end tests cover customer submission through staff decision. Model tests verify metrics, calibration and artifact compatibility."),
            ("Reproducibility", "Record data manifest, fold IDs, seed, code version, feature version, hyperparameters, dependency versions, artifact checksum, thresholds and evaluation output. A PKL file without this lineage is not a reproducible model."),
            ("Promotion gate", "A candidate must improve or safely trade off grouped OOF and held-out PR-AUC, Fraud recall, Brier score, false positives, false negatives and review workload. Accuracy or model size alone cannot trigger promotion."),
            ("Governance", "The model card defines intended use, prohibited use, data limitations, overlap caveat, metrics and production validation. Every decision remains with an authorized human and is logged with rationale."),
        ],
        "implementation": [
            "Run unit tests for validation, features, model behavior and transformation-resistant evidence matching.",
            "Verify saved artifact load, preprocessing version and threshold configuration in a clean environment.",
            "Compare the deployed hybrid against the GPU candidate using the same metric table.",
            "Retain the candidate but do not promote it: recall 83.87% vs 92.47%, PR-AUC 82.64% vs 90.48%, and 66 vs 48 false positives.",
            "Define monitoring for input drift, score drift, calibration, latency, error rate, review volume, overrides and evidence-match rates.",
            "Keep rollback instructions and ensure cloud scale-to-zero does not silently remove persistent state.",
        ],
        "insight": "Model governance is demonstrated by saying no to an attractive experiment. The RTX 4060 candidate had more trainable capacity but worse recall, PR-AUC, calibration and workload, so the deployed model remained unchanged.",
        "risks": [
            "Metric drift between notebook, PPT, model card and live API.",
            "Artifact/version mismatch after a code or dependency update.",
            "Monitoring only uptime while missing calibration or workload drift.",
            "Production use before insurer-owned temporal and claim-level validation.",
        ],
        "inputs": "Source code, tests, data/fold manifest, model artifacts, metric reports, deployment configuration and governance requirements.",
        "outputs": "Test report, release checklist, model registry entry, comparison report, monitoring plan, rollback plan and approved model card.",
        "demo": [
            "Run the automated test suite and show pass/fail scope.",
            "Load the PKL artifact and query model-card/health metadata.",
            "Show the deployed-versus-GPU candidate promotion table.",
            "Demonstrate one replay test and one transformed-evidence test.",
            "Explain the monitoring dashboard and rollback condition.",
        ],
        "script": "I own the evidence that this system is reproducible and governed. The test strategy covers data validation, feature extraction, model interfaces, Evidence DNA transformations, API integration and Claim Passport replay protection. Every release records fold IDs, seed, feature version, dependencies, model checksum, thresholds and metrics. Our most important governance example is the GPU EfficientNetV2-S candidate. Although it was a stronger trainable CNN, it achieved only 83.87% Fraud recall and 82.64% PR-AUC, compared with 92.47% recall and 90.48% PR-AUC for the deployed hybrid. It also increased false positives from 48 to 66 and false negatives from 7 to 15, with worse Brier score. Therefore I retained the experiment but blocked promotion. In production I would monitor drift, calibration, review volume, overrides, latency and error rates, with rollback and human approval. I now hand over to our Presentation, Documentation and Business Analyst, who connects the technical evidence to the final judge narrative and business value.",
        "qa": [
            ("What is your release gate?", "Reproducible grouped validation plus acceptable recall, PR-AUC, calibration, false-positive workload, latency and artifact compatibility."),
            ("Why monitor Brier score?", "It measures probability error and helps detect when confidence becomes unreliable even if ranking stays strong."),
            ("What is the rollback trigger?", "Material metric, calibration, workload, latency or error regression, artifact incompatibility, or governance violation."),
            ("How do you test Evidence DNA?", "Use exact, cropped, rotated, flipped, inverted, resized and compressed variants plus unrelated negatives."),
            ("Is the current test result production-ready?", "No. Perceptual overlap requires insurer-owned temporal claim-level validation and shadow deployment."),
        ],
        "files": ["tests/test_validation.py", "tests/test_features.py", "tests/test_model.py", "tests/test_evidence_matching.py", "docs/model_card.md"],
    },
    {
        "num": 8,
        "slug": "presentation_documentation_business_analyst",
        "title": "Presentation, Documentation and Business Analyst",
        "tagline": "Own requirements traceability, technical storytelling, business interpretation, demo orchestration and evidence consistency.",
        "major": "Make every claim in the final presentation traceable to code, notebook output, model metrics or a clearly labeled product assumption.",
        "foundation": [
            ("Evidence-backed storytelling", "The presentation follows problem, dataset, preprocessing, modeling, validation, comparison, interpretation, integration, limitations and next steps. Each metric is paired with what it means for Fraud detection and investigator workload."),
            ("Requirements traceability", "Map mentor requirements to visible evidence: EDA charts, feature descriptions, architecture, hyperparameters, training outputs, confusion matrix, PR curve, calibration, comparison, PKL loading and executed notebook cells."),
            ("Business interpretation", "False negatives represent missed Fraud opportunities; false positives represent investigator workload and customer friction. The business analyst never converts model scores directly into financial savings without insurer cost data."),
            ("Demo orchestration", "The demo uses one claim journey to connect all eight roles. Each speaker receives equal time, a clear artifact, one major insight and a handoff sentence, avoiding repeated explanations."),
        ],
        "implementation": [
            "Maintain the metric glossary and ensure every displayed value matches model_metrics.json.",
            "Build the AI-first PPT and executed notebook around mentor evaluation criteria.",
            "Document architecture, model card, API, deployment, limitations and future work.",
            "Prepare an equal eight-part speaking schedule with one visual or artifact per speaker.",
            "Create judge Q&A covering imbalance, leakage, neural objective, ensemble rationale, calibration, Evidence DNA, security and production readiness.",
            "Rehearse failure handling so the team can continue if the live server or GPU is unavailable.",
        ],
        "insight": "The strongest story is not that the model is perfect. It is that the team recognized imbalance and leakage, tested a stronger candidate honestly, preserved human control and integrated multiple evidence safeguards into one review workflow.",
        "risks": [
            "PPT, notebook, model card and website showing different metrics.",
            "Too much UI time and insufficient AI/analytics depth.",
            "Eight speakers repeating architecture instead of advancing the story.",
            "Unsupported claims about savings, legal conclusions or production readiness.",
        ],
        "inputs": "Mentor criteria, role deliverables, notebook outputs, model metrics, architecture, UI demo, tests and limitations.",
        "outputs": "Traceability matrix, final deck, presenter notes, demo runbook, Q&A bank, submission checklist and business-value narrative.",
        "demo": [
            "Open the requirements-to-evidence matrix.",
            "Show that the notebook, metrics JSON, PKL artifact and PPT agree.",
            "Run the eight-speaker handoff sequence without repeating content.",
            "Interpret the confusion matrix as missed Fraud versus review workload.",
            "Close with limitations, production validation plan and measurable pilot objectives.",
        ],
        "script": "My responsibility is to make the technical work understandable, consistent and judge-ready. I map every mentor requirement to evidence in the executed notebook, model artifact, metric report, documentation or demo. The story begins with 3.85% Fraud prevalence, explains leakage-aware folds, then moves through EfficientNetV2B0, Extra Trees, MLP, rotating balance, out-of-fold stacking, Platt calibration and threshold tradeoffs. I interpret the confusion matrix operationally: 86 detected Fraud images, 7 missed Fraud images and 48 Non-Fraud images sent to review at the balanced threshold. I also ensure we disclose 761 perceptually close test images and never claim production readiness. Each teammate receives equal speaking time, one owned artifact, one major insight and one integration handoff. Our conclusion is that VeriClaim is a neural-network-led, evidence-integrity and human-review system, not an automatic fraud verdict. The next step is insurer-owned temporal validation followed by shadow deployment and monitored investigator feedback.",
        "qa": [
            ("What should judges remember in one sentence?", "VeriClaim combines a neural visual model with calibrated evidence integrity and secure human-led claim triage."),
            ("Which metric should lead the story?", "PR-AUC and Fraud recall, supported by precision, F1, Brier score and confusion-matrix workload."),
            ("How do you prove equal contribution?", "Each role has a unique artifact, measurable deliverable, integration contract, demo step and speaking section."),
            ("What result must be disclosed?", "The supplied test has substantial perceptual overlap with training, so external temporal validation is required."),
            ("What business value can you safely claim?", "Faster prioritization, reusable evidence screening, auditable decisions and measurable investigator workload; financial savings require insurer pilot data."),
        ],
        "files": ["output/VeriClaim_AI_Analytics_Submission_Notebook.ipynb", "output/VeriClaim_AI_Analytics_Technical_Deck_52_Slides.pptx", "docs/model_card.md", "docs/demo_script.md", "README.md"],
    },
]


PROJECT_PARTS = [
    "Deployment strategy, requirements and product integration",
    "Dataset, EDA and validation",
    "Deep-learning model",
    "ML ensemble, calibration and metrics",
    "Backend, security and integration",
    "Frontend and user experience",
    "QA, MLOps and model governance",
    "Documentation, presentation and business analysis",
]


CROSS_FUNCTIONAL_CONTRIBUTIONS = {
    1: [
        "Led local, Docker and Azure deployment design, runtime requirements, health checks, cost controls and production-integration roadmap.",
        "Verified that data paths, validation dependencies and persistent-storage assumptions remain correct in every runtime environment.",
        "Packaged the neural runtime and checked that EfficientNet preprocessing and model artifacts load consistently after deployment.",
        "Verified the served ensemble version, calibrated thresholds and component schema against the approved metrics artifact.",
        "Integrated server startup, API routing, Claim Passport, Evidence DNA and persistence requirements into one deployable service.",
        "Verified that customer, staff and Model Lab screens call the deployed API correctly and recover from cold-start or service errors.",
        "Worked with QA/MLOps on release validation, monitoring, rollback and environment-specific operational checks.",
        "Documented deployment commands, architecture, limitations, cost controls, demo recovery and production hardening for the team.",
    ],
    2: [
        "Converted data limitations into honest product scope and prevented unsupported claim-level promises.",
        "Led dataset inventory, EDA, data-quality checks, perceptual grouping and leakage audit.",
        "Supplied frozen grouped folds and preprocessing checks to the CNN experiments.",
        "Supplied leakage-safe features, labels and identical folds for ensemble comparison.",
        "Defined runtime evidence-validity checks and stable label/schema assumptions for the API.",
        "Helped design upload validation, quality feedback and optional incident metadata behavior.",
        "Added reproducibility checks for manifests, folds, hashes, seeds and data integrity.",
        "Produced class-distribution, leakage and validation visuals for notebook and presentation.",
    ],
    3: [
        "Translated the objective into a neural image-risk signal that supports review rather than a verdict.",
        "Analyzed image modes and sizes, standardized RGB/224-pixel preprocessing and used grouped folds.",
        "Led EfficientNetV2B0 transfer learning, embeddings, Fraud-weighted heads and Grad-CAM.",
        "Provided out-of-fold CNN scores and embeddings and compared CNN standalone with the hybrid.",
        "Defined the exact preprocessing and artifact contract required by web inference.",
        "Worked on attention-map presentation, model comparison and plain-language CNN explanations.",
        "Recorded seeds, folds, hyperparameters, candidate experiments and promotion evidence.",
        "Explained CNN architecture, transfer learning, limitations and results in the notebook/PPT.",
    ],
    4: [
        "Converted missed-Fraud and false-alert costs into metric and threshold requirements.",
        "Analyzed engineered feature families, class imbalance and fold-safe feature preparation.",
        "Consumed CNN out-of-fold scores and helped evaluate whether the neural route added value.",
        "Led Extra Trees, MLP, rotating balance, archive similarity, stacking, Platt calibration and thresholds.",
        "Defined serialized ensemble outputs, component-score schema and threshold configuration for serving.",
        "Helped design threshold explanations, model-comparison views and investigator workload displays.",
        "Built ablation, calibration, confusion-matrix and candidate-comparison quality gates.",
        "Produced model-comparison tables and simple explanations of imbalance, stacking and calibration.",
    ],
    5: [
        "Mapped the technical model into repeat-claim, evidence-review and audit business workflows.",
        "Implemented runtime evidence decoding, validation, storage schema and persistent evidence manifests.",
        "Reproduced CNN preprocessing in inference and exposed Grad-CAM/model-version outputs safely.",
        "Loaded the approved hybrid artifact and returned calibrated scores, thresholds and components.",
        "Led API serving, SQLite state, Claim Passport, replay protection, Evidence DNA and transactions.",
        "Integrated authentication, drafts, claim submission, Model Lab and staff-review API behavior.",
        "Added API, persistence, replay, transformation and artifact-compatibility tests and health checks.",
        "Documented API contracts, security behavior, deployment flow and production alternatives.",
    ],
    6: [
        "Converted insurer and customer needs into clear claim, tracking, support and review journeys.",
        "Contributed upload-quality guidance, validation feedback, evidence previews and optional-field design.",
        "Presented Grad-CAM and neural output with correct limitations and understandable terminology.",
        "Presented component evidence, calibrated score, model comparison and workload-aware thresholds.",
        "Integrated session, claim, token, analysis, messaging and decision endpoints into the interface.",
        "Led responsive customer portal, staff portal, Model Lab, accessibility and trustworthy risk language.",
        "Performed usability, accessibility, error-recovery and end-to-end workflow regression checks.",
        "Produced screenshots, demo steps, UI explanations and reviewer-facing workflow evidence.",
    ],
    7: [
        "Defined responsible-use constraints, acceptance gates and operational risks with the deployment and integration engineer.",
        "Verified manifests, fold reproducibility, leakage controls and supplied-test caveats.",
        "Evaluated CNN reproducibility, Grad-CAM limitations and the GPU candidate promotion decision.",
        "Verified ensemble ablations, PR-AUC, recall, Brier score, confusion matrix and thresholds.",
        "Tested APIs, model loading, persistence, token replay protection and Evidence DNA transformations.",
        "Tested user journeys, role permissions, risk wording, accessibility and failure recovery.",
        "Led automated QA, artifact lineage, release gates, monitoring, rollback and model governance.",
        "Maintained the model card, test evidence, limitations and consistency checklist for submission.",
    ],
    8: [
        "Led requirements traceability, problem narrative, business interpretation and judge-oriented framing.",
        "Converted EDA, imbalance and leakage results into accurate tables, graphs and observations.",
        "Explained EfficientNetV2B0, transfer learning, embeddings, Grad-CAM and CNN metrics clearly.",
        "Explained Extra Trees, MLP, rotating balance, stacking, calibration and metric tradeoffs.",
        "Documented the API, Claim Passport, Evidence DNA, persistence and deployment architecture.",
        "Structured customer/staff workflow demos and ensured UI claims matched actual backend behavior.",
        "Collected test results, promotion evidence, governance controls and production-validation needs.",
        "Led the executed-notebook story, PPT, demo runbook, Q&A bank and equal team speaking sequence.",
    ],
}


MAJOR_PART_INDEX = {1: 0, 2: 1, 3: 2, 4: 3, 5: 4, 6: 5, 7: 6, 8: 7}


CODE_FEATURE_ASSIGNMENTS = {
    1: {
        "features": ["Local Python service deployment", "Portable Docker runtime", "Free-tier-aware Azure deployment", "Health checks, scale controls and production hardening"],
        "code": [
            ("Dockerfile and azure.yaml", "Explain the portable application image, start command and Azure service mapping."),
            ("scripts/deploy-azure-free.ps1", "Explain cloud build, deployment, scaling, shutdown and cost-aware operation."),
            ("server.py", "Explain application bootstrap, configured host/port and deployed health/model metadata behavior."),
            ("pyproject.toml, requirements.txt and docs/azure_free_tier_deployment.md", "Explain dependency reproducibility, run commands, operational limits and production hardening."),
        ],
    },
    2: {
        "features": ["Dataset schema and EDA", "Training-data quality checks", "Perceptual leakage grouping", "Exact and perceptual overlap audit"],
        "code": [
            ("src/vericlaim/validation.py", "Explain image validation, perceptual grouping and split-safety utilities."),
            ("src/vericlaim/features.py", "Explain image decoding and the data contract required before feature extraction."),
            ("scripts/download_dataset.py", "Explain safe dataset acquisition, archive extraction and reproducible folder setup."),
            ("output/VeriClaim_AI_Analytics_Submission_Notebook.ipynb", "Present executed EDA, class counts, leakage analysis and observations."),
        ],
    },
    3: {
        "features": ["EfficientNetV2B0 visual route", "Transfer learning and fraud heads", "CNN standalone evaluation", "Grad-CAM attention map"],
        "code": [
            ("src/vericlaim/train_efficientnet_hybrid.py", "Explain RGB/224 preprocessing, embedding extraction and grouped CNN-head training."),
            ("src/vericlaim/explainability.py", "Explain gradient-based attention generation and its limitations."),
            ("src/vericlaim/train_gpu_efficientnet_candidate.py", "Explain fine-tuning, focal loss, augmentation and controlled candidate evaluation."),
            ("requirements-deep.txt", "Explain the deep-learning runtime dependencies and reproducibility requirements."),
        ],
    },
    4: {
        "features": ["Extra Trees and MLP learners", "Rotating balanced ensemble", "Out-of-fold stacking", "Platt calibration and threshold selection"],
        "code": [
            ("src/vericlaim/model.py", "Explain base estimators, prediction interfaces, class weighting and saved model behavior."),
            ("src/vericlaim/train.py", "Explain fold training, rotating subsets, stacking, calibration and metric generation."),
            ("src/vericlaim/features.py", "Explain handcrafted color, texture, composition, frequency and gradient features."),
            ("models/efficientnet_hybrid/model_metrics.json", "Explain the ensemble comparison, thresholds, confusion matrix and calibration evidence."),
        ],
    },
    5: {
        "features": ["Prediction and case APIs", "Secure Claim Passport", "Transformation-resistant Evidence DNA", "SQLite persistence and audit history"],
        "code": [
            ("server.py", "Explain routing, authentication, model loading, claim transactions and API responses."),
            ("src/vericlaim/evidence_matching.py", "Explain exact, transformed and regional evidence fingerprints and match types."),
            ("src/vericlaim/model.py", "Explain runtime image analysis, claim-level fusion and route construction."),
            ("docs/architecture.md", "Explain security boundaries, persistence and production backend alternatives."),
        ],
    },
    6: {
        "features": ["Public homepage and navigation", "Customer claim and tracking portal", "Staff investigation workbench", "Model Lab and explanation experience"],
        "code": [
            ("app/static/index.html", "Explain page structure, portals, forms, Model Lab and accessible semantic regions."),
            ("app/static/app.js", "Explain state, API calls, claim submission, model output and role-specific interactions."),
            ("app/static/styles.css", "Explain responsive layout, status hierarchy, accessibility and visual feedback."),
            ("server.py", "Explain the frontend-backend endpoints used by each major screen."),
        ],
    },
    7: {
        "features": ["Automated quality assurance", "Model promotion gate", "Monitoring, rollback and release validation", "Responsible AI and model governance"],
        "code": [
            ("tests/test_validation.py and tests/test_features.py", "Explain deterministic data, grouping, feature and preprocessing regression tests."),
            ("tests/test_model.py and tests/test_evidence_matching.py", "Explain saved-model, inference, transformation and negative-control tests."),
            ("pyproject.toml and requirements files", "Explain clean-environment reproducibility, dependency validation and release compatibility checks."),
            ("docs/model_card.md", "Explain intended use, prohibited use, metrics, limitations and production validation."),
        ],
    },
    8: {
        "features": ["Executed AI/analytics notebook", "Technical PPT and architecture story", "Business-value and workload interpretation", "Demo orchestration, documentation and Q&A"],
        "code": [
            ("output/VeriClaim_AI_Analytics_Submission_Notebook.ipynb", "Explain how code, outputs, EDA, training and evaluation evidence are organized."),
            ("output/VeriClaim_AI_Analytics_Technical_Deck_52_Slides.pptx", "Explain the mentor-aligned technical journey and result consistency."),
            ("docs/demo_script.md", "Explain the end-to-end demo order, speaker handoffs and fallback plan."),
            ("README.md", "Explain setup, project features, model reproduction, APIs, tests and responsible-use statement."),
        ],
    },
}


CODE_LINE_OWNERSHIP = {
    1: [
        ("Dockerfile", "1-9", "Container image, runtime dependencies, exposed port and service start command"),
        ("azure.yaml", "1-8", "Azure service definition and container-hosting mapping"),
        ("scripts/deploy-azure-free.ps1", "1-54", "Azure build, deploy, scaling, shutdown and cost-aware automation"),
        ("server.py", "941-949", "Application startup and service entry point"),
        ("pyproject.toml / requirements.txt", "1-20 / 1-6", "Application package metadata and deployable dependency contract"),
        ("docs/azure_free_tier_deployment.md", "1-60", "Deployment runbook, free-tier constraints and production hardening roadmap"),
    ],
    2: [
        ("scripts/download_dataset.py", "1-42", "Safe dataset download and extraction workflow"),
        ("src/vericlaim/validation.py", "1-146", "Perceptual grouping, grouped holdout and overlap audit"),
        ("src/vericlaim/features.py", "1-124", "Image opening, forensics schema, EXIF, entropy, pHash, gradients and HOG utilities"),
        ("output/VeriClaim_AI_Analytics_Submission_Notebook.ipynb", "EDA cells", "Dataset loading, class distribution, quality and leakage outputs"),
    ],
    3: [
        ("src/vericlaim/train_efficientnet_hybrid.py", "1-247", "EfficientNet embedding extraction, CNN heads and hybrid neural training route"),
        ("src/vericlaim/explainability.py", "1-44", "EfficientNet gradient-based attention-map generation"),
        ("src/vericlaim/train_gpu_efficientnet_candidate.py", "1-145", "GPU fine-tuning, focal loss, loaders, prediction and candidate metrics"),
        ("requirements-deep.txt", "1-4", "Deep-learning dependency contract"),
    ],
    4: [
        ("src/vericlaim/features.py", "125-216", "Final engineered feature vector, forensic outputs and feature-name contract"),
        ("src/vericlaim/model.py", "1-128", "Artifact loading, class similarities, CNN/base probabilities and nearest references"),
        ("src/vericlaim/train.py", "1-391", "Discovery, extraction, balancing, Extra Trees, MLP, stacking, calibration, thresholds and metrics"),
        ("models/efficientnet_hybrid/model_metrics.json", "metric sections", "Model comparison, thresholds, confusion matrices and calibration evidence"),
    ],
    5: [
        ("server.py", "1-230", "SQLite persistence, Claim Passport issuance/rotation/replay checks, accounts and decoding"),
        ("server.py", "272-552", "HTTP helpers, authentication, drafts, Claim Passport endpoint and Model Lab testing"),
        ("server.py", "712-940", "Claim analysis, messaging, status, feedback, reports, receipts and decisions"),
        ("src/vericlaim/evidence_matching.py", "1-219", "Evidence DNA creation, transformation comparison and historical matching"),
        ("src/vericlaim/model.py", "129-265", "Runtime image analysis, claim scoring, calibrated routing and metric loading"),
    ],
    6: [
        ("app/static/app.js", "1-27", "Client state, helpers, navigation, session restore and authentication"),
        ("app/static/app.js", "28-42", "Customer/staff navigation, portal shell, dashboards, claims and staff workflow"),
        ("app/static/app.js", "43-77", "Claim form, drafts, uploads, Model Lab, evidence display, support and startup bindings"),
        ("app/static/index.html", "1-71", "Public pages, customer/staff shells, Model Lab, forms and semantic structure"),
        ("app/static/styles.css", "1-29", "Complete responsive visual system, portals, lab, Evidence DNA, trust and accessibility styling"),
    ],
    7: [
        ("tests/test_validation.py", "1-36", "Perceptual grouping and overlap validation tests"),
        ("tests/test_features.py", "1-37", "Feature-shape and perceptual-distance regression tests"),
        ("tests/test_model.py", "1-58", "Artifact, scoring, legitimate-reference and multi-image model tests"),
        ("tests/test_evidence_matching.py", "1-87", "Exact, flip, inversion, rotation, crop, recompression and negative tests"),
        ("docs/model_card.md", "1-92", "Release limitations, metric evidence, responsible use and production validation"),
        ("pyproject.toml / requirements.txt / requirements-deep.txt", "1-20 / 1-6 / 1-4", "Clean-environment dependency and artifact compatibility validation"),
    ],
    8: [
        ("scripts/build_ai_submission_notebook.py", "1-66", "Executed-notebook construction and output organization"),
        ("scripts/create_team_role_packets.py", "1-218", "Role definitions, project-file allocation and study-guide packet generation"),
        ("scripts/build_deployment_guide_pdf.py", "1-103", "Deployment-book generation, chapter flow and formatted delivery"),
        ("docs/demo_script.md", "1-54", "Integrated demo order, evidence narrative and presenter handoffs"),
        ("docs/roadmap_and_estimate.md", "1-34", "Roadmap, effort, sequencing and future-work ownership"),
    ],
}


DEVELOPMENT_TYPES_BY_ROLE = {
    1: ["Container engineering", "Azure cloud configuration", "DevOps deployment automation", "Application bootstrap", "Environment and dependency engineering", "Deployment documentation and operations"],
    2: ["Data engineering", "Data validation", "Image feature engineering", "EDA and analytics"],
    3: ["Deep learning", "Explainable AI", "GPU model experimentation", "DL environment and dependencies"],
    4: ["Feature engineering", "ML model integration", "ML training and ensembling", "Model evaluation and analytics"],
    5: ["Database and application security", "Backend API and authentication", "Claims workflow backend", "Computer-vision forensics", "Model serving and integration"],
    6: ["Frontend core and authentication", "Portal and workflow frontend", "Claim filing and Model Lab frontend", "HTML and UX structure", "CSS, responsive design and accessibility"],
    7: ["Data QA automation", "Feature QA automation", "Model QA automation", "Evidence-security QA", "Model governance and release assurance", "MLOps dependency validation"],
    8: ["Notebook and analytics engineering", "Team tooling and code allocation", "Document automation", "Technical documentation and demo", "Business analysis and project planning"],
}


def esc(text: str) -> str:
    return html.escape(str(text)).replace("\n", "<br/>")


styles = getSampleStyleSheet()
S = {
    "cover_brand": ParagraphStyle("cover_brand", parent=styles["Normal"], fontName="Helvetica-Bold", fontSize=12, leading=15, textColor=CYAN, alignment=TA_CENTER),
    "cover_title": ParagraphStyle("cover_title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=27, leading=32, textColor=WHITE, alignment=TA_CENTER, spaceAfter=12),
    "cover_sub": ParagraphStyle("cover_sub", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=16, textColor=colors.HexColor("#D9EAF1"), alignment=TA_CENTER),
    "h1": ParagraphStyle("h1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=NAVY, spaceAfter=9),
    "h2": ParagraphStyle("h2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=TEAL, spaceBefore=8, spaceAfter=4),
    "h3": ParagraphStyle("h3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.5, leading=14, textColor=INDIGO, spaceBefore=5, spaceAfter=2),
    "body": ParagraphStyle("body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.4, leading=13.3, textColor=INK, spaceAfter=5),
    "small": ParagraphStyle("small", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.1, leading=11.2, textColor=INK, spaceAfter=3),
    "table_header": ParagraphStyle("table_header", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=8.1, leading=11.2, textColor=WHITE, spaceAfter=0),
    "bullet": ParagraphStyle("bullet", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13, textColor=INK, leftIndent=14, firstLineIndent=-9, bulletIndent=2, spaceAfter=3),
    "callout": ParagraphStyle("callout", parent=styles["BodyText"], fontName="Helvetica-Bold", fontSize=10.2, leading=14.2, textColor=NAVY, alignment=TA_LEFT),
    "quote": ParagraphStyle("quote", parent=styles["BodyText"], fontName="Helvetica-Oblique", fontSize=10, leading=15, textColor=INDIGO, leftIndent=12, rightIndent=12, spaceAfter=6),
}


def p(text, style="body"):
    return Paragraph(esc(text), S[style])


def bullets(items):
    return [Paragraph(esc(item), S["bullet"], bulletText="-") for item in items]


def page_header(canvas, doc):
    canvas.saveState()
    if doc.page == 1:
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, A4[0], A4[1], fill=1, stroke=0)
    else:
        canvas.setFillColor(NAVY)
        canvas.rect(0, A4[1] - 1.15 * cm, A4[0], 1.15 * cm, fill=1, stroke=0)
        canvas.setFont("Helvetica-Bold", 8)
        canvas.setFillColor(WHITE)
        canvas.drawString(1.55 * cm, A4[1] - .72 * cm, "VERICLAIM AI - EIGHT-MEMBER TECHNICAL TEAM GUIDE")
        canvas.setStrokeColor(LIGHT)
        canvas.line(1.55 * cm, 1.35 * cm, A4[0] - 1.55 * cm, 1.35 * cm)
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MUTED)
        canvas.drawString(1.55 * cm, .95 * cm, getattr(doc, "role_title", "Role guide"))
        canvas.drawRightString(A4[0] - 1.55 * cm, .95 * cm, f"Page {doc.page}")
    canvas.restoreState()


def title(text, subtitle=None):
    out = [p(text, "h1")]
    if subtitle:
        out += [p(subtitle, "small"), Spacer(1, 4)]
    return out


def role_flow(role):
    d = Drawing(500, 150)
    role_labels = {
        1: "Deployment and\nIntegration",
        2: "Data\nValidation",
        3: "Deep Learning\nEngineer",
        4: "ML Ensemble\nEngineer",
        5: "Backend and\nSecurity",
        6: "Frontend and\nUI/UX",
        7: "QA, MLOps and\nGovernance",
        8: "Presentation and\nBusiness Analysis",
    }
    labels = ["Validated\ninputs", role_labels[role["num"]], "Owned\nartifact", "Integrated\nsystem", "Human\nreview"]
    fills = [colors.HexColor("#E7F4F6"), colors.HexColor("#DCD6FA"), colors.HexColor("#FFF0E7"), colors.HexColor("#E7F4F6"), colors.HexColor("#DCD6FA")]
    for i, label in enumerate(labels):
        x = 5 + i * 100
        if i < 4:
            d.add(Rect(x + 86, 72, 12, 4, fillColor=TEAL, strokeColor=None))
            d.add(String(x + 92, 82, ">", fontName="Helvetica-Bold", fontSize=14, fillColor=TEAL, textAnchor="middle"))
        d.add(Rect(x, 45, 86, 62, rx=8, ry=8, fillColor=fills[i], strokeColor=INDIGO, strokeWidth=1))
        for j, line in enumerate(label.split("\n")):
            d.add(String(x + 43, 78 - j * 14, line, fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY, textAnchor="middle"))
    d.add(String(250, 125, "Every role owns a major artifact and an explicit integration handoff", fontName="Helvetica-Bold", fontSize=10, fillColor=ORANGE, textAnchor="middle"))
    return d


def metric_chart():
    d = Drawing(500, 175)
    data = [("Accuracy", .9612), ("Balanced acc.", .9442), ("Fraud recall", .9247), ("Precision", .6418), ("F1", .7577), ("PR-AUC", .9048)]
    for i, (label, value) in enumerate(data):
        y = 150 - i * 25
        d.add(String(0, y + 3, label, fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY))
        d.add(Rect(85, y, 350, 12, fillColor=colors.HexColor("#E4E9F2"), strokeColor=None))
        d.add(Rect(85, y, 350 * value, 12, fillColor=TEAL if label != "Precision" else ORANGE, strokeColor=None))
        d.add(String(445, y + 2, f"{value*100:.2f}%", fontName="Helvetica-Bold", fontSize=8, fillColor=NAVY))
    d.add(String(250, 2, "Balanced threshold: 6.12%", fontName="Helvetica-Bold", fontSize=9, fillColor=INDIGO, textAnchor="middle"))
    return d


def table(data, widths, header=True, font=7.8):
    rows = []
    for row_index, row in enumerate(data):
        style = S["table_header"] if header and row_index == 0 else S["small"]
        rows.append([Paragraph(esc(cell), style) for cell in row])
    t = Table(rows, colWidths=widths, repeatRows=1 if header else 0, hAlign="LEFT")
    cmds = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), .45, colors.HexColor("#B9C8D2")),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BACKGROUND", (0, 1 if header else 0), (-1, -1), WHITE),
    ]
    if header:
        cmds += [("BACKGROUND", (0, 0), (-1, 0), NAVY), ("TEXTCOLOR", (0, 0), (-1, 0), WHITE)]
    t.setStyle(TableStyle(cmds))
    return t


def page_break(story):
    story.append(PageBreak())


def build(role):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{role['num']:02d}_{role['slug']}_speaking_and_mastery_guide.pdf"
    doc = SimpleDocTemplate(str(path), pagesize=A4, leftMargin=1.55*cm, rightMargin=1.55*cm, topMargin=1.65*cm, bottomMargin=1.65*cm, title=f"VeriClaim AI - {role['title']}", author="VeriClaim AI Team")
    doc.role_title = role["title"]
    story = [Spacer(1, 4.2*cm), p("VERICLAIM AI", "cover_brand"), Spacer(1, .35*cm), p(f"Member {role['num']} - {role['title']}", "cover_title"), p(role["tagline"], "cover_sub"), Spacer(1, 1*cm)]
    cover_box = Table([[Paragraph("MAJOR OWNED CONTRIBUTION", S["cover_brand"])], [Paragraph(esc(role["major"]), S["cover_sub"]) ]], colWidths=[15.5*cm])
    cover_box.setStyle(TableStyle([("BOX", (0,0), (-1,-1), 1, CYAN), ("BACKGROUND", (0,0), (-1,-1), colors.HexColor("#122B5E")), ("TOPPADDING", (0,0), (-1,-1), 12), ("BOTTOMPADDING", (0,0), (-1,-1), 12)]))
    story += [cover_box, Spacer(1, 1.1*cm), p("Equal speaking weight - distinct technical ownership - explicit integration handoff", "cover_brand"), PageBreak()]

    story += title("1. Role Charter and Equal-Contribution Contract", "Each member owns one major insight and understands how it integrates with all other roles.")
    story += [role_flow(role), Spacer(1, 5), p("Role mission", "h2"), p(role["tagline"]), p("Major contribution", "h2"), p(role["major"], "callout")]
    story += [p("Equal contribution rule", "h2")]
    story += bullets(["Two-minute core presentation plus a concise integration handoff.", "One owned technical artifact shown live or in the notebook/PPT.", "One measurable result or quality gate explained accurately.", "One limitation stated honestly and one production improvement proposed.", "Ability to explain the complete pipeline at overview level, not only an isolated module."])
    page_break(story)

    story += title("2. Contribution Across Every Project Part", "This member contributed throughout the project and provides the deepest ownership in one major area.")
    contribution_rows = [["Project part", "Member contribution", "Responsibility"]]
    for index, (part, contribution) in enumerate(zip(PROJECT_PARTS, CROSS_FUNCTIONAL_CONTRIBUTIONS[role["num"]])):
        responsibility = "MAJOR OWNER" if index == MAJOR_PART_INDEX[role["num"]] else "ACTIVE CONTRIBUTOR"
        contribution_rows.append([part, contribution, responsibility])
    story += [table(contribution_rows, [4.1*cm, 10.4*cm, 2.5*cm]), Spacer(1, 8)]
    story += [p("How to describe the team model", "h2"), p("Every member participated in problem understanding, data, modeling, application integration, testing and presentation. The role title identifies the area where that member contributed the deepest technical ownership, made the key decisions and explains the main insight to reviewers. This is shared delivery with accountable specialization - not isolated work.", "callout")]
    page_break(story)

    story += title("3. Equal Code and Feature Explanation Assignment", "All major features and code areas are divided evenly across eight speakers without repetition.")
    assignment = CODE_FEATURE_ASSIGNMENTS[role["num"]]
    story += [p("Four features this member explains", "h2")]
    story += bullets(assignment["features"])
    story += [p("Four source-code or artifact walkthroughs", "h2")]
    code_rows = [["File or artifact", "What this member explains"]] + [[file, explanation] for file, explanation in assignment["code"]]
    story += [table(code_rows, [6.2*cm, 10.8*cm]), Spacer(1, 8)]
    story += [p("Equal feature-allocation rule", "h2"), p("Each member explains four assigned features and four related code/artifact locations. The member must show the main entry point, inputs, processing, outputs, one test or metric and the integration handoff. Other members may add a short clarification, but they should not repeat the same walkthrough.", "callout")]
    story += [p("Code explanation formula", "h2")]
    story += bullets(["Purpose: what problem this file or function solves.", "Input: data type, shape, schema or state it receives.", "Logic: the important steps, algorithm and safeguards.", "Output: artifact, score, JSON, screen state or test evidence it produces.", "Integration: which component consumes the output next.", "Failure case: one error condition and how the project detects or handles it."])
    page_break(story)

    story += title("4. Verified Line-by-Line and Development-Type Ownership", "Ranges are taken from the current project snapshot and should be refreshed after major source edits.")
    ownership = CODE_LINE_OWNERSHIP[role["num"]]
    development_types = DEVELOPMENT_TYPES_BY_ROLE[role["num"]]
    if len(ownership) != len(development_types):
        raise RuntimeError(f"Development-type mapping mismatch for member {role['num']}")
    ownership_rows = [["File or artifact", "Owned range", "Development type", "Owned code or explanation responsibility"]]
    ownership_rows += [[file, line_range, dev_type, responsibility] for (file, line_range, responsibility), dev_type in zip(ownership, development_types)]
    story += [table(ownership_rows, [3.7*cm, 2.0*cm, 3.3*cm, 8.0*cm]), Spacer(1, 9)]
    story += [p("How ownership should be interpreted", "h2")]
    story += bullets(["The range identifies the source this member must understand, explain, test and maintain during the hackathon.", "Development type identifies whether the range is data, AI/ML, backend, security, frontend, QA, MLOps, DevOps, documentation or business-analysis work.", "Shared interfaces are reviewed by both neighboring members, but one primary owner remains accountable for changes.", "Notebook and JSON artifacts use named cells or sections because they do not have stable source-code line numbers.", "Frontend files are compact/minified, so a small physical line range can contain many functions and features.", "Equal contribution is measured by four assigned features, code complexity, testing and integration responsibility - not identical raw line counts."])
    story += [p("Change-control rule", "h2"), p("Before presentation, run a fresh numbered-line check. If source edits shift the range, update this table and keep the function/responsibility description unchanged unless ownership itself changes.", "callout")]
    page_break(story)

    story += title("5. The Complete Project in One View", "Know the whole system before specializing in your own component.")
    if ARCH.exists():
        story += [Image(str(ARCH), width=17.2*cm, height=9.7*cm), Spacer(1, 5)]
    story += [p("End-to-end explanation", "h2"), p("Claim evidence first passes format, usability and security validation. The same image then follows parallel routes: EfficientNetV2B0 learns a visual representation; Extra Trees and MLP analyze engineered features; archive similarity searches label-aware references. Out-of-fold component scores enter a logistic stacker, Platt calibration improves probability behavior, and thresholds route the case. Evidence DNA, Claim Passport, Grad-CAM and investigator actions remain separately visible and governed."), p("Where this member connects", "h2"), p(f"Input contract: {role['inputs']}"), p(f"Output contract: {role['outputs']}")]
    page_break(story)

    story += title("6. Project Facts Every Team Member Must Know", "These values must remain consistent in the notebook, PPT, model card, website and answers.")
    story += [table([["Fact", "Verified project value"]] + COMMON_FACTS, [4.2*cm, 12.8*cm]), Spacer(1, 8), metric_chart(), p("Interpretation", "h2"), p("At the balanced threshold, 86 of 93 Fraud images are detected, 7 are missed and 48 Non-Fraud images enter review. Precision is lower than recall because the system intentionally prioritizes catching rare Fraud while keeping workload visible. These results belong to the supplied split and are not a production guarantee.")]
    page_break(story)

    story += title("7. Foundations You Must Master", "Explain each concept first in plain language and then with its project-specific technical meaning.")
    for heading, body in role["foundation"]:
        story += [p(heading, "h2"), p(body)]
    story += [p("Self-test", "h2")]
    story += bullets(["Explain each concept without reading the guide.", "Draw the role's input, transformation and output on paper.", "Name one failure mode and the test that would expose it.", "Connect the concept to a real file, metric or demo screen in the project."])
    page_break(story)

    story += title("8. What This Role Implemented", "Use these points as both a learning checklist and evidence of contribution.")
    story += bullets(role["implementation"])
    story += [p("Canonical files to study", "h2")]
    story += bullets(role["files"])
    story += [p("Major technical insight", "h2"), p(role["insight"], "callout"), p("How to prove ownership", "h2"), p("Open one owned file, identify the main function or data structure, explain its inputs and outputs, show one test or metric, and describe the handoff to the next component. This evidence is stronger than saying that the member helped with the module.")]
    page_break(story)

    story += title("9. Integration Responsibilities", "Integration is part of every role, not only the backend role.")
    integ = [
        ["Boundary", "What this member must verify"],
        ["Incoming data", role["inputs"]],
        ["Owned transformation", role["major"]],
        ["Outgoing artifact", role["outputs"]],
        ["Versioning", "Record data/fold version, code version, artifact name, thresholds and assumptions."],
        ["Failure behavior", "Return an explicit warning or safe fallback; never silently change model meaning."],
        ["Governance", "Preserve original evidence, log the model version and keep final claim decisions human-owned."],
    ]
    story += [table(integ, [4.1*cm, 12.9*cm]), Spacer(1, 9), p("Integration handshake", "h2")]
    story += bullets(["Confirm schema, units, shapes, class ordering and missing-value behavior with the previous owner.", "Run one known-good case and one deliberately failing case at the boundary.", "Record the artifact checksum/version and the metrics used to approve it.", "Explain what the next owner may assume and what they must revalidate."])
    story += [p("Team-wide integration sentence", "h2"), p("We integrated eight roles through frozen data folds, versioned artifacts, stable API contracts, shared metric definitions, automated tests and one human-review workflow. Each component remains independently testable, but all components contribute to one calibrated evidence package.", "quote")]
    page_break(story)

    story += title("10. Risks, Limitations and Quality Gates", "A strong engineer can explain when the component should not be trusted.")
    risk_rows = [["Risk", "Required control"]]
    controls = ["Document and test the assumption before release.", "Add a deterministic validation or regression test.", "Expose the limitation in model/UI documentation.", "Block promotion until the failure is resolved or accepted by governance."]
    for i, risk in enumerate(role["risks"]):
        risk_rows.append([risk, controls[i % len(controls)]])
    story += [table(risk_rows, [8.2*cm, 8.8*cm]), Spacer(1, 8), p("Universal project limitations", "h2")]
    story += bullets(["Image labels do not reveal the fraud mechanism or final adjudication evidence.", "A genuine damage image can belong to a fraudulent claim, and an unusual image can be legitimate.", "The supplied test split has substantial perceptual overlap with training.", "No policy history, claimant graph, repair estimate, temporal event or lawful fairness attributes are available.", "External insurer validation and shadow deployment are required before operational use."])
    page_break(story)

    story += title("11. Live Demo Responsibilities", "Every member gets one visible moment in the end-to-end demonstration.")
    for i, step in enumerate(role["demo"], 1):
        story += [KeepTogether([p(f"Demo step {i}", "h3"), p(step)])]
    story += [p("Fallback if the live demo fails", "h2")]
    story += bullets(["Use pre-rendered screenshots and executed notebook outputs.", "Show the saved model metrics JSON and artifact load result.", "Explain the expected request and response using the documented API schema.", "Never improvise a metric or claim that was not produced by the project."])
    page_break(story)

    story += title("12. Two-Minute Presentation Script", "Practice until it sounds natural; preserve the facts and handoff even if you paraphrase.")
    story += [p(role["script"], "quote"), p("Delivery structure", "h2")]
    story += [table([
        ["Time", "Purpose", "What to say"],
        ["0:00-0:20", "Position", "State your role, owned artifact and why it matters."],
        ["0:20-1:10", "Technical depth", "Explain the working method using one diagram, file or metric."],
        ["1:10-1:35", "Evidence", "Show the result, quality gate or failure control."],
        ["1:35-1:50", "Integration", "Explain what you receive and what you hand to the next role."],
        ["1:50-2:00", "Handoff", "Name the next role and the question that role answers."],
    ], [2.2*cm, 3.3*cm, 11.5*cm])]
    page_break(story)

    story += title("13. Reviewer and Judge Questions", "Answer directly, give project evidence, state the limitation and stop.")
    for question, answer in role["qa"]:
        story += [p(question, "h2"), p(answer)]
    story += [p("Answer formula", "h2"), p("Decision -> technical reason -> project evidence -> limitation or next test. Avoid giving a long algorithm lecture before answering the question.")]
    page_break(story)

    story += title("14. Contribution Evidence and Handoff Checklist", "Use this page to prove work was completed and integrated.")
    checklist = [
        "I can identify the exact canonical files and artifacts I own.",
        "I can explain my input schema, transformation, output schema and failure behavior.",
        "I can show one automated test, experiment, metric or usability result.",
        "I can explain how class imbalance and leakage affect my role.",
        "I can state the difference between model evidence and a human claim decision.",
        "I verified that my numbers match model_metrics.json and the executed notebook.",
        "I documented one limitation and one production improvement.",
        "I completed a boundary test with the previous and next owners.",
        "I rehearsed my two-minute section and handoff without repeating another speaker.",
    ]
    story += bullets([f"[ ] {item}" for item in checklist])
    story += [p("Definition of done", "h2"), p("The role is complete only when the owned artifact works, its evidence is reproducible, its limitations are documented, and the next role can consume it through an agreed contract.", "callout")]
    page_break(story)

    story += title("15. Seven-Day Mastery Plan and Core Glossary", "Move from reading to explaining, testing and defending the work.")
    plan = [
        ["Day", "Learning target", "Evidence produced"],
        ["1", "Read this guide and architecture", "One-page role map"],
        ["2", "Inspect owned source files", "Function and data-flow notes"],
        ["3", "Reproduce one test or metric", "Screenshot/log with version"],
        ["4", "Study failure cases and limitations", "Risk-control table"],
        ["5", "Practice the demo and handoff", "Two-minute recorded rehearsal"],
        ["6", "Answer judge questions without notes", "Peer-reviewed Q&A"],
        ["7", "Run the complete team presentation", "Integrated rehearsal checklist"],
    ]
    story += [table(plan, [1.3*cm, 7.3*cm, 8.4*cm]), Spacer(1, 8)]
    glossary = [
        ["Term", "Plain meaning"],
        ["Fraud recall", "Share of actual Fraud images detected."],
        ["Precision", "Share of Fraud alerts that are actually labeled Fraud."],
        ["PR-AUC", "Quality of ranking the rare positive class across thresholds."],
        ["Out-of-fold", "Prediction made by a model that did not train on that sample."],
        ["Calibration", "How closely predicted probabilities match observed frequencies."],
        ["Threshold", "Operational score cutoff for a label or review route."],
        ["Perceptual hash", "Compact visual signature tolerant to some image changes."],
        ["Human-in-the-loop", "A trained person owns the final claim action."],
    ]
    story += [table(glossary, [4.2*cm, 12.8*cm])]

    doc.build(story, onFirstPage=page_header, onLaterPages=page_header)
    return path


def main():
    outputs = [build(role) for role in ROLES]
    for path in outputs:
        reader = PdfReader(str(path))
        text = "".join((page.extract_text() or "") for page in reader.pages)
        if len(reader.pages) < 10 or "Two-Minute Presentation Script" not in text or "Integration Responsibilities" not in text:
            raise RuntimeError(f"Guide validation failed: {path}")
        print(f"{path} | pages={len(reader.pages)} | bytes={path.stat().st_size}")


if __name__ == "__main__":
    main()
