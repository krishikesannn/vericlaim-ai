from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, PageBreak,
                                Table, TableStyle, KeepTogether, Flowable)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "VeriClaim_AI_Developer_Study_Guide.pdf"

NAVY = colors.HexColor("#102A43")
TEAL = colors.HexColor("#087E8B")
MINT = colors.HexColor("#DFF4F0")
LIME = colors.HexColor("#B9E769")
INK = colors.HexColor("#172B4D")
MUTED = colors.HexColor("#52616B")
PALE = colors.HexColor("#F5F8FA")
RED = colors.HexColor("#C94C4C")


def para(text, style, **kwargs):
    return Paragraph(text, style, **kwargs)


class ArchitectureDiagram(Flowable):
    def __init__(self):
        super().__init__()
        self.width, self.height = 17 * cm, 8.1 * cm

    def _box(self, c, x, y, w, h, title, subtitle, fill):
        c.setFillColor(fill); c.setStrokeColor(TEAL); c.roundRect(x, y, w, h, 8, fill=1, stroke=1)
        c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 8); c.drawCentredString(x + w / 2, y + h - 14, title)
        c.setFillColor(MUTED); c.setFont("Helvetica", 6.5)
        for i, line in enumerate(subtitle.split("\n")):
            c.drawCentredString(x + w / 2, y + h - 27 - i * 8, line)

    def _arrow(self, c, x1, y1, x2, y2):
        c.setStrokeColor(TEAL); c.setLineWidth(1.2); c.line(x1, y1, x2, y2)
        c.setFillColor(TEAL); c.circle(x2, y2, 2.2, fill=1, stroke=0)

    def draw(self):
        c = self.canv
        c.setFillColor(PALE); c.roundRect(0, 0, self.width, self.height, 12, fill=1, stroke=0)
        self._box(c, 9, 190, 113, 45, "CLAIM IMAGE", "photo plus optional\ndamage context", MINT)
        self._box(c, 9, 105, 113, 54, "EFFICIENTNETV2B0", "CNN turns pixels into a\n1,280-number visual summary", colors.white)
        self._box(c, 9, 22, 113, 52, "FRAUD ARCHIVE", "pHash similarity checks\nfor close visual matches", colors.white)
        self._box(c, 183, 174, 115, 54, "MLP ENSEMBLE", "small neural networks\nread the visual summary", colors.white)
        self._box(c, 183, 98, 115, 54, "EXTRA TREES", "many decision trees with\nrotating normal-photo groups", colors.white)
        self._box(c, 183, 22, 115, 52, "FUSION + CALIBRATION", "combines evidence into a\nprobability and threshold", MINT)
        self._box(c, 359, 98, 113, 54, "HUMAN TRIAGE", "Fraud / non-fraud /\nreview recommendation", colors.HexColor("#F9F1DA"))
        self._arrow(c, 65, 190, 65, 159); self._arrow(c, 65, 105, 65, 74)
        self._arrow(c, 122, 132, 183, 201); self._arrow(c, 122, 132, 183, 125)
        self._arrow(c, 122, 48, 183, 48); self._arrow(c, 240, 174, 240, 152); self._arrow(c, 240, 98, 240, 74)
        self._arrow(c, 298, 48, 359, 125)
        c.setFillColor(MUTED); c.setFont("Helvetica-Oblique", 7)
        c.drawString(10, 5, "The model prioritizes a claim for review; an investigator makes the decision.")


