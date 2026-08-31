from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, KeepTogether)

OUT = Path(__file__).with_name("Data_Validation_Engineer_Complete_Study_Guide.pdf")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="BookTitle", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=27, leading=33, textColor=colors.HexColor("#123B5D"), alignment=TA_CENTER, spaceAfter=18))
styles.add(ParagraphStyle(name="SubTitle", parent=styles["Normal"], fontSize=13, leading=19, textColor=colors.HexColor("#41627D"), alignment=TA_CENTER))
styles.add(ParagraphStyle(name="Chapter", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=18, leading=24, textColor=colors.HexColor("#0B6E69"), spaceBefore=10, spaceAfter=10))
styles.add(ParagraphStyle(name="H2x", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=colors.HexColor("#123B5D"), spaceBefore=8, spaceAfter=5))
styles.add(ParagraphStyle(name="Bodyx", parent=styles["BodyText"], fontSize=9.4, leading=14, spaceAfter=7))
styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], fontSize=9.3, leading=14, leftIndent=10, rightIndent=10, borderPadding=8, borderColor=colors.HexColor("#92C9C4"), borderWidth=0.7, borderRadius=3, backColor=colors.HexColor("#F1FAF9"), spaceBefore=6, spaceAfter=10))
styles.add(ParagraphStyle(name="CodeBlock", parent=styles["BodyText"], fontName="Courier", fontSize=7.6, leading=10, leftIndent=8, rightIndent=8, backColor=colors.HexColor("#F5F7F9"), borderPadding=7, spaceAfter=8))

