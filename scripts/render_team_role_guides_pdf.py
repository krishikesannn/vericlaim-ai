"""Render every chapter-based team study guide as a polished PDF."""
from __future__ import annotations

import html
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer


ROOT = Path(__file__).resolve().parents[1]
PACKETS = ROOT / "Team_Role_Packets"
NAVY, TEAL, MINT, PALE, INK, MUTED = [colors.HexColor(value) for value in ("#102A43", "#087E8B", "#DFF4F0", "#F5F8FA", "#172B4D", "#52616B")]


class LearningFlow(Flowable):
    def __init__(self):
        super().__init__(); self.width = 17 * cm; self.height = 3.5 * cm
    def draw(self):
        canvas = self.canv; canvas.setFillColor(PALE); canvas.roundRect(0, 0, self.width, self.height, 10, fill=1, stroke=0)
        labels = ["Read\nconcept", "Inspect\nproject file", "Run a\nsmall test", "Explain it\nplainly", "Record\nrisk + next step"]
        width = 2.7 * cm; gap = .55 * cm
        for index, label in enumerate(labels):
            x = .4 * cm + index * (width + gap)
            canvas.setFillColor(MINT); canvas.setStrokeColor(TEAL); canvas.roundRect(x, 1.45 * cm, width, .95 * cm, 7, fill=1, stroke=1)
            canvas.setFillColor(NAVY); canvas.setFont("Helvetica-Bold", 6.8)
            for row, text in enumerate(label.split("\n")): canvas.drawCentredString(x + width / 2, 1.98 * cm - row * .24 * cm, text)
            if index < len(labels) - 1:
                canvas.setStrokeColor(TEAL); canvas.line(x + width, 1.92 * cm, x + width + gap, 1.92 * cm)
                canvas.setFillColor(TEAL); canvas.circle(x + width + gap, 1.92 * cm, 2, fill=1, stroke=0)
        canvas.setFillColor(MUTED); canvas.setFont("Helvetica-Oblique", 7)
        canvas.drawCentredString(self.width / 2, .48 * cm, "Use every chapter as a practical learning loop, not only as reading material.")


def header_footer(canvas, doc):
    canvas.saveState()
    if doc.page > 1:
        canvas.setStrokeColor(colors.HexColor("#D7E2E8")); canvas.line(1.7*cm, 28.2*cm, 19.3*cm, 28.2*cm); canvas.line(1.7*cm, 1.45*cm, 19.3*cm, 1.45*cm)
        canvas.setFillColor(MUTED); canvas.setFont("Helvetica", 8)
        canvas.drawString(1.7*cm, 28.45*cm, "VERICLAIM AI - TEAM ROLE STUDY GUIDE")
        canvas.drawRightString(19.3*cm, 1.15*cm, f"Page {doc.page}")
    canvas.restoreState()


def inline_markdown(text: str) -> str:
    safe = html.escape(text)
    while "**" in safe:
        start = safe.find("**"); end = safe.find("**", start + 2)
        if end == -1: break
        safe = safe[:start] + "<b>" + safe[start+2:end] + "</b>" + safe[end+2:]
    safe = safe.replace("`", "")
    return safe


def render_guide(markdown: Path) -> Path:
    packet = markdown.parent
    output = packet / "STUDY_GUIDE.pdf"
    styles = getSampleStyleSheet()
    title = ParagraphStyle("title", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=25, leading=31, textColor=NAVY, alignment=TA_CENTER, spaceAfter=10)
    subtitle = ParagraphStyle("sub", parent=styles["Normal"], fontName="Helvetica", fontSize=11, leading=16, textColor=MUTED, alignment=TA_CENTER)
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=17, leading=22, textColor=NAVY, spaceBefore=12, spaceAfter=7)
    h2 = ParagraphStyle("h2", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=12.2, leading=16, textColor=TEAL, spaceBefore=9, spaceAfter=5)
    h3 = ParagraphStyle("h3", parent=styles["Heading3"], fontName="Helvetica-Bold", fontSize=10.2, leading=13, textColor=INK, spaceBefore=6, spaceAfter=3)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontName="Helvetica", fontSize=9.2, leading=13.3, textColor=INK, spaceAfter=5)
    bullet = ParagraphStyle("bullet", parent=body, leftIndent=15, firstLineIndent=-10, bulletIndent=2, spaceAfter=2)
    story = []
    lines = markdown.read_text(encoding="utf-8").splitlines()
    first_title = next((line[2:] for line in lines if line.startswith("# ")), packet.name.replace("_", " ").title())
    story += [Spacer(1, 2.8*cm), Paragraph("VERICLAIM AI", ParagraphStyle("k", parent=subtitle, fontName="Helvetica-Bold", textColor=TEAL)), Spacer(1, .15*cm), Paragraph(inline_markdown(first_title), title), Paragraph("Chapter-based learning packet with project-specific code, practical tasks and reviewer preparation", subtitle), Spacer(1, .6*cm), LearningFlow(), Spacer(1, .25*cm)]
    for line in lines:
        if not line.strip(): continue
        if line.startswith("# "): continue
        if line.startswith("## "): story.append(Paragraph(inline_markdown(line[3:]), h1))
        elif line.startswith("### "): story.append(Paragraph(inline_markdown(line[4:]), h3))
        elif line.startswith("- "): story.append(Paragraph(inline_markdown(line[2:]), bullet, bulletText="-"))
        else: story.append(Paragraph(inline_markdown(line), body))
    doc = SimpleDocTemplate(str(output), pagesize=A4, leftMargin=1.7*cm, rightMargin=1.7*cm, topMargin=2.15*cm, bottomMargin=1.8*cm, title=first_title, author="VeriClaim AI Hackathon Team")
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    return output


def main():
    outputs = [render_guide(path) for path in sorted(PACKETS.glob("*/STUDY_GUIDE.md"))]
    for output in outputs: print(output)


if __name__ == "__main__": main()
