"""Generate the VeriClaim AI frontend developer study guide PDF."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table,
    TableStyle,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "pdf" / "VeriClaim_AI_Frontend_Developer_Master_Guide.pdf"


def p(text: str, style):
    return Paragraph(text, style)


def bullet(items, styles):
    return [p(f"<b>{item.split(':', 1)[0]}:</b>{item.split(':', 1)[1]}" if ':' in item else item, styles["BulletX"]) for item in items]


def code(text: str, styles):
    return Table([[p(text.replace("\n", "<br/>"), styles["CodeX"])]], colWidths=[17.0 * cm], style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#10251e")),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#34584a")),
        ("LEFTPADDING", (0, 0), (-1, -1), 10), ("RIGHTPADDING", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 8), ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))


def flow(labels, styles):
    cells = [[p(label, styles["Flow"]) for label in labels]]
    widths = [17.0 * cm / len(labels)] * len(labels)
    return Table(cells, colWidths=widths, style=TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#e9f3ec")),
        ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#83a996")),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#83a996")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 10), ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleX", parent=styles["Title"], fontName="Helvetica-Bold", fontSize=29, leading=34, textColor=colors.HexColor("#073d2c"), spaceAfter=14))
    styles.add(ParagraphStyle(name="Subtitle", parent=styles["BodyText"], fontSize=13, leading=20, textColor=colors.HexColor("#426457"), spaceAfter=16))
    styles.add(ParagraphStyle(name="H1X", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=20, leading=25, textColor=colors.HexColor("#073d2c"), spaceBefore=6, spaceAfter=12))
    styles.add(ParagraphStyle(name="H2X", parent=styles["Heading2"], fontName="Helvetica-Bold", fontSize=13, leading=17, textColor=colors.HexColor("#0d6548"), spaceBefore=10, spaceAfter=6))
    styles.add(ParagraphStyle(name="BodyX", parent=styles["BodyText"], fontSize=10.2, leading=15, spaceAfter=7, textColor=colors.HexColor("#20362d")))
    styles.add(ParagraphStyle(name="BulletX", parent=styles["BodyText"], leftIndent=14, firstLineIndent=-10, bulletIndent=2, fontSize=9.7, leading=14, spaceAfter=4, textColor=colors.HexColor("#20362d"), bulletText="-"))
    styles.add(ParagraphStyle(name="CodeX", fontName="Courier", fontSize=7.6, leading=10, textColor=colors.HexColor("#e8f4ec")))
    styles.add(ParagraphStyle(name="Flow", parent=styles["BodyText"], alignment=TA_CENTER, fontName="Helvetica-Bold", fontSize=8.6, leading=11, textColor=colors.HexColor("#073d2c")))
    styles.add(ParagraphStyle(name="Callout", parent=styles["BodyText"], backColor=colors.HexColor("#f3f8f4"), borderColor=colors.HexColor("#b5d5c0"), borderWidth=0.6, borderPadding=10, fontSize=9.8, leading=14, textColor=colors.HexColor("#1d4937"), spaceBefore=8, spaceAfter=10))

    def heading(number, title):
        return [p(f"CHAPTER {number}", styles["H2X"]), p(title, styles["H1X"])]

    story = []
    story += [Spacer(1, 2.2 * cm), p("VeriClaim AI", styles["H2X"]), p("Frontend Developer Master Guide", styles["TitleX"]), p("A project-specific study book for learning, understanding, extending and confidently presenting the VeriClaim customer portal, staff workspace and Model Lab.", styles["Subtitle"]), flow(["Public website", "Customer portal", "Staff workspace", "Model Lab"], styles), Spacer(1, .7 * cm), p("Who this guide is for", styles["H2X"]), p("A frontend developer with basic HTML, CSS and JavaScript knowledge who needs to master the exact interface already built in VeriClaim AI. It focuses on what the application does, why the UX choices matter in insurance fraud triage, how browser code connects to the backend, and how to improve it without breaking trust or security.", styles["BodyX"]), p("Outcome", styles["H2X"]), p("After completing the guide, you should be able to explain the interface to a judge, trace an uploaded image from browser to result card, add a new portal tab safely, test an API state, diagnose a UI bug, and propose a production-ready frontend architecture.", styles["Callout"]), PageBreak()]

    chapters = [
        ("1", "The product experience and your frontend mission", [
            ("The core problem", "Vehicle-claim customers need a clear way to submit evidence and follow a claim. Staff need a prioritised review workspace. The model is decision support, not a machine that rejects a claim."),
            ("Your frontend responsibility", "Make complex insurance and AI signals understandable without hiding uncertainty. A strong screen tells a user what they can do next, what the system knows, and what a human will decide."),
        ], ["Customer journey: visit site -> sign in -> file claim -> upload evidence -> track status -> message staff.", "Staff journey: sign in -> see queue -> inspect evidence signals -> verify documents -> record outcome.", "Model Lab journey: choose one image -> run local screening -> compare score with threshold -> understand evidence passport."]),
        ("2", "Project map: where the frontend lives", [
            ("Static application", "app/static/index.html contains the screen shells; styles.css contains visual rules and responsive layout; app.js owns state, rendering and browser events."),
            ("Backend contract", "server.py serves static files and exposes JSON endpoints. The frontend should not calculate fraud itself; it displays the backend response faithfully."),
        ], ["index.html: semantic page sections, navigation, portal containers, forms and Model Lab placeholders.", "styles.css: design tokens, components, mobile media rules, status colours and layout grids.", "app.js: state object, fetch helper, view routing, form logic and HTML rendering functions.", "server.py: authentication, case APIs, model-test APIs, file validation and report downloads."]),
        ("3", "How the single-page interface works", [
            ("No framework does not mean no architecture", "VeriClaim uses plain browser JavaScript. It behaves like a small single-page application: the document contains view containers, and JavaScript decides which view is active and what content is rendered."),
            ("The state object", "At the start of app.js, state stores the signed-in user, portal data, active tab, claim step, attached files and selected claim. Rendering should derive from state rather than leaving old screen content around."),
        ], ["showView(name): toggles public, auth, portal and Model Lab views and updates the URL hash.", "restoreSession(): requests /api/session on load, then restores navigation state.", "renderPortalShell(): builds different customer or staff navigation from the user role.", "renderPortal(): selects the appropriate tab renderer from state.tab."]),
        ("4", "UI composition: public pages, portals and role-based navigation", [
            ("Public experience", "The homepage explains benefits before asking for a login. Claims, policies, contact and FAQs reduce friction for a first-time visitor."),
            ("Role separation", "Customer and staff experiences share a visual language but not the same permissions or navigation. The server is authoritative; hiding a staff button is never security by itself."),
        ], ["Customer tabs include overview, policies, claims, new claim, trust, messages, notifications and support.", "Staff tabs include overview, claims, fraud queue, verification, analytics, messages and notifications.", "Use status colours consistently: active/green, low/green, medium/amber and high/red. Never use red alone: include text labels."]),
        ("5", "Claim filing: build the most important workflow carefully", [
            ("Three-step form", "The claim form collects claim details, evidence, then declaration/review. claimStep in state decides which section is visible."),
            ("Optional incident type", "Collision, parked damage and weather damage are optional because the supplied test data does not have reliable labels for those categories. The UI must never imply that the model uses the selection as a fraud feature."),
        ], ["Step 1: policy, incident date, optional incident type, amount, location and description.", "Step 2: photos, PDFs and videos. At least one supported damage image is required for AI screening.", "Step 3: review the data and require a truthful declaration before submission.", "Auto-save: debounce form input, then POST the draft to /api/drafts. Avoid sending a request on every keystroke."]),
        ("6", "Uploads, browser previews and safe evidence UX", [
            ("Client checks are usability checks", "The frontend checks allowed MIME types, count and 10 MB image size early. The backend repeats validation because browser checks can be bypassed."),
            ("Preview lifecycle", "URL.createObjectURL gives a local preview. Revoke the previous object URL when selecting another Model Lab file so memory is not leaked."),
        ], ["Show the filename, file size and remove control after selection.", "Explain accepted formats before upload; do not reveal a model error after the user has filled a long form.", "Use accessible labels for file input and meaningful alt text for previews.", "Never promise files are secure solely because they were selected in the browser; security is an end-to-end system property."]),
        ("7", "Calling APIs and handling asynchronous states", [
            ("The api helper", "api(path, options) wraps fetch, sends JSON headers, parses the response and turns non-200 responses into a readable error. Reuse it instead of repeating fetch boilerplate."),
            ("States a polished UI needs", "Every request has at least loading, success, empty and error states. Disable the submit button while a request is running to prevent duplicate claims."),
        ], ["GET /api/session: restore login state.", "POST /api/auth/login and /api/auth/signup: establish the current user.", "GET /api/portal: load role-scoped dashboard data.", "POST /api/drafts: persist the form draft.", "POST /api/analyze: submit a full claim for triage.", "POST /api/model-test: run a no-claim Model Lab image test."]),
        ("8", "Model Lab: presenting AI output responsibly", [
            ("What it is", "Model Lab is a separate demo/testing space. It uploads one image, sends it to /api/model-test, and displays the current hybrid-model result plus a previous-model comparison."),
            ("What it must not do", "It must not claim that an image proves a customer committed fraud. A positive result means the image meets a review threshold and should be investigated by a human."),
        ], ["Display the prediction label, calibrated probability and the active classification threshold.", "Show evidence signals: EfficientNet CNN score, evidence quality, fraud archive similarity, legitimate archive similarity, focus and image size.", "Use the disclaimer provided by the backend rather than writing a stronger claim in the UI.", "Explain probability versus threshold: a threshold changes workload and missed-fraud trade-offs; it does not retrain the model."]),
        ("9", "Evidence Passport and explainable trust design", [
            ("Why it is distinctive", "Most demos stop at Fraud / Non-Fraud. VeriClaim adds a Claim DNA Passport: coverage, view diversity, image quality, integrity and archive similarity presented as investigation aids."),
            ("Separation is fairness", "Evidence weakness, legitimate-reference similarity and fraud signals should remain visually separate. Low-quality evidence is not proof of fraud."),
        ], ["Twin Radar: compare labelled fraud archive, legitimate archive and within-claim image similarity.", "Evidence Quality Coach: give constructive next actions, such as upload a wider vehicle view or a sharper photo.", "Human decision guarantee: repeat this in claim submission, Model Lab and staff decision screens."]),
        ("10", "Accessibility, responsive design and secure rendering", [
            ("Accessibility", "Use labels, heading hierarchy, keyboard-reachable controls, visible focus states and text alongside colour. A claims app must remain useful on mobile, where many accident photos are uploaded."),
            ("Safe rendering", "app.js uses esc(...) before inserting user-provided text into template strings. Keep doing this. Directly inserting untrusted text with innerHTML creates XSS risk."),
        ], ["Test at narrow mobile widths and at desktop widths.", "Keep touch targets large enough for mobile use.", "Use semantic buttons for actions and anchors for navigation/downloads.", "Do not store secrets, passwords, model files or API keys in app.js or index.html.", "Server-side authorization remains mandatory for staff routes."]),
        ("11", "Testing and debugging like the owner of the experience", [
            ("Manual test matrix", "Test a signed-out visitor, new customer, existing customer, staff member, valid image, unsupported file, API failure and slow connection."),
            ("Browser tools", "Use DevTools Elements for layout, Console for errors, Network for request/response validation, Application for cookies, and device emulation for responsive checks."),
        ], ["After UI changes, run the server and test the exact flow you changed.", "Verify /api/model-test does not create a claim.", "Verify a staff user can see the queue but a customer cannot access staff actions.", "Test an error response deliberately and ensure the user sees a recovery action, not a blank panel.", "When changing response fields, update server and app.js together, then test both roles."]),
        ("12", "How to extend the frontend without breaking the product", [
            ("Safe extension recipe", "Define the user problem, write the response contract, add a small state field, build a renderer, bind events, define loading/error states, test role permissions, then update the demo narrative."),
            ("High-value next features", "Replace in-memory prototype data with a persistent API, add real notification preference controls, add document preview/virus-scan statuses, and make the Grad-CAM map available only with clear caveats."),
        ], ["Do not add a feature simply because it looks impressive. It must answer a customer or investigator need.", "Keep the model result component separate from business decision controls.", "For production, move from manual DOM strings toward component-based TypeScript (React or Vue) only when the team needs the maintainability benefit.", "Before a demo, rehearse the human-in-the-loop statement and the limitation of image-only labels."]),
    ]

    for number, title, prose, points in chapters:
        story += heading(number, title)
        for subheading, body in prose:
            story += [p(subheading, styles["H2X"]), p(body, styles["BodyX"])]
        story += bullet(points, styles)
        if number == "3":
            story += [Spacer(1, 5), flow(["state", "render function", "DOM update", "event", "API response", "new state"], styles)]
        if number == "7":
            story += [Spacer(1, 5), code("const data = await api('/api/model-test', {<br/>  method: 'POST',<br/>  body: JSON.stringify({ name: file.name, data_url: await fileDataUrl(file) })<br/>});", styles)]
        if number == "8":
            story += [Spacer(1, 5), flow(["Upload image", "POST /api/model-test", "Result + threshold", "Evidence Passport", "Human review"], styles)]
        story += [PageBreak()]

    story += heading("13", "Frontend learning plan, reviewer answers and final checklist")
    story += [p("Four-week mastery plan", styles["H2X"])]
    table_data = [[p("Week", styles["Flow"]), p("Focus", styles["Flow"]), p("Evidence of mastery", styles["Flow"])] ]
    for row in [("1", "HTML, CSS and screen map", "Explain every public view and portal tab."), ("2", "State, API helper and auth", "Trace login through portal load."), ("3", "Claim form and Model Lab", "Add a controlled field and test its failure state."), ("4", "Accessibility, testing and pitch", "Demo both roles and defend human-in-the-loop design.")]:
        table_data.append([p(cell, styles["BodyX"]) for cell in row])
    story += [Table(table_data, colWidths=[1.4 * cm, 6.0 * cm, 9.6 * cm], style=TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#dceee1")), ("GRID", (0,0), (-1,-1), .4, colors.HexColor("#a9c7b3")), ("VALIGN", (0,0), (-1,-1), "TOP"), ("LEFTPADDING", (0,0), (-1,-1), 7), ("RIGHTPADDING", (0,0), (-1,-1), 7), ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)])), p("Questions a judge may ask", styles["H2X"])]
    story += bullet(["Why is incident type optional?: The data lacks reliable incident-type labels, so it is collected for human context, not treated as a model feature.", "Why show Fraud / Not Fraud?: It is a Model Lab classification label at a selected threshold; the operational product routes cases for human review.", "What happens when the API fails?: The UI catches the error, restores interactive controls and shows a readable message rather than silently changing claim state.", "How do you protect a customer?: The frontend clearly separates AI signals from final staff decisions and never offers automatic denial.", "Why not use a frontend framework?: This hackathon prototype uses focused vanilla JavaScript to remain portable and transparent. A larger production team could migrate incrementally to TypeScript components."], styles)
    story += [p("Release checklist", styles["H2X"]), p("Confirm responsive layout, test both roles, test valid and invalid uploads, verify no unescaped user text enters innerHTML, verify API error messages, ensure every AI result carries a human-review caveat, and capture screenshots for the pitch.", styles["Callout"])]

    def page(canvas, doc):
        canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#b8d6c2")); canvas.line(1.8*cm, 1.6*cm, 19.2*cm, 1.6*cm)
        canvas.setFont("Helvetica", 8); canvas.setFillColor(colors.HexColor("#426457")); canvas.drawString(1.8*cm, 1.15*cm, "VeriClaim AI - Frontend Developer Master Guide")
        canvas.drawRightString(19.2*cm, 1.15*cm, f"Page {doc.page}"); canvas.restoreState()

    SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=1.8*cm, leftMargin=1.8*cm, topMargin=1.7*cm, bottomMargin=2.1*cm, title="VeriClaim AI Frontend Developer Master Guide").build(story, onFirstPage=page, onLaterPages=page)
    print(OUTPUT)


if __name__ == "__main__":
    build()