def P(text, style="Bodyx"): return Paragraph(text, styles[style])
def bullets(items): return [P("• " + x) for x in items]
def table(rows, widths=None):
    t=Table(rows, colWidths=widths, repeatRows=1, hAlign="LEFT")
    t.setStyle(TableStyle([
      ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#123B5D")), ("TEXTCOLOR",(0,0),(-1,0),colors.white),
      ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),
      ("LEADING",(0,0),(-1,-1),11),("VALIGN",(0,0),(-1,-1),"TOP"),
      ("GRID",(0,0),(-1,-1),0.3,colors.HexColor("#C8D4DD")), ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#F4F8FA")]),
      ("LEFTPADDING",(0,0),(-1,-1),6),("RIGHTPADDING",(0,0),(-1,-1),6),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    return t

def chapter(title, intro, sections):
    flow=[P(title,"Chapter"), P(intro,"Callout")]
    for heading, body in sections:
      flow += [P(heading,"H2x")]
      if isinstance(body, list): flow += body
      elif isinstance(body, str): flow += [P(body)]
      else: flow += [body]
    return flow

def footer(canvas, doc):
    canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#BDD5E4")); canvas.line(1.5*cm,1.35*cm,19.5*cm,1.35*cm)
    canvas.setFont("Helvetica",8); canvas.setFillColor(colors.HexColor("#527086")); canvas.drawString(1.5*cm,.85*cm,"VeriClaim AI | Data Validation Engineer Study Guide")
    canvas.drawRightString(19.5*cm,.85*cm,f"Page {doc.page}"); canvas.restoreState()

story=[]
story += [Spacer(1,3.3*cm),P("VERICLAIM AI","BookTitle"),P("Data Validation Engineer\nComplete Study Guide", "BookTitle"),P("From raw claim images to trustworthy evaluation", "SubTitle"),Spacer(1,1*cm),P("Purpose", "H2x"),P("This is a project-specific learning book. It teaches the role, explains the current code, gives repeatable checks, and prepares you for technical review questions. Fraud flags are review priorities, never automatic decisions.","Callout"),PageBreak()]

story += chapter("How to use this book", "Read in order. First understand the plain-language idea, then locate the listed project code, then complete the practice activity. Keep a validation log: date, dataset version, command, result, limitation, and owner.", [
("Your role in one sentence", "You make sure the system learns from the right images, does not accidentally see answers during training, and is evaluated honestly."),
("What you own", bullets(["Dataset inventory and data dictionary.","Image readability, schema and label checks.","Exact and near-duplicate audits.","Leakage-aware grouped validation and reproducible split records.","Validation reports that include uncertainty and limitations."])),
("What you do not claim", "You do not declare an image fraudulent, approve/reject a claim, or treat a model probability as evidence by itself. Your job is to protect the quality of information that reaches the model and reviewers."),
("Suggested 3-week learning route", table([["Week","Outcome","Practice"],["1","Understand images, labels, imbalance","Inventory folders; inspect 20 examples per class"],["2","Understand similarity and leakage","Run/interpret pHash and overlap audit"],["3","Understand evaluation","Explain grouped folds, threshold and metrics to a teammate"]],[2*cm,5*cm,10*cm]))])

story += chapter("1. The problem and data schema", "VeriClaim AI is a binary, image-based claim-triage system. It prioritizes images for human investigation; it does not prove fraud.", [
("The supplied dataset", table([["Split","Fraud","Non-Fraud","Total","Fraud rate"],["Training","200","5,000","5,200","3.85%"],["Supplied test","93","1,323","1,416","6.57%"]],[2.7*cm,2.5*cm,3*cm,2.5*cm,3*cm])),
("Label contract", "For training only, Fraud maps to 1 and Non-Fraud maps to 0. A test image may have a hidden or unknown label in the live portal; the application must never invent a ground truth label from its prediction."),
("Folder schema", P("dataset root/\n  train/\n    Fraud/          -> label 1\n    Non-Fraud/      -> label 0\n  test/\n    Fraud/          -> label 1 (evaluation only)\n    Non-Fraud/      -> label 0 (evaluation only)","CodeBlock")),
("Data dictionary", table([["Field","Meaning","Why validate it"],["path","image location","must exist and remain inside dataset root"],["label","0 or 1","must be known for supervised training"],["sha256","byte-level fingerprint","find exact copies"],["perceptual_hash","visual fingerprint","find resized/compressed near copies"],["width, height, format","decoded image properties","detect unusable or surprising files"],["feature_version","feature recipe identifier","prevents artifact/code mismatch"]],[3*cm,6*cm,7.7*cm]))])

story += chapter("2. Why data validation comes before machine learning", "A model cannot repair a wrong label, a corrupt image, a hidden duplicate, or an unrealistic split. Validation is risk control, not cleaning for appearance.", [
("The ingestion gate", P("RAW FOLDERS -> discover files -> decode image -> validate label/schema -> fingerprint -> audit -> approved manifest -> training/evaluation", "CodeBlock")),
("Checks to run", bullets(["File count by split and label; compare to the expected inventory.","Allowed extensions, readable bytes and successful PIL decode.","Width, height, aspect ratio, color mode and unusually tiny images.","Folder names and label mapping; no unexpected class folder.","Exact duplicate file hashes and visually close perceptual hashes.","Missing EXIF is not fraud. Treat metadata as a weak context signal only.","Feature vector dimension and feature version consistency."])),
("Fail loudly", "A corrupt image should be reported with its path and reason. Do not silently drop it, because silently changing which images are used makes a later result impossible to reproduce."),
("Mini exercise", "Choose five images from each class. Record dimensions, format, SHA-256, pHash and whether the visual content seems related. Then explain why image similarity is not automatically proof of duplicate claims.")])

story += chapter("3. Class imbalance: why accuracy can mislead", "Only about 4 in 100 training images are fraud. A lazy model predicting Non-Fraud for every image would obtain about 96.15% training accuracy and still catch zero fraud.", [
("Confusion matrix", table([["Actual / Predicted","Non-Fraud","Fraud"],["Non-Fraud","True negative (TN)","False positive (FP): unnecessary review"],["Fraud","False negative (FN): missed review candidate","True positive (TP): correctly prioritized"]],[4*cm,6.2*cm,6.2*cm])),
("Metrics you must report", bullets(["Recall = TP / (TP + FN): of actual fraud, how many were flagged?","Precision = TP / (TP + FP): of flags, how many were actually fraud?","F1 balances precision and recall. F2 weights recall more strongly.","PR AUC is useful when fraud is rare; ROC AUC alone can look impressive in imbalanced data.","Balanced accuracy averages class-specific recall; it does not let majority examples dominate.","Review workload = flags per 1,000 images. It connects model behavior to human capacity."])),
("Current supplied-test snapshot", "At the selected threshold (.0612), the current hybrid reported: TN 1,275, FP 48, FN 7, TP 86; accuracy .9612, recall .9247, precision .6418, F1 .7577, F2 .8498, ROC AUC .9759 and PR AUC .9048. Treat this as a dataset-specific evaluation, not a production promise."),
("Key distinction", "Imbalance handling belongs in training. Evaluation must preserve the natural, imbalanced population so the reported workload and precision stay realistic.")])

story += chapter("4. Image fingerprints and feature forensics", "The project uses two identities: SHA-256 answers 'are these exact same bytes?'; perceptual hash answers 'do these look visually close?'", [
("Exact versus perceptual", table([["Method","Detects","Can miss"],["SHA-256","same file bytes","same photo resized, compressed or cropped"],["pHash","visually similar structure","different scenes that look broadly similar; semantic truth"],["manual review","context and claim relevance","scale and consistency without a protocol"]],[3.2*cm,7*cm,6.2*cm])),
("How pHash works", "features.py converts the image to a small gray version, takes low-frequency DCT information and writes 63 comparison bits as hexadecimal. Hamming distance counts bit positions that differ. A distance of 0 means identical pHash, not necessarily identical file bytes."),
("Current forensic record", "ImageForensics stores width, height, megapixels, aspect ratio, format, EXIF/GPS presence, editing software tag, capture time, SHA-256, pHash, quality score and a narrow edit-software tamper signal. None of these is a fraud verdict."),
("Important limitation", "A Photoshop or editor tag can occur in innocent workflows; absence of metadata can arise from messaging apps. Use these fields for explanation and review context, never as a sole rule.")])

story += chapter("5. Near duplicates, transitive groups and leakage", "Leakage happens when information from a validation/test image is effectively present during training. Visually repeated claim photos are a major leakage route in image datasets.", [
("The risk", "The supplied split audit found 53.7% of test images had a close training-image match, including 261 identical pHashes. This can make a model appear better because it has already seen almost the same visual pattern."),
("Why groups are transitive", P("A is close to B; B is close to C.\nEven if A is not directly close to C, all three belong together.\nA -- B -- C  =>  one perceptual group", "CodeBlock")),
("Current code walkthrough", bullets(["validation.py uses a BK-tree to search pHash values efficiently within a Hamming radius.","Union-Find merges matching images into connected components.","build_perceptual_groups() assigns one integer group per component.","The default maximum distance is 6. Lower is stricter; higher catches more similarity but can over-group unrelated images.","perceptual_overlap_audit() reports close matches, identical pHashes, cross-label close matches and nearest-distance histogram."])),
("Cross-label matches", "A close match whose labels differ is not automatically a bad label. It is a priority for inspection: it may be visually generic, an ambiguous case, a mislabeled file, or a threshold artifact.")])

story += chapter("6. Grouped validation: an honest rehearsal", "Validation is a rehearsal of deployment. Related images must not cross the boundary between fitting and evaluation.", [
("Random split versus grouped split", table([["Approach","What it preserves","Main danger"],["Random stratified split","rough fraud proportion","near copies can appear on both sides"],["Stratified group split","rough proportion and group isolation","fold sizes/class rates may vary slightly"],["Supplied test split","organizer protocol","may contain visual overlap; disclose audit"]],[4*cm,6.3*cm,6.1*cm])),
("Current implementation", "grouped_holdout_indices(labels, groups, folds=5, random_state=42) uses StratifiedGroupKFold. It checks that the fit and validation group sets do not overlap and raises an error if they do."),
("Validation protocol", bullets(["Freeze the dataset manifest and hash it.","Compute pHash for every training image using a recorded code version.","Build groups with recorded radius 6 and random seed 42.","Create 5 stratified group folds.","Train only on four folds; create out-of-fold predictions only for the held-out fold.","Choose threshold from validation/out-of-fold predictions, not from the final test set.","Evaluate once on supplied test and publish the leakage caveat."])),
("Review question", "Why not simply deduplicate everything? Because similar photos may be legitimate multiple views of a vehicle. Grouping is safer: it prevents evaluation contamination without assuming a claim is invalid.")])

story += chapter("7. Reading the project code", "You are not expected to memorize every line. Be able to explain the purpose, inputs, outputs and failure modes of each function.", [
("features.py", table([["Function","Input -> output","Role relevance"],["_open_image","path/bytes -> decoded image, raw bytes","decode reliably and preserve raw bytes for SHA"],["extract_features","image -> numeric vector + ImageForensics","deterministic feature/forensic contract"],["_perceptual_hash","gray pixels -> 16-hex pHash","near-duplicate screening"],["hamming_distance","two pHashes -> integer distance","similarity thresholding"],["feature_names","none -> ordered list","feature vector auditability"]],[4.3*cm,6.2*cm,5.9*cm])),
("validation.py", table([["Function","Purpose","What to test"],["build_perceptual_groups","build transitive similarity groups","empty list, exact duplicates, chains"],["grouped_holdout_indices","produce isolated fit/validation indices","no group overlap, reproducibility"],["perceptual_overlap_audit","screen train/test visual overlap","counts, rate, conflicts, histogram"]],[4.3*cm,6.2*cm,5.9*cm])),
("A useful test", P("assert not (set(groups[fit]) & set(groups[validation]))\nassert len(features) == len(feature_names())\nassert label in {0, 1}\nassert image_decodes_successfully", "CodeBlock"))])

story += chapter("8. Reproducibility and data contracts", "A data contract is a written promise between components. If it changes, the pipeline should fail or explicitly version the change.", [
("Minimum contract", table([["Contract item","Current expectation","Failure response"],["Image decode","valid image readable by PIL","quarantine + log path/reason"],["Label","binary 0/1 for training","fail manifest build"],["Feature vector","ordered, deterministic; version vericlaim-vision-v1","reject incompatible artifact"],["Fingerprint","63-bit pHash hex and SHA-256","recompute and record tool version"],["Split","group isolation and recorded seed","abort validation if groups cross"]],[3.6*cm,7.2*cm,5.6*cm])),
("Manifest fields", "dataset_version, source_path, relative_path, split, label, SHA-256, pHash, image width/height/format, group_id, extraction timestamp, feature version, code commit or archive identifier."),
("Reproducible does not mean unchanged", "You may improve the pipeline. When you do, create a new manifest/version and compare results. Never overwrite a result without recording the code, threshold and data version that generated it."),
("No external claim data", "This project trains claim-specific behavior only from the supplied insurance dataset. Generic ImageNet pretrained visual weights are disclosed separately; they are not additional insurance claim examples.")])

story += chapter("9. Your validation report", "A strong report lets another teammate reproduce your conclusion and tells a reviewer where it may be optimistic.", [
("Report template", bullets(["Scope: dataset path/version, date, code version and owner.","Inventory: counts by split, class, extension and readability.","Quality: image dimension distribution, decode failures, anomalous files and resolution policy.","Label: class mapping and count verification.","Similarity: SHA duplicate counts; pHash radius; group count; train/test overlap; label conflicts.","Split protocol: StratifiedGroupKFold folds, seed, group-isolation assertion.","Metrics: confusion matrix, recall, precision, PR AUC, F1/F2, balanced accuracy, workload and threshold.","Limitations: overlap caveat, sample size, generalization boundary and human-review policy."])),
("One-page reviewer explanation", "'We first checked that every image was readable and assigned only the documented binary label. We used SHA-256 for exact copies and pHash for visual similarity. Because related images can cause leakage, we built transitive perceptual groups and kept each group in one validation fold. We measured fraud recall, precision and review workload rather than relying on accuracy. The supplied test data has substantial visual overlap with train, so we disclose that its score may be optimistic.'")])

story += chapter("10. Operational checklist and incident playbook", "Use this before every retraining or demo evaluation.", [
("Before training", bullets(["Confirm no files changed since manifest generation.","Confirm train/test paths and label mapping.","Run readability and class-count audit.","Recompute or verify SHA/pHash using the recorded feature version.","Confirm group-fold overlap is zero.","Confirm no final test labels/predictions are used to tune threshold."])),
("If a suspicious result appears", table([["Observation","First response","Do not do"],["Very high accuracy, low fraud recall","inspect confusion matrix and imbalance","celebrate accuracy alone"],["Test score far above grouped CV","inspect overlap audit","call it production-ready"],["Cross-label near match","queue visual/label review","overwrite labels without evidence"],["Unreadable image","log and quarantine consistently","silently remove from one split"],["Feature length change","bump version/retrain","load an old artifact anyway"]],[4.4*cm,6.3*cm,5.7*cm])),
("Daily role cadence", "Morning: check new data and manifests. During development: review failed validations and data-contract changes. Before demo: reproduce the report from a clean run. After demo: archive metrics, limitations and questions raised.")])

story += chapter("11. Interview and judge readiness", "Answer in plain language first, then add the technical detail.", [
("Q: Why use pHash instead of only file names?", "File names are arbitrary. SHA finds exact byte copies; pHash catches visually related images after common changes such as resizing or compression."),
("Q: What does distance 6 mean?", "It is the maximum number of pHash bits allowed to differ for an image pair to be screened as close. It is a tuning choice, not a fraud rule; we record it and audit its effect."),
("Q: How did you prevent leakage?", "We clustered close pHashes transitively, then used StratifiedGroupKFold so an entire visual group stays in either fit or validation, never both."),
("Q: Is a close training/test match evidence of fraud?", "No. It is evidence that the evaluation may be easier than a fresh deployment scenario. We disclose it and use grouped validation for a stricter internal estimate."),
("Q: What would you do next?", "Add claim-level identifiers when ethically and legally available, label-audit ambiguous clusters, maintain a data-quality dashboard, and test on a genuinely time-separated, group-isolated holdout.")])

story += chapter("Appendix: 10-step practical lab", "Complete this lab without altering canonical data or model artifacts.", [
("Lab steps", table([["Step","Task","Evidence to save"],["1","Locate canonical dataset and copied role files","paths and date"],["2","Count train/test images by label","inventory table"],["3","Open 10 images per label","short visual notes"],["4","Extract forensic record for two images","width, hash, pHash, metadata"],["5","Compare two pHashes","Hamming distance and interpretation"],["6","Explain SHA versus pHash","one paragraph"],["7","Create perceptual groups","group count and largest group"],["8","Verify fold isolation","zero shared group IDs"],["9","Read overlap audit","rate, exact pHash count, caveat"],["10","Present validation report","3-minute explanation"]],[1.2*cm,8*cm,7.2*cm])),
("Completion standard", "You have mastered the role when you can reproduce these checks, explain why they matter to a non-technical stakeholder, identify a leakage risk, and refuse to make a model-performance claim without the matching data version and validation protocol.")])

story += [PageBreak(), P("Quick Reference", "Chapter"), table([["Concept","Remember"],["Target","Fraud = 1; Non-Fraud = 0"],["Training imbalance","200 fraud vs 5,000 non-fraud; use class-sensitive learning but preserve natural test ratio"],["Exact duplicate","same SHA-256"],["Near duplicate","close pHash, measured by Hamming distance"],["Leakage defense","transitive pHash groups + StratifiedGroupKFold"],["Current pHash screen","radius 6"],["Validation priority","recall, precision, PR AUC, workload, then accuracy"],["Ethical boundary","flag for human review; never automatic fraud verdict"]],[5*cm,11.4*cm]),Spacer(1,0.5*cm),P("Project files to study", "H2x")]
story += bullets(["project_files/src/vericlaim/features.py - image decoding, features, hashes and forensic record.","project_files/src/vericlaim/validation.py - grouping, BK-tree similarity search and overlap audit.","project_files/src/vericlaim/train.py - baseline data discovery and evaluation flow.","project_files/tests/test_features.py and tests/test_validation.py - expected behavior.","project_files/docs/model_card.md and architecture.md - model scope, limits and system boundaries."])
story += [P("End of guide. Keep it with your data-quality report and use it as your speaking outline.","Callout")]

doc=SimpleDocTemplate(str(OUT), pagesize=A4, rightMargin=1.5*cm,leftMargin=1.5*cm,topMargin=1.5*cm,bottomMargin=1.8*cm,title="VeriClaim AI - Data Validation Engineer Complete Study Guide",author="VeriClaim AI Team")
doc.build(story,onFirstPage=footer,onLaterPages=footer)
print(OUT)
