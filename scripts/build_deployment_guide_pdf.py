"""Build the chapter-wise VeriClaim deployment study guide."""
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle, KeepTogether

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "output" / "pdf" / "VeriClaim_Deployment_Study_Guide.pdf"

def p(text, style): return Paragraph(text, style)
def bullets(items, styles):
    return [p("&bull; " + item, styles['Body']) for item in items]
def footer(canvas, doc):
    canvas.saveState(); canvas.setFont('Helvetica', 8); canvas.setFillColor(colors.HexColor('#61756d'))
    canvas.drawString(48, 26, 'VeriClaim AI - Deployment Study Guide | Hackathon prototype')
    canvas.drawRightString(A4[0]-48, 26, f'Page {doc.page}'); canvas.restoreState()

def chapter(num, title, purpose, sections, styles):
    flow=[p(f"CHAPTER {num}",styles['Eyebrow']),p(title,styles['H1']),p(purpose,styles['Lead']),Spacer(1,10)]
    for heading, body in sections:
        flow += [p(heading,styles['H2'])]
        if isinstance(body,list): flow += bullets(body,styles)
        else: flow += [p(body,styles['Body'])]
        flow += [Spacer(1,7)]
    flow.append(PageBreak()); return flow

def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Title2',parent=styles['Title'],fontName='Helvetica-Bold',fontSize=30,leading=36,textColor=colors.HexColor('#073d2c'),alignment=TA_CENTER,spaceAfter=15))
    styles.add(ParagraphStyle(name='Eyebrow',parent=styles['Normal'],fontName='Helvetica-Bold',fontSize=10,leading=13,textColor=colors.HexColor('#176b55'),spaceAfter=8))
    styles.add(ParagraphStyle(name='H1',parent=styles['Heading1'],fontName='Helvetica-Bold',fontSize=22,leading=27,textColor=colors.HexColor('#073d2c'),spaceAfter=8))
    styles.add(ParagraphStyle(name='H2',parent=styles['Heading2'],fontName='Helvetica-Bold',fontSize=14,leading=18,textColor=colors.HexColor('#176b55'),spaceBefore=8,spaceAfter=4))
    styles.add(ParagraphStyle(name='Lead',parent=styles['Normal'],fontSize=13,leading=19,textColor=colors.HexColor('#40574e'),spaceAfter=10))
    styles.add(ParagraphStyle(name='Body',parent=styles['Normal'],fontSize=10.3,leading=15,textColor=colors.HexColor('#182c25'),spaceAfter=4))
    doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=48,leftMargin=48,topMargin=50,bottomMargin=45)
    story=[Spacer(1,1.1*inch),p('VERICLAIM AI',styles['Eyebrow']),p('Deployment Study Guide',styles['Title2']),p('A chapter-wise guide to running, packaging, deploying and operating the vehicle-insurance fraud-triage prototype.',styles['Lead']),Spacer(1,18)]
    story += [p('Who this guide is for',styles['H2']),p('This guide is written for project members who need to explain the deployment part confidently to a mentor or reviewer. It distinguishes the local hackathon prototype from a production-grade insurer deployment.',styles['Body']),Spacer(1,12)]
    story += [p('Important status',styles['H2']),p('The Azure demo previously created for the project was intentionally stopped. The current reliable demonstration environment is the local server at <b>http://127.0.0.1:8080</b>. Do not claim that a public cloud website is currently live unless it is redeployed and verified.',styles['Body']),PageBreak()]
    story += chapter('1','Deployment in simple words','Deployment means making the trained model and its website usable outside a training notebook.',[
        ('The three pieces that must travel together',['The frontend: pages, forms, dashboards and Model Lab.','The backend: API routes, authentication, claim processing and model inference.','The model package: saved ensemble artifact, CNN backbone, calibration model, thresholds and metrics.']),
        ('A useful analogy','Training is like teaching an investigator how to recognize patterns. Deployment is giving that investigator a secure office, case files, rules, a phone line and a way to record decisions.')],styles)
    story += chapter('2','Current project architecture','VeriClaim is a single-service Python prototype that serves the website and API together.',[
        ('Current request flow','Browser -> Python HTTP server -> image validation -> feature extraction -> hybrid model -> calibrated score -> triage response -> SQLite persistence.'),
        ('Main technology choices',['Python standard-library ThreadingHTTPServer provides the local API and static website.','HTML, CSS and JavaScript provide customer, staff and Model Lab screens.','Joblib loads the trained hybrid model.','SQLite persists accounts, claims and one-time Claim Passport history.','Docker packages the same app for a container platform.']),
        ('Why this is good for a hackathon','One command starts the UI and API, the model runs without a GPU, and the demo is easy to reproduce on a laptop.')],styles)
    story += chapter('3','What is deployed with the model','A deployed model is more than a .pkl file.',[
        ('Required artifacts',['vericlaim_model.joblib / .pkl: Extra Trees, MLPs, CNN heads, stacker, calibrator and thresholds.','efficientnetv2b0_backbone.keras: pretrained CNN backbone used during inference and Grad-CAM.','model_metrics.json: reproducible reported metrics, threshold values and leakage audit.','Source modules: feature extraction, model inference, Evidence DNA and explainability.']),
        ('Why version matching matters','The trained artifact expects the same handcrafted feature order and preprocessing used at training. Changing feature extraction without retraining can silently produce wrong predictions.'),
        ('Practical check','Before deployment, load the model artifact, run one image inference, call /api/health, and compare the loaded model family and metric report to the intended release.')],styles)
    story += chapter('4','Local deployment: the current demo','Local deployment is the safest and most appropriate mode for mentor demonstration.',[
        ('How it runs',['Create/activate the project virtual environment.','Install requirements.','Set PYTHONPATH=src.','Run python server.py.','Open http://127.0.0.1:8080 in a browser.']),
        ('Configuration','VERICLAIM_HOST defaults to 127.0.0.1 and VERICLAIM_PORT defaults to 8080. For containers, the Dockerfile sets host to 0.0.0.0 so the platform can reach the service.'),
        ('What to test locally',['Homepage loads.','/api/health returns status ok.','Model Lab returns prediction, calibrated probability, operating band and Grad-CAM when available.','Customer/staff demo flows work.','A repeat claim token cannot be replayed.'])],styles)
    story += chapter('5','Backend deployment flow','The backend receives an upload, validates it and produces a human-review signal.',[
        ('Image path','Upload -> size/type check -> server-side decode -> feature extraction -> EfficientNet/MLP/Extra Trees inference -> stacker -> Platt calibration -> threshold band.'),
        ('Claim path','Authenticated user -> optional repeat-claim passport -> evidence validation -> historical Evidence DNA comparison -> score -> atomic SQLite save -> customer/staff notifications.'),
        ('Why server-side validation matters','Browser file extensions and MIME labels can be false. The server decodes the image itself and rejects unsupported or unsafe inputs.')],styles)
    story += chapter('6','Containerization with Docker','A Docker image packages the exact runtime needed by the application.',[
        ('What the Dockerfile does',['Starts from Python 3.13 slim.','Sets unbuffered logs and container host/port variables.','Installs Python requirements.','Copies the project and runs python server.py.']),
        ('Why containers help','The laptop, mentor machine and cloud platform run the same packaged environment. This reduces the classic “works on my machine” problem.'),
        ('Container commands','Build: docker build -t vericlaim-ai .  Run: docker run -p 8080:8080 vericlaim-ai. Then verify /api/health before showing the UI.')],styles)
    story += chapter('7','Azure deployment path','Azure Container Apps is the documented public-demo path; it is not currently live.',[
        ('Why Container Apps','It can run the Docker image as a public HTTPS service and can scale down when unused. It fits a temporary demo better than managing a full virtual machine.'),
        ('Pre-deployment steps',['Create/sign in to an Azure account.','Create a budget alert before provisioning.','Ensure only demo-safe accounts and claims are packaged.','Install Azure CLI and Docker if required.','Read docs/azure_free_tier_deployment.md and run scripts/deploy-azure-free.ps1.']),
        ('Post-deployment checks',['Open the HTTPS site.','Call /api/health.','Test Model Lab with a safe image.','Confirm the container listens on platform-provided port settings.','Review Cost Analysis and stop the app when not demonstrating.'])],styles)
    story += chapter('8','Free-tier reality and cost control','“Free tier” does not mean unlimited or permanently free.',[
        ('Cost controls',['Create a small Azure budget and alert before deployment.','Use scale-to-zero where platform policy permits.','Keep the service stopped when not demonstrating.','Avoid GPU cloud instances for the CPU-first prototype.','Do not upload real customer evidence to a demo cloud deployment.']),
        ('Status discipline','A stopped Azure app does not consume active compute in the same way as a running one, but account, registry, storage or network charges may still apply. Always inspect current billing in Azure rather than assuming.')],styles)
    story += chapter('9','Persistence and the database','The current prototype persists selected operational state in local SQLite.',[
        ('Persisted data',['Accounts and password hashes.','Claims, messages and decisions.','Claim Passport token history as token hashes.','Evidence manifests and Evidence DNA summaries.']),
        ('Atomic repeat-claim protection','A valid one-time passport is checked early, then consumed inside the same transaction that saves the claim. This prevents a repeated request from using the same token twice.'),
        ('Container limitation','Local container disk is not durable after container replacement. For a real deployment, use managed database storage and object storage with encryption and backups.')],styles)
    story += chapter('10','Security controls','Deployment is incomplete if the model is exposed without safety controls.',[
        ('Already demonstrated',['Role-separated customer and staff views.','Password hashing and HttpOnly local sessions.','Short-lived, account-and-policy-bound Claim Passport tokens.','Replay detection and token rotation.','Server-side file decoding and evidence validation.','Masked historical claim references for non-staff users.']),
        ('Production upgrades',['HTTPS enforced end-to-end.','Managed identity provider and MFA.','Secret manager rather than source-controlled secrets.','Encrypted managed database and object storage.','Rate limiting, WAF/API gateway and centralized audit logs.'])],styles)
    story += chapter('11','Model serving and performance','The deployed service is CPU-first by design.',[
        ('Why CPU-first','The saved hybrid can serve the hackathon demo without TensorFlow, PyTorch, a GPU or a cloud account for its main prediction path. This keeps cost and complexity low.'),
        ('Performance considerations',['Image decode and handcrafted features add latency.','Evidence DNA matching grows as historical claims grow.','Grad-CAM is optional and can be slower than regular prediction.','Large file uploads should be limited and processed asynchronously in production.']),
        ('Production pattern','API gateway -> upload/object storage -> validation worker -> model service -> evidence search -> claims workflow -> monitoring.')],styles)
    story += chapter('12','Monitoring and MLOps','A deployed ML system must be observed after release.',[
        ('Operational monitoring',['Health endpoint uptime.','Latency and error rate.','Upload rejection reasons.','Database and storage usage.','Token replay attempts.']),
        ('Model monitoring',['Fraud recall and precision after adjudicated labels arrive.','Probability calibration/Brier score.','False-positive review workload.','Evidence-quality mix and image-size drift.','Reviewer overrides and subgroup differences.']),
        ('Release rule','Do not promote a candidate model because accuracy alone rises. Compare grouped out-of-fold PR-AUC, recall, calibration and workload first.')],styles)
    story += chapter('13','Release, rollback and model governance','Every model release must be traceable and reversible.',[
        ('Release checklist',['Freeze model artifact and metrics report together.','Record data version, code version, thresholds and validation protocol.','Run smoke tests before deployment.','Deploy in shadow/review-only mode first.','Document owner approval for threshold changes.']),
        ('Rollback','Keep the prior verified artifact. If health checks fail, probabilities drift or false alerts rise unexpectedly, route traffic back to the earlier artifact and investigate before retrying.'),
        ('Governance rule','The model supports triage only. It must not automatically approve, reject, cancel, price, accuse or refer a claim for legal action.')],styles)
    story += chapter('14','How to explain deployment to a mentor','Use this short explanation during review.',[
        ('Suggested answer','“We deploy VeriClaim as a CPU-first Python web service. The frontend and API are served together for the hackathon demo. The container packages the same model artifact, preprocessing code, calibration logic and UI, so deployment does not change the prediction pipeline. SQLite persists prototype accounts, claims and token history. For cloud demonstration we prepared Azure Container Apps with cost controls, but the public app is currently stopped. A production rollout would separate object storage, managed database, model service, evidence search and monitoring.”'),
        ('Do not say',['“The AI automatically rejects fraud claims.”','“The free cloud service has no cost risk.”','“The deployed test accuracy proves production performance.”','“Evidence DNA proves fraud.”'])],styles)
    story += chapter('15','Deployment readiness checklist','Use this final checklist before any mentor demo or cloud redeployment.',[
        ('Before starting',['Correct virtual environment active.','Model artifact and backbone present.','SQLite store reachable.','Port 8080 free.','No real customer data in demo records.']),
        ('Before presenting',['Open local URL and /api/health.','Run one Model Lab image test.','Show one customer claim flow and staff alert flow.','Explain thresholds and human review.','Keep a screenshot/PDF of verified metrics.']),
        ('Before cloud deployment',['Azure budget alert created.','Secrets and demo data reviewed.','HTTPS URL verified.','Health endpoint verified.','Stop service after demonstration if it is not needed.'])],styles)
    story[-1]=story[-1] if story[-1].__class__.__name__!='PageBreak' else story.pop()
    doc.build(story,onFirstPage=footer,onLaterPages=footer)
    print(OUT)

if __name__=='__main__': main()