class BalanceDiagram(Flowable):
    def __init__(self):
        super().__init__(); self.width, self.height = 17 * cm, 6.6 * cm

    def draw(self):
        c = self.canv
        c.setFillColor(PALE); c.roundRect(0, 0, self.width, self.height, 12, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 9); c.setFillColor(NAVY); c.drawString(14, 162, "The data starts highly imbalanced")
        c.setFont("Helvetica", 7); c.setFillColor(MUTED); c.drawString(14, 149, "Training data: 200 fraud photos and 5,000 non-fraud photos")
        for i in range(25):
            c.setFillColor(colors.HexColor("#B7D9F6")); c.roundRect(14 + (i % 13) * 20, 115 - (i // 13) * 18, 14, 11, 2, fill=1, stroke=0)
        c.setFillColor(RED); c.roundRect(14, 92, 14, 11, 2, fill=1, stroke=0)
        c.setFillColor(MUTED); c.setFont("Helvetica", 7); c.drawString(34, 95, "Fraud is rare: roughly 1 photo out of every 26")
        c.setFont("Helvetica-Bold", 9); c.setFillColor(NAVY); c.drawString(270, 162, "Training makes fraud mistakes count more")
        c.setFillColor(RED); c.roundRect(270, 115, 70, 28, 5, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 8); c.drawCentredString(305, 127, "Fraud x25")
        c.setFillColor(colors.HexColor("#B7D9F6")); c.roundRect(354, 115, 70, 28, 5, fill=1, stroke=0)
        c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 8); c.drawCentredString(389, 127, "Normal x1")
        c.setFillColor(MUTED); c.setFont("Helvetica", 7); c.drawString(270, 96, "Class weighting prevents the easy 'always normal' shortcut.")
        c.setFont("Helvetica-Bold", 9); c.setFillColor(NAVY); c.drawString(14, 60, "Rotating balanced Extra Trees")
        c.setFont("Helvetica", 7); c.setFillColor(MUTED); c.drawString(14, 47, "Each small learner sees every fraud photo plus a different 1:8 slice of normal photos.")
        for i, label in enumerate(["Fraud + normal group A", "Fraud + normal group B", "...", "Fraud + normal group T"]):
            x = 14 + i * 116
            c.setFillColor(MINT if i != 2 else colors.white); c.setStrokeColor(TEAL); c.roundRect(x, 17, 100, 20, 5, fill=1, stroke=1)
            c.setFillColor(NAVY); c.setFont("Helvetica", 6.5); c.drawCentredString(x + 50, 25, label)


class ReviewDiagram(Flowable):
    def __init__(self):
        super().__init__(); self.width, self.height = 17 * cm, 4.3 * cm

    def draw(self):
        c = self.canv
        c.setFillColor(PALE); c.roundRect(0, 0, self.width, self.height, 12, fill=1, stroke=0)
        boxes = [(14, "Upload claim"), (135, "AI evidence\nassessment"), (256, "Route by\nconfidence"), (377, "Investigator\ndecision")]
        for x, label in boxes:
            c.setFillColor(MINT); c.setStrokeColor(TEAL); c.roundRect(x, 40, 95, 34, 6, fill=1, stroke=1)
            c.setFillColor(NAVY); c.setFont("Helvetica-Bold", 7.5)
            for i, line in enumerate(label.split("\n")):
                c.drawCentredString(x + 47, 60 - i * 9, line)
        c.setStrokeColor(TEAL); c.setLineWidth(1.3)
        for x in (109, 230, 351):
            c.line(x, 57, x + 26, 57); c.setFillColor(TEAL); c.circle(x + 26, 57, 2.1, fill=1, stroke=0)
        c.setFillColor(MUTED); c.setFont("Helvetica", 7); c.drawCentredString(self.width / 2, 15, "AI is a prioritization assistant, not an automatic claim rejection engine.")


def header_footer(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#D7E2E8")); canvas.line(1.7*cm, 28.2*cm, 19.3*cm, 28.2*cm)
        canvas.setFillColor(MUTED); canvas.setFont("Helvetica", 8)
        canvas.drawString(1.7*cm, 28.45*cm, "VERICLAIM AI - DEVELOPER STUDY GUIDE")
        canvas.drawRightString(19.3*cm, 1.15*cm, f"Page {doc.page}")
        canvas.line(1.7*cm, 1.45*cm, 19.3*cm, 1.45*cm)
    canvas.restoreState()


def build_pdf():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    title = ParagraphStyle("Title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=31, leading=37, textColor=NAVY, alignment=TA_CENTER, spaceAfter=14)
    subtitle = ParagraphStyle("Subtitle", parent=styles["Normal"], fontName="Helvetica", fontSize=13, leading=19, textColor=MUTED, alignment=TA_CENTER)
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=25, textColor=NAVY, spaceBefore=4, spaceAfter=10)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=TEAL, spaceBefore=12, spaceAfter=6)
    body = ParagraphStyle("Body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.4, leading=14, textColor=INK, spaceAfter=7)
    small = ParagraphStyle("Small", parent=body, fontSize=8, leading=11, textColor=MUTED)
    callout = ParagraphStyle("Callout", parent=body, backColor=MINT, borderColor=TEAL, borderWidth=.7, borderPadding=9, borderRadius=4, spaceBefore=5, spaceAfter=10)
    bullet = ParagraphStyle("Bullet", parent=body, leftIndent=14, firstLineIndent=-10, bulletIndent=2, spaceAfter=4)
    story = []
    # Cover
    story += [Spacer(1, 4.4*cm), para("VERICLAIM AI", ParagraphStyle("Kicker", parent=subtitle, fontName="Helvetica-Bold", fontSize=12, textColor=TEAL, spaceAfter=8)),
              para("Developer Study Guide", title), para("A plain-language handbook for image-based car-insurance fraud triage", subtitle), Spacer(1, .8*cm)]
    cover = Table([[para("<b>Hackathon prototype</b><br/>Build, understand, explain and improve the solution responsibly.", body),
                    para("<b>August 2026</b><br/>Source: supplied project dataset and local evaluation artifacts.", body)]], colWidths=[8.25*cm, 8.25*cm])
    cover.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,-1), MINT), ("BOX", (0,0), (-1,-1), .8, TEAL), ("INNERGRID", (0,0), (-1,-1), .4, colors.HexColor("#9DD5CE")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 12), ("RIGHTPADDING", (0,0), (-1,-1), 12), ("TOPPADDING", (0,0), (-1,-1), 12), ("BOTTOMPADDING", (0,0), (-1,-1), 12)]))
    story += [cover, Spacer(1, 1.0*cm), para("The essential idea", h2), para("A claim photograph becomes a set of visual measurements. Several models inspect those measurements, an archive checks for close visual similarities, and the final system recommends whether the claim should be prioritized for human review. It does not decide guilt or reject claims automatically.", body), PageBreak()]
    # contents
    story += [para("Contents", h1)]
    contents = ["1. The problem and scope", "2. Dataset, labels and imbalance", "3. Supervised learning in simple terms", "4. How imbalance is handled", "5. The deployed hybrid model", "6. How a photo becomes a result", "7. Metrics and model comparison", "8. Website workflow and standout features", "9. Code map and developer workflow", "10. Limitations, guardrails and future work", "11. Glossary and learning path"]
    for item in contents: story.append(para(item, bullet, bulletText="-"))
    story += [Spacer(1, .3*cm), para("Reading tip: read Chapters 1-6 first for the core story, then use Chapters 7-11 when preparing the demo, retraining, or presentation.", callout), PageBreak()]
    # Ch1
    story += [para("1. The problem and scope", h1), para("Insurance fraud review is difficult because suspicious claims are rare and visual evidence is ambiguous. A damaged tire, for example, is not automatically fraudulent. The system must learn patterns that were associated with fraud labels in the supplied training photos and use those patterns only to prioritize investigation.", body), para("What this project does", h2)]
    for t in ["Accepts a claim image with optional damage context.", "Produces a calibrated fraud-risk probability and a fraud/non-fraud triage label.", "Surfaces related evidence such as close visual archive matches.", "Keeps a human investigator in the decision loop."]:
        story.append(para(t, bullet, bulletText="-"))
    story += [para("What it does not do", h2), para("It cannot prove fraud from a single image. It should not be used as an automatic denial, a pricing decision, or a statement about a customer. The label reflects the supplied dataset, not a universal definition of suspicious damage.", callout)]
    # Ch2
    story += [para("2. Dataset, labels and imbalance", h1), para("The project uses only the supplied hackathon image dataset. No additional insurance or claim dataset was added. The learning task is binary classification: each training photo has a fraud or non-fraud label.", body)]
    dataset = [["Split", "Images", "Fraud", "Non-fraud", "Fraud rate"], ["Training", "5,200", "200", "5,000", "3.85%"], ["Supplied test", "1,416", "93", "1,323", "6.57%"]]
    tbl = Table([[para(str(x), small) for x in row] for row in dataset], colWidths=[3.1*cm, 2.4*cm, 2.4*cm, 3.1*cm, 2.5*cm])
    tbl.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), NAVY), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("BACKGROUND", (0,1), (-1,-1), PALE), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C7D5DB")), ("ALIGN", (1,0), (-1,-1), "CENTER"), ("VALIGN", (0,0), (-1,-1), "MIDDLE"), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7)]))
    story += [tbl, Spacer(1, .3*cm), para("Why accuracy alone is misleading", h2), para("If a model called every image non-fraud, it would be about 96% accurate on the training distribution, yet it would identify no fraud at all. That is why recall, precision, F-scores and PR AUC are used alongside accuracy.", body), PageBreak()]
    # Ch3
    story += [para("3. Supervised learning in simple terms", h1), para("This is supervised machine learning. During training, the model is shown a photograph and the known label that came with it. It repeatedly adjusts itself to make its prediction closer to the supplied answer.", body), para("A helpful analogy", h2), para("Imagine teaching a new investigator with a collection of previously reviewed cases. Each photo is a flashcard. On the front is the image; on the back is the dataset label. The learner finds visual clues that tend to appear with each label. It does not understand intent, accidents, or people in the way a human does.", callout), para("What the CNN learns", h2), para("Early neural-network layers detect simple edges, textures and colors. Deeper layers combine those into more useful visual patterns, such as damage areas, image composition and recurring photo characteristics. The exact learned features are distributed across many numbers rather than stored as a simple written rule.", body)]
    # Ch4
    story += [PageBreak(), para("4. How imbalance is handled", h1), para("The training data contains far fewer fraud photos. The solution does not invent new claim photos and does not permanently discard normal photos. It uses two complementary methods so the model cannot succeed merely by predicting 'normal' for everything.", body), BalanceDiagram(), Spacer(1, .25*cm), para("Method A - class weighting", h2), para("A missed fraud example is assigned about 25 times the training importance of a normal example in the MLP components. This is a cost-sensitive learning approach. It makes the learner pay attention when it misses the rare class.", body), para("Method B - rotating balanced ensemble", h2), para("Twenty Extra Trees learners each see every fraud photo and a different temporary 1:8 fraud-to-normal training subset. Their predictions are averaged. Across rotations, the system uses the available normal images without allowing any one learner to be overwhelmed by them.", body), para("Why not only use equal counts?", h2), para("Keeping equal fraud and normal counts would throw away most normal examples or make an unrealistic test set. Instead, the final evaluation preserves the original class balance while training adds appropriate emphasis to fraud. This produces a more honest view of likely review workload.", body), PageBreak()]
    # Ch5
    story += [para("5. The deployed hybrid model", h1), para("The deployed artifact is a calibrated EfficientNetV2B0 CNN + Extra Trees/MLP + fraud-archive similarity hybrid. Multiple evidence sources are intentionally combined: no single model is trusted as the whole answer.", body), ArchitectureDiagram(), Spacer(1, .25*cm)]
    comps = [["Component", "Role in the system"], ["EfficientNetV2B0 CNN", "Pretrained ImageNet backbone creates a 1,280-number visual embedding. No external insurance data was used."], ["MLP ensemble", "Five small neural networks estimate fraud likelihood from the visual embedding."], ["Extra Trees ensemble", "Tree-based learners capture non-linear feature combinations; includes full and rotating balanced learners."], ["Archive similarity", "Perceptual hashing checks whether the photo is visually close to archived fraud evidence."], ["Fusion and calibration", "A final logistic model combines evidence; Platt calibration makes its probability easier to interpret."]]
    ct = Table([[para(c, small) for c in r] for r in comps], colWidths=[4*cm, 12*cm])
    ct.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), NAVY), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("BACKGROUND", (0,1), (-1,-1), PALE), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C7D5DB")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    story += [ct, PageBreak()]
    # Ch6
    story += [para("6. How a photo becomes a result", h1), para("At prediction time the same image preparation used in training is applied: the photo is read, resized to 224 x 224 pixels and converted into numeric pixels. The CNN turns it into a compact visual embedding. MLP and Extra Trees models score it, the archive adds similarity evidence, and the fusion layer produces one calibrated risk probability.", body), para("The threshold turns probability into a review label", h2), para("The chosen operating threshold is 0.0612. A probability at or above that value is shown as 'Fraud - review recommended'; below it is shown as 'Non-fraud - no fraud flag'. The low threshold is intentional: this hackathon model aims to miss fewer labelled fraud cases, accepting that some normal claims will be reviewed. Threshold selection is a business decision and can be changed based on investigator capacity.", callout), ReviewDiagram(), Spacer(1, .25*cm), para("Why two tire photos can receive different labels", h2), para("The system does not use a rule such as 'tire damage equals fraud'. It compares the complete visual pattern - texture, lighting, crop, damage appearance, background, angle and similarities learned from training labels. Two tire photos can therefore create different embeddings and different scores. This is also why the result needs a human review process and explanation features such as archive-match evidence.", body), PageBreak()]
    # Ch7
    story += [para("7. Metrics and model comparison", h1), para("Metrics below are from the supplied test split at the selected review threshold. They describe this hackathon evaluation split, not a production guarantee. The test set has close visual relationships with training images in a perceptual audit, so the results should be treated carefully.", body)]
    metrics = [["Metric", "Previous MLP hybrid", "Current EfficientNet hybrid"], ["Accuracy", "83.33%", "96.12%"], ["Balanced accuracy", "82.58%", "94.42%"], ["Precision", "25.76%", "64.18%"], ["Fraud recall", "81.72%", "92.47%"], ["F1 score", "39.18%", "75.77%"], ["F2 score", "56.97%", "84.98%"], ["ROC AUC", "0.9183", "0.9759"], ["PR AUC", "0.6438", "0.9048"]]
    mt = Table([[para(c, small) for c in r] for r in metrics], colWidths=[5.2*cm, 5.3*cm, 5.5*cm])
    mt.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), NAVY), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("BACKGROUND", (0,1), (-1,-1), PALE), ("BACKGROUND", (2,1), (2,-1), MINT), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C7D5DB")), ("ALIGN", (1,0), (-1,-1), "CENTER"), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    story += [mt, Spacer(1, .4*cm), para("Current confusion matrix", h2)]
    confusion_matrix = [["", "Predicted non-fraud", "Predicted fraud"], ["Actually non-fraud", "1,275 true negatives", "48 false positives"], ["Actually fraud", "7 false negatives", "86 true positives"]]
    cmt = Table([[para(c, small) for c in r] for r in confusion_matrix], colWidths=[4*cm, 6*cm, 6*cm])
    cmt.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), NAVY), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("BACKGROUND", (0,1), (0,-1), MINT), ("BACKGROUND", (1,1), (-1,-1), PALE), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C7D5DB")), ("ALIGN", (1,0), (-1,-1), "CENTER"), ("TOPPADDING", (0,0), (-1,-1), 8), ("BOTTOMPADDING", (0,0), (-1,-1), 8)]))
    story += [cmt, Spacer(1, .25*cm), para("Leakage caution", h2), para("The perceptual audit found that 53.7% of supplied test images were close visual matches to training images, including 261 identical perceptual hashes. This may inflate reported performance. A stronger future evaluation should group duplicate or near-duplicate vehicle/photo clusters before splitting data.", callout), PageBreak()]
    # Ch8
    story += [para("8. Website workflow and standout features", h1), para("The local website is designed as a demo operations portal, not merely a classification page. It includes a Model Lab for uploading an image and comparing the previous and current models.", body)]
    features = [["Feature", "Why it is valuable"], ["Model Lab comparison", "Shows prior and current models side by side so the improvement is visible and testable."], ["Claim DNA Passport", "Keeps a review-ready evidence record: photo, score, threshold, model version and rationale."], ["Twin Radar", "Uses archive similarity to show potentially related visual evidence, rather than hiding that signal."], ["Human-led governance", "Frames the model as triage support and retains investigator ownership of decisions."], ["Customer fraud protection", "Can help flag suspicious communication patterns and preserve an evidence trail for customers."], ["Integrity and reporting", "Supports evidence receipts, review workload insight and model-governance communication."]]
    ft = Table([[para(c, small) for c in r] for r in features], colWidths=[5*cm, 11*cm])
    ft.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), NAVY), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("BACKGROUND", (0,1), (-1,-1), PALE), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C7D5DB")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7)]))
    story += [ft, PageBreak()]
    # Ch9
    story += [para("9. Code map and developer workflow", h1), para("These are the key project files for a developer who wants to understand, reproduce or safely modify the solution.", body)]
    files = [["Path", "Purpose"], ["src/vericlaim/train_efficientnet_hybrid.py", "Trains the CNN-embedding hybrid, ensembles, archive signal, fusion model and calibration."], ["src/vericlaim/app.py", "Application routes and prediction integration for the local website."], ["models/efficientnet_hybrid/vericlaim_model.joblib", "Saved hybrid prediction artifact."], ["models/efficientnet_hybrid/efficientnetv2b0_backbone.keras", "Saved EfficientNetV2B0 CNN backbone."], ["docs/model_card.md", "Model purpose, intended use, metrics and limitations."], ["docs/architecture.md", "Architecture and implementation details."], ["docs/developer_study_guide.md", "Full editable source study guide for this PDF."]]
    ft2 = Table([[para(c, small) for c in r] for r in files], colWidths=[7.3*cm, 8.7*cm])
    ft2.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), NAVY), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("BACKGROUND", (0,1), (-1,-1), PALE), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C7D5DB")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
    story += [ft2, Spacer(1,.3*cm), para("Safe developer workflow", h2)]
    for t in ["Inspect class counts and duplicate risks before training.", "Keep all preprocessing inside the training/prediction pipeline so behavior matches.", "Use grouped or duplicate-aware validation when possible.", "Compare recall, precision, PR AUC and calibration - not accuracy alone.", "Save the threshold, model version and metrics with every trained artifact.", "Test uploads in Model Lab using known examples, then ask a reviewer to interpret results."]:
        story.append(para(t, bullet, bulletText="-"))
    story.append(PageBreak())
    # Ch10
    story += [para("10. Limitations, guardrails and future work", h1), para("A good hackathon system should be honest about what it cannot yet establish. The model can recognize dataset-associated patterns; it cannot infer customer intent or establish fraud as a fact.", body), para("Current limitations", h2)]
    for t in ["The labels and images are limited to the supplied dataset and may contain bias or noise.", "Near-duplicate relationships between training and test images may make the evaluation optimistic.", "There is no damage-location detector or Grad-CAM explanation map in the current artifact.", "Optional context fields should not be required when the test data does not provide them.", "Predictions on out-of-distribution photos, such as unrelated tire pictures, can be unreliable."]:
        story.append(para(t, bullet, bulletText="-"))
    story += [para("Future roadmap", h2)]
    roadmap = [["Phase", "Next contribution"], ["1 - Trust", "Add Grad-CAM and out-of-distribution warnings so reviewers can see where the model looked and when it is uncertain."], ["2 - Damage evidence", "Add damage localisation with a detector such as YOLO only after obtaining suitable labelled bounding-box data."], ["3 - Better generalisation", "Use carefully documented image augmentation and duplicate-aware grouped splits."], ["4 - Claim context", "Fuse lawful, available metadata with images only after privacy, consent and leakage checks."], ["5 - Production readiness", "Add authentication, audit logs, monitoring, drift alerts, a feedback loop and regular threshold review."]]
    rt = Table([[para(c, small) for c in r] for r in roadmap], colWidths=[4*cm, 12*cm])
    rt.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), NAVY), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("BACKGROUND", (0,1), (-1,-1), PALE), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C7D5DB")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 7), ("BOTTOMPADDING", (0,0), (-1,-1), 7)]))
    story += [rt, Spacer(1,.3*cm), para("Presentation-safe statement", callout), para("'VeriClaim AI is a human-led triage assistant. It uses image patterns, archive similarity and calibrated model evidence to prioritize claims for review. It does not automatically accuse customers or reject claims.'", body), PageBreak()]
    # Ch11
    story += [para("11. Glossary and learning path", h1)]
    glossary = [["Term", "Plain-language meaning"], ["CNN", "A neural network designed for images. It learns useful visual patterns from pixels."], ["EfficientNetV2B0", "The lightweight CNN backbone that produces the visual embedding."], ["Embedding", "A list of numbers summarising important visual information from an image."], ["MLP", "A small, general-purpose neural network that reads the embedding."], ["Extra Trees", "An ensemble of many randomized decision trees that vote together."], ["Class weighting", "Making errors on rare fraud examples count more during training."], ["Calibration", "Adjusting raw scores so probabilities better match observed frequencies."], ["Threshold", "The probability boundary that decides whether to flag a claim for review."], ["Recall", "Of all labelled fraud cases, the share the system flags."], ["Precision", "Of cases the system flags, the share labelled fraud in the test data."], ["PR AUC", "A score that summarizes precision/recall performance and is useful for rare classes."], ["Leakage", "Information that makes evaluation unrealistically easy, such as near-duplicate photos across train and test."]]
    gt = Table([[para(c, small) for c in r] for r in glossary], colWidths=[4.2*cm, 11.8*cm])
    gt.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), NAVY), ("TEXTCOLOR", (0,0), (-1,0), colors.white), ("BACKGROUND", (0,1), (-1,-1), PALE), ("GRID", (0,0), (-1,-1), .35, colors.HexColor("#C7D5DB")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("TOPPADDING", (0,0), (-1,-1), 5), ("BOTTOMPADDING", (0,0), (-1,-1), 5)]))
    story += [gt, Spacer(1,.25*cm), para("Suggested learning path", h2)]
    for t in ["Start with Chapters 1-4 to understand the problem, labels and imbalance.", "Study the architecture diagram in Chapter 5, then trace the code map in Chapter 9.", "Use Chapter 7 to explain performance honestly in a demo.", "Use Chapter 10 to answer questions about ethics, limitations and future improvements.", "Open the Model Lab and test known examples, remembering that individual predictions are triage signals, not proof."]:
        story.append(para(t, bullet, bulletText="-"))
    story += [Spacer(1, .5*cm), para("End of guide", ParagraphStyle("End", parent=subtitle, fontName="Helvetica-Bold", textColor=TEAL, fontSize=12))]
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=1.7*cm, leftMargin=1.7*cm, topMargin=2.15*cm, bottomMargin=1.8*cm, title="VeriClaim AI Developer Study Guide", author="VeriClaim AI Hackathon Team")
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(OUTPUT)


if __name__ == "__main__":
    build_pdf()
