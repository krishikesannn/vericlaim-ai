#!/usr/bin/env python3
"""Zero-framework HTTP server for the VeriClaim AI prototype."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import mimetypes
import os
import re
import secrets
import sqlite3
import sys
import threading
import textwrap
import uuid
from http.cookies import SimpleCookie
from datetime import datetime, timedelta, timezone
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

from vericlaim.model import VeriClaimModel  # noqa: E402
from vericlaim.explainability import efficientnet_attention_map  # noqa: E402
from vericlaim.evidence_matching import build_evidence_dna, find_historical_matches  # noqa: E402


STATIC_DIR = ROOT / "app" / "static"
ASSET_DIR = ROOT / "assets"
STATE_DIR = ROOT / "data"
STATE_DB = STATE_DIR / "vericlaim_state.sqlite3"
EVIDENCE_DIR = STATE_DIR / "claim_evidence"
MODEL_PATH = Path(os.environ.get("VERICLAIM_MODEL", ROOT / "models" / "efficientnet_hybrid" / "vericlaim_model.joblib"))
PREVIOUS_MODEL_PATH = ROOT / "models" / "neural_candidate" / "vericlaim_model.joblib"
MAX_IMAGES = 8
MAX_IMAGE_BYTES = 10 * 1024 * 1024
MODEL = VeriClaimModel.load(MODEL_PATH)
PREVIOUS_MODEL = VeriClaimModel.load(PREVIOUS_MODEL_PATH)
CASES: list[dict] = []
LOCK = threading.Lock()
USERS: dict[str, dict] = {}
SESSIONS: dict[str, str] = {}
DRAFTS: dict[str, dict] = {}
MESSAGES: list[dict] = []
NOTIFICATIONS: list[dict] = []
POLICIES = [
    {"policy_id": "POL-2026-0419", "type": "Comprehensive Motor", "vehicle": "2023 Hyundai Creta", "status": "Active", "renewal": "2027-04-19", "premium": 18400},
    {"policy_id": "POL-2025-1182", "type": "Zero Depreciation Add-on", "vehicle": "2023 Hyundai Creta", "status": "Active", "renewal": "2027-04-19", "premium": 3250},
]


def state_connection() -> sqlite3.Connection:
    """Open a short-lived SQLite connection for durable local-demo state."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(STATE_DB)
    connection.row_factory = sqlite3.Row
    return connection


def initialise_state() -> None:
    with state_connection() as connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                email TEXT PRIMARY KEY, name TEXT NOT NULL, role TEXT NOT NULL,
                salt TEXT NOT NULL, password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS claims (
                case_id TEXT PRIMARY KEY, customer_email TEXT NOT NULL,
                policy_id TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL, payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS claim_passports (
                token_hash TEXT PRIMARY KEY, customer_email TEXT NOT NULL,
                policy_id TEXT NOT NULL, issued_at TEXT NOT NULL,
                expires_at TEXT NOT NULL, used_at TEXT, revoked_at TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_claims_customer_policy
                ON claims(customer_email, created_at);
            CREATE INDEX IF NOT EXISTS idx_passports_customer_policy
                ON claim_passports(customer_email, policy_id, expires_at);
        """)
        columns = {row[1] for row in connection.execute("PRAGMA table_info(claims)")}
        if "policy_id" not in columns:
            connection.execute("ALTER TABLE claims ADD COLUMN policy_id TEXT NOT NULL DEFAULT ''")
        connection.execute("CREATE INDEX IF NOT EXISTS idx_claims_customer_policy_id ON claims(customer_email, policy_id)")


def persist_user(user: dict) -> None:
    with state_connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO users(email, name, role, salt, password_hash) VALUES (?, ?, ?, ?, ?)",
            (user["email"], user["name"], user["role"], user["salt"], user["password_hash"]),
        )


def restore_state() -> None:
    with state_connection() as connection:
        for row in connection.execute("SELECT email, name, role, salt, password_hash FROM users"):
            USERS[row["email"]] = dict(row)
        for row in connection.execute("SELECT payload FROM claims ORDER BY created_at"):
            CASES.append(json.loads(row["payload"]))


def persist_case(case: dict) -> None:
    with state_connection() as connection:
        connection.execute(
            "INSERT OR REPLACE INTO claims(case_id, customer_email, policy_id, created_at, payload) VALUES (?, ?, ?, ?, ?)",
            (case["case_id"], case["customer_email"], case["policy_id"], case["created_at"], json.dumps(case, ensure_ascii=False)),
        )


def persist_claim_submission(case: dict, passport_token: str | None = None) -> None:
    """Persist the claim and consume its passport in one atomic transaction."""
    with state_connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        if passport_token is not None:
            now = utc_now()
            token_hash = hashlib.sha256(passport_token.encode("utf-8")).hexdigest()
            cursor = connection.execute(
                """UPDATE claim_passports SET used_at = ?
                   WHERE token_hash = ? AND customer_email = ? AND policy_id = ?
                     AND used_at IS NULL AND revoked_at IS NULL AND expires_at > ?""",
                (now, token_hash, case["customer_email"], case["policy_id"], now),
            )
            if cursor.rowcount != 1:
                connection.rollback()
                raise ValueError("Claim Passport was expired, revoked or already used. Request a fresh token.")
        connection.execute(
            "INSERT INTO claims(case_id, customer_email, policy_id, created_at, payload) VALUES (?, ?, ?, ?, ?)",
            (case["case_id"], case["customer_email"], case["policy_id"], case["created_at"], json.dumps(case, ensure_ascii=False)),
        )
        connection.commit()


def previous_claim_count(email: str, policy_id: str) -> int:
    with state_connection() as connection:
        return int(connection.execute(
            "SELECT COUNT(*) FROM claims WHERE customer_email = ? AND policy_id = ?", (email, policy_id)
        ).fetchone()[0])


def issue_claim_passport(email: str, policy_id: str) -> dict:
    """Rotate a short-lived token. Only its SHA-256 digest is persisted."""
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=10)
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    with state_connection() as connection:
        # A fresh passport invalidates any earlier unused passport for the same
        # customer and policy. This is the explicit rotation behaviour.
        connection.execute(
            "UPDATE claim_passports SET revoked_at = ? WHERE customer_email = ? AND policy_id = ? AND used_at IS NULL AND revoked_at IS NULL",
            (issued_at.isoformat(timespec="seconds"), email, policy_id),
        )
        connection.execute(
            "INSERT INTO claim_passports(token_hash, customer_email, policy_id, issued_at, expires_at) VALUES (?, ?, ?, ?, ?)",
            (token_hash, email, policy_id, issued_at.isoformat(timespec="seconds"), expires_at.isoformat(timespec="seconds")),
        )
    return {"token": token, "expires_at": expires_at.isoformat(timespec="seconds")}


def consume_claim_passport(token: str, email: str, policy_id: str) -> bool:
    """Atomically consume a passport so a copied request cannot replay it."""
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = utc_now()
    with state_connection() as connection:
        cursor = connection.execute(
            """UPDATE claim_passports SET used_at = ?
               WHERE token_hash = ? AND customer_email = ? AND policy_id = ?
                 AND used_at IS NULL AND revoked_at IS NULL AND expires_at > ?""",
            (now, token_hash, email, policy_id, now),
        )
        return cursor.rowcount == 1


def claim_passport_is_valid(token: str, email: str, policy_id: str) -> bool:
    """Check eligibility early; final consumption occurs with claim persistence."""
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    now = utc_now()
    with state_connection() as connection:
        row = connection.execute(
            """SELECT 1 FROM claim_passports
               WHERE token_hash = ? AND customer_email = ? AND policy_id = ?
                 AND used_at IS NULL AND revoked_at IS NULL AND expires_at > ?""",
            (token_hash, email, policy_id, now),
        ).fetchone()
        return row is not None


def password_record(password: str, salt: bytes | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 240_000)
    return salt.hex(), digest.hex()


def add_user(email: str, password: str, name: str, role: str) -> None:
    salt, digest = password_record(password)
    USERS[email.lower()] = {"email": email.lower(), "name": name, "role": role, "salt": salt, "password_hash": digest}
    persist_user(USERS[email.lower()])


initialise_state()
restore_state()
if "customer@vericlaim.demo" not in USERS:
    add_user("customer@vericlaim.demo", "CustomerDemo!2026", "Ananya Rao", "customer")
if "staff@vericlaim.demo" not in USERS:
    add_user("staff@vericlaim.demo", "StaffDemo!2026", "Rohan Mehta", "staff")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_data_url(value: str) -> bytes:
    match = re.fullmatch(r"data:image/[A-Za-z0-9.+-]+;base64,(.+)", value, flags=re.DOTALL)
    if not match:
        raise ValueError("Image must be a base64 data URL")
    try:
        decoded = base64.b64decode(match.group(1), validate=True)
    except Exception as exc:
        raise ValueError("Invalid base64 image") from exc
    if len(decoded) > MAX_IMAGE_BYTES:
        raise ValueError("Each image must be 10 MB or smaller")
    return decoded


def parse_attachment_data_url(value: str) -> bytes:
    """Decode a PDF/video data URL while keeping a strict per-file limit."""
    match = re.fullmatch(r"data:(?:application/pdf|video/(?:mp4|webm));base64,(.+)", value, flags=re.DOTALL)
    if not match:
        raise ValueError("Attachment must be a PDF, MP4 or WEBM data URL")
    try:
        decoded = base64.b64decode(match.group(1), validate=True)
    except Exception as exc:
        raise ValueError("Invalid base64 attachment") from exc
    if len(decoded) > 40 * 1024 * 1024:
        raise ValueError("Each PDF or video must be 40 MB or smaller")
    return decoded


def safe_evidence_suffix(name: str, content_type: str) -> str:
    suffix = Path(name).suffix.lower()
    allowed = {".jpg", ".jpeg", ".png", ".webp", ".pdf", ".mp4", ".webm"}
    if suffix in allowed:
        return suffix
    return {
        "image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp",
        "application/pdf": ".pdf", "video/mp4": ".mp4", "video/webm": ".webm",
    }.get(content_type, ".bin")


def persist_evidence(case_id: str, image_inputs: list[tuple[dict, bytes]], attachments: list[dict]) -> list[dict]:
    """Persist local-demo originals and an auditable per-file evidence manifest."""
    case_dir = (EVIDENCE_DIR / case_id).resolve()
    evidence_root = EVIDENCE_DIR.resolve()
    if evidence_root not in case_dir.parents:
        raise ValueError("Invalid evidence storage path")
    case_dir.mkdir(parents=True, exist_ok=True)
    manifest: list[dict] = []

    for index, (result, raw) in enumerate(image_inputs, start=1):
        evidence_id = f"EV-{index:03d}"
        content_type = "image/jpeg" if str(result.get("name", "")).lower().endswith((".jpg", ".jpeg")) else "image/png" if str(result.get("name", "")).lower().endswith(".png") else "image/webp"
        stored_name = f"{evidence_id}{safe_evidence_suffix(str(result.get('name', 'claim-image')), content_type)}"
        (case_dir / stored_name).write_bytes(raw)
        manifest.append({
            "evidence_id": evidence_id, "name": str(result.get("name", "claim-image"))[:160],
            "kind": "image", "content_type": content_type, "size": len(raw), "stored_name": stored_name,
            "sha256": result["forensics"]["sha256"], "perceptual_hash": result["forensics"]["perceptual_hash"],
            "quality": result["forensics"]["quality_score"], "visual_fraud_probability": result["visual_fraud_probability"],
            "cnn_fraud_probability": result.get("cnn_fraud_probability"), "classification": result["image_classification"],
            "evidence_dna": result["evidence_dna"], "received_at": utc_now(),
        })

    for offset, item in enumerate(attachments, start=len(manifest) + 1):
        content_type = str(item.get("type", "")).lower()
        if content_type not in {"application/pdf", "video/mp4", "video/webm"}:
            raise ValueError("Unsupported evidence attachment type")
        raw = parse_attachment_data_url(str(item.get("data_url", "")))
        evidence_id = f"EV-{offset:03d}"
        stored_name = f"{evidence_id}{safe_evidence_suffix(str(item.get('name', 'evidence')), content_type)}"
        (case_dir / stored_name).write_bytes(raw)
        manifest.append({
            "evidence_id": evidence_id, "name": str(item.get("name", "evidence"))[:160],
            "kind": "document" if content_type == "application/pdf" else "video", "content_type": content_type,
            "size": len(raw), "stored_name": stored_name, "sha256": hashlib.sha256(raw).hexdigest(),
            "received_at": utc_now(),
        })
    return manifest


def evidence_passport(image_results: list[dict], score: dict) -> dict:
    """Convert raw image signals into an investigator-friendly evidence profile."""
    signals = score["signals"]
    coverage = min(100, int(len(image_results) / 3 * 100))
    diversity = max(0, int(100 - signals.get("within_claim_similarity", 0))) if len(image_results) > 1 else 35
    quality = int(signals["evidence_quality"])
    integrity = int(100 - signals["image_integrity"])
    coach: list[str] = []
    if len(image_results) < 3:
        coach.append("Add wider, closer and alternate-angle vehicle views for stronger evidence coverage.")
    if quality < 60:
        coach.append("Retake at least one image in better light and focus; low quality increases uncertainty.")
    if signals.get("within_claim_similarity", 0) >= 94:
        coach.append("Several uploads are visually very similar; add a different angle rather than another copy.")
    historical_matches = score.get("historical_evidence_matches", [])
    if historical_matches:
        best = historical_matches[0]
        coach.append(
            f"Possible evidence reuse detected ({best['similarity']}%): compare with {best['previous_case_id']} before disposition."
        )
    if not coach:
        coach.append("Evidence coverage is usable. Preserve original files and verify claim linkage before disposition.")
    twin_nodes = [
        {"name": "Labeled fraud archive", "similarity": signals["fraud_archive_similarity"], "kind": "fraud"},
        {"name": "Legitimate archive", "similarity": signals["legitimate_archive_similarity"], "kind": "legitimate"},
        {"name": "Within this claim", "similarity": signals.get("within_claim_similarity", 0), "kind": "claim"},
        {"name": "Prior submitted claims", "similarity": signals.get("historical_evidence_similarity", 0), "kind": "history"},
    ]
    return {
        "verdict": "Review required" if score["risk_tier"] in {"medium", "high"} else "Evidence appears consistent",
        "coverage": coverage,
        "diversity": diversity,
        "quality": quality,
        "integrity": integrity,
        "coach": coach,
        "historical_matches": historical_matches,
        "twin_radar": twin_nodes,
        "separation": "Evidence weakness and fraud-pattern signals are displayed separately; neither alone proves fraud.",
    }


class Handler(SimpleHTTPRequestHandler):
    server_version = "VeriClaim/1.0"

    def log_message(self, fmt: str, *args) -> None:
        print(f"{self.address_string()} - {fmt % args}")

    def send_json(self, payload: object, status: int = 200, session_token: str | None = None, session_age: int = 28_800) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        if session_token is not None:
            self.set_session_cookie(session_token, session_age)
        self.end_headers()
        self.wfile.write(body)

    def send_pdf(self, lines: list[str], filename: str) -> None:
        """Create a compact, dependency-free one-page investigation report."""
        y = 770
        commands = ["BT", "/F1 18 Tf", "0.03 0.18 0.12 rg", "44 800 Td", "(VeriClaim - Investigation Evidence Report) Tj", "ET"]
        for raw_line in lines:
            for line in textwrap.wrap(raw_line, width=88) or [""]:
                safe = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
                commands.extend(["BT", "/F1 10 Tf", "0.05 0.16 0.12 rg", f"44 {y} Td", f"({safe}) Tj", "ET"])
                y -= 15
                if y < 52:
                    break
            if y < 52:
                break
        stream = "\n".join(commands).encode("latin-1", errors="replace")
        objects = [
            b"<< /Type /Catalog /Pages 2 0 R >>",
            b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
            b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
            b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
            b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream",
        ]
        body = bytearray(b"%PDF-1.4\n")
        offsets = [0]
        for index, obj in enumerate(objects, start=1):
            offsets.append(len(body))
            body.extend(f"{index} 0 obj\n".encode() + obj + b"\nendobj\n")
        xref = len(body)
        body.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
        body.extend(b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets[1:]))
        body.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF".encode())
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0 or length > 90 * 1024 * 1024:
            raise ValueError("Invalid request size")
        return json.loads(self.rfile.read(length))

    def current_user(self) -> dict | None:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        token = cookie.get("vericlaim_session")
        email = SESSIONS.get(token.value) if token else None
        return USERS.get(email) if email else None

    def require_user(self, role: str | None = None) -> dict | None:
        user = self.current_user()
        if not user:
            self.send_json({"error": "Sign in required"}, status=401)
            return None
        if role and user["role"] != role:
            self.send_json({"error": "You do not have access to this workspace"}, status=403)
            return None
        return user

    @staticmethod
    def public_user(user: dict | None) -> dict | None:
        return {key: user[key] for key in ("email", "name", "role")} if user else None

    @staticmethod
    def public_case(case: dict, include_evidence_details: bool = False) -> dict:
        """Return role-appropriate claim data without exposing storage paths."""
        visible = dict(case)
        allowed = {"evidence_id", "name", "kind", "content_type", "size", "received_at"}
        if include_evidence_details:
            allowed |= {"sha256", "perceptual_hash", "quality", "visual_fraud_probability", "cnn_fraud_probability", "classification"}
        visible["evidence_manifest"] = [
            {**{key: value for key, value in evidence.items() if key in allowed}, "preview_available": bool(evidence.get("stored_name"))}
            for evidence in case.get("evidence_manifest", [])
        ]
        return visible

    def find_case(self, case_id: str) -> dict | None:
        with LOCK:
            return next((item for item in CASES if item["case_id"] == case_id), None)

    def handle_evidence_file(self, case_id: str, evidence_id: str) -> None:
        if not self.require_user("staff"):
            return
        case = self.find_case(case_id)
        if not case:
            self.send_json({"error": "Claim not found"}, status=404)
            return
        evidence = next((item for item in case.get("evidence_manifest", []) if item.get("evidence_id") == evidence_id), None)
        if not evidence or not evidence.get("stored_name"):
            self.send_json({"error": "Original evidence is unavailable for this legacy claim"}, status=404)
            return
        case_dir = (EVIDENCE_DIR / case_id).resolve()
        requested = (case_dir / str(evidence["stored_name"])).resolve()
        if case_dir not in requested.parents or not requested.is_file():
            self.send_json({"error": "Evidence file not found"}, status=404)
            return
        data = requested.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", str(evidence.get("content_type", "application/octet-stream")))
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Content-Disposition", f'inline; filename="{Path(str(evidence.get("name", "evidence"))).name}"')
        self.send_header("Cache-Control", "private, no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(data)

    def handle_evidence_attention(self, case_id: str, evidence_id: str) -> None:
        if not self.require_user("staff"):
            return
        case = self.find_case(case_id)
        evidence = next((item for item in (case or {}).get("evidence_manifest", []) if item.get("evidence_id") == evidence_id), None)
        if not case or not evidence or evidence.get("kind") != "image" or not evidence.get("stored_name"):
            self.send_json({"error": "Image evidence is unavailable for attention analysis"}, status=404)
            return
        evidence_path = (EVIDENCE_DIR / case_id / str(evidence["stored_name"])).resolve()
        if not evidence_path.is_file():
            self.send_json({"error": "Original evidence is unavailable for this legacy claim"}, status=404)
            return
        attention = efficientnet_attention_map(MODEL.cnn_backbone_path, MODEL.cnn_models, evidence_path.read_bytes(), int(MODEL.artifact.get("cnn_image_size", 224))) if MODEL.cnn_backbone_path else None
        self.send_json({"attention_map": attention, "note": "CNN attention map: regions that influenced the visual component only. It does not prove fraud or identify damage conclusively."})

    def set_session_cookie(self, token: str, max_age: int = 28_800) -> None:
        self.send_header("Set-Cookie", f"vericlaim_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={max_age}")

    def handle_login(self) -> None:
        payload = self.read_json()
        email = str(payload.get("email", "")).strip().lower()
        password = str(payload.get("password", ""))
        user = USERS.get(email)
        if not user:
            raise ValueError("Invalid email or password")
        _, candidate = password_record(password, bytes.fromhex(user["salt"]))
        if not hmac.compare_digest(candidate, user["password_hash"]):
            raise ValueError("Invalid email or password")
        token = secrets.token_urlsafe(32)
        with LOCK:
            SESSIONS[token] = email
        self.send_json({"user": self.public_user(user)}, session_token=token)

    def handle_signup(self) -> None:
        payload = self.read_json()
        email = str(payload.get("email", "")).strip().lower()
        name = str(payload.get("name", "")).strip()[:120]
        password = str(payload.get("password", ""))
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
            raise ValueError("Enter a valid email address")
        if len(name) < 2:
            raise ValueError("Enter your full name")
        if len(password) < 10 or not re.search(r"[A-Z]", password) or not re.search(r"\d", password):
            raise ValueError("Password must be at least 10 characters with an uppercase letter and number")
        with LOCK:
            if email in USERS:
                raise ValueError("An account already exists for this email")
            add_user(email, password, name, "customer")
            token = secrets.token_urlsafe(32)
            SESSIONS[token] = email
        self.send_json({"user": self.public_user(USERS[email])}, status=201, session_token=token)

    def handle_logout(self) -> None:
        cookie = SimpleCookie(self.headers.get("Cookie", ""))
        token = cookie.get("vericlaim_session")
        if token:
            with LOCK:
                SESSIONS.pop(token.value, None)
        self.send_json({"ok": True}, session_token="", session_age=0)

    def handle_draft(self) -> None:
        user = self.require_user("customer")
        if not user:
            return
        payload = self.read_json()
        draft = {key: str(payload.get(key, ""))[:500] for key in ("policy_id", "incident_date", "incident_type", "location", "description", "claim_amount")}
        draft["saved_at"] = utc_now()
        with LOCK:
            DRAFTS[user["email"]] = draft
        self.send_json({"draft": draft})

    def handle_claim_passport(self) -> None:
        """Issue a one-time token only when this is a repeat claim."""
        user = self.require_user("customer")
        if not user:
            return
        payload = self.read_json()
        policy_id = str(payload.get("policy_id", "")).strip()[:80]
        if not any(policy["policy_id"] == policy_id for policy in POLICIES):
            raise ValueError("Choose an active policy before requesting a claim passport")
        prior_claims = previous_claim_count(user["email"], policy_id)
        if prior_claims == 0:
            self.send_json({
                "required": False, "prior_claims": 0,
                "message": "First claim for this policy: your authenticated session is sufficient.",
            })
            return
        passport = issue_claim_passport(user["email"], policy_id)
        self.send_json({
            "required": True, "prior_claims": prior_claims,
            "claim_passport_token": passport["token"], "expires_at": passport["expires_at"],
            "message": "One-time Secure Claim Passport issued. It expires in 10 minutes and is consumed when this claim is submitted.",
        })

    def handle_model_test(self) -> None:
        payload = self.read_json()
        raw = parse_data_url(str(payload.get("data_url", "")))
        upload_name = str(payload.get("name", "model-lab-image"))[:160]
        def assess(model: VeriClaimModel) -> dict:
            result = model.analyze_image(raw)
            threshold = float(model.thresholds.get("classification", model.thresholds["review"]))
            probability = float(result["visual_fraud_probability"])
            return {
                "model_family": model.artifact.get("metrics", {}).get("model", model.artifact.get("model_family", "VeriClaim vision model")),
                "metrics": model.artifact.get("metrics", {}).get("classification_metrics", {}),
                "result": result,
                "fraud_probability": probability,
                "classification_threshold": threshold,
                "prediction_label": "FRAUD" if probability >= threshold else "NOT FRAUD",
                "threshold_met": probability >= threshold,
            }

        current = assess(MODEL)
        previous = assess(PREVIOUS_MODEL)
        # Keep the balanced binary output, but expose a separate operating
        # band so a high-confidence fraud alert uses a stricter threshold.
        probability = current["fraud_probability"]
        binary_threshold = current["classification_threshold"]
        investigate_threshold = float(MODEL.thresholds.get("investigate", binary_threshold))
        if probability >= investigate_threshold:
            operating_band = {
                "level": "high",
                "label": "High-confidence fraud alert",
                "action": "Priority investigation",
                "message": "This image cleared the strict investigation threshold and should be prioritized for human verification.",
            }
        elif probability >= binary_threshold:
            operating_band = {
                "level": "medium",
                "label": "Manual review recommended",
                "action": "Review evidence before deciding",
                "message": "The image meets the balanced fraud-screening threshold but not the strict high-confidence threshold.",
            }
        else:
            operating_band = {
                "level": "low",
                "label": "No fraud alert",
                "action": "Continue normal claim review",
                "message": "The image is below the balanced fraud-screening threshold. This does not prove that a claim is legitimate.",
            }
        result = current["result"]
        result["name"] = upload_name
        result["evidence_dna"] = build_evidence_dna(raw)
        sandbox_score = MODEL.score_claim([result], claim_amount=None)
        with LOCK:
            prior_case_snapshot = list(CASES)
        historical_matches = find_historical_matches([result], prior_case_snapshot)
        staff_user = self.current_user()
        lab_matches = []
        for match in historical_matches:
            visible = dict(match)
            case_id = str(visible.get("previous_case_id", ""))
            if not staff_user or staff_user.get("role") != "staff":
                visible["previous_case_id"] = f"VC-••••{case_id[-4:]}"
            lab_matches.append(visible)
        historical_similarity = lab_matches[0]["similarity"] if lab_matches else 0.0
        sandbox_score["signals"]["historical_evidence_similarity"] = historical_similarity
        sandbox_score["historical_evidence_matches"] = lab_matches
        if lab_matches:
            sandbox_score["factors"].insert(0, "Uploaded image resembles evidence from a previous claim; verify claim linkage.")
        lab_passport = evidence_passport([result], sandbox_score)
        lab_passport["historical_matches"] = []
        attention_map = None
        # This explains the CNN visual component only; archive and integrity
        # evidence remain separate and are never painted as visual attention.
        if MODEL.cnn_backbone_path is not None:
            try:
                attention_map = efficientnet_attention_map(
                    MODEL.cnn_backbone_path, MODEL.cnn_models, raw, int(MODEL.artifact.get("cnn_image_size", 224))
                )
            except Exception as exc:
                print(f"Grad-CAM attention map unavailable: {exc}")
        self.send_json({
            "status": "working",
            "model_family": current["model_family"],
            "classification": result["image_classification"],
            "prediction_label": current["prediction_label"],
            "fraud_probability": current["fraud_probability"],
            "classification_threshold": current["classification_threshold"],
            "review_threshold": current["classification_threshold"],
            "claim_review_threshold": float(MODEL.thresholds["review"]),
            "threshold_met": current["threshold_met"],
            "operating_band": {
                **operating_band,
                "balanced_threshold": binary_threshold,
                "high_confidence_threshold": investigate_threshold,
                "human_review_required": operating_band["level"] in {"medium", "high"},
            },
            "result": {key: value for key, value in result.items() if key != "evidence_dna"},
            "comparison": {"previous_model": previous},
            "evidence_reuse": {
                "status": "match" if lab_matches else "clear",
                "similarity": historical_similarity,
                "matches": lab_matches,
                "summary": "Potential transformed or partial reuse found" if lab_matches else "No strong match in previously submitted claim evidence",
                "policy": "A match routes evidence to an investigator; it is never an automatic fraud verdict.",
            },
            "evidence_passport": lab_passport,
            "attention_map": attention_map,
            "attention_note": "CNN attention map: areas that influenced the visual model component. It does not prove fraud or identify damage conclusively.",
            "disclaimer": "Screening result only. It is not proof of fraud and does not create or change a claim.",
        })

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/health":
            self.send_json({"status": "ok", "model": MODEL.artifact["feature_version"], "time": utc_now()})
            return
        if path == "/api/model-card":
            metrics = MODEL.artifact.get("metrics", {})
            self.send_json(metrics)
            return
        if path == "/api/model-comparison":
            def model_summary(model: VeriClaimModel, label: str, generation: str) -> dict:
                report = model.artifact.get("metrics", {})
                binary = report.get("classification_metrics", {})
                matrix = binary.get("confusion_matrix", {})
                return {
                    "label": label,
                    "generation": generation,
                    "model": report.get("model", model.artifact.get("model_family", "VeriClaim model")),
                    "architecture": report.get("cnn", {}).get("backbone", "MLP + ExtraTrees stack"),
                    "calibration": report.get("fusion", {}).get("probability_calibration", "No explicit probability calibration"),
                    "metrics": binary,
                    "correct": int(matrix.get("tn", 0)) + int(matrix.get("tp", 0)),
                    "errors": int(matrix.get("fp", 0)) + int(matrix.get("fn", 0)),
                }
            current = model_summary(MODEL, "EfficientNetV2B0 hybrid", "Current")
            previous = model_summary(PREVIOUS_MODEL, "MLP hybrid", "Previous")
            current_accuracy = float(current["metrics"].get("accuracy", 0))
            previous_accuracy = float(previous["metrics"].get("accuracy", 0))
            test_images = int(MODEL.artifact.get("metrics", {}).get("dataset", {}).get("test_images", 0))
            test_fraud = int(MODEL.artifact.get("metrics", {}).get("dataset", {}).get("test_fraud", 0))
            majority_accuracy = (test_images - test_fraud) / test_images if test_images else 0
            self.send_json({
                "models": [current, previous],
                "accuracy_gain_points": round((current_accuracy - previous_accuracy) * 100, 2),
                "majority_baseline_accuracy": round(majority_accuracy, 4),
                "note": "Accuracy is shown, but balanced accuracy, fraud recall and PR-AUC are more informative for this imbalanced dataset.",
            })
            return
        if path == "/api/threshold-simulator":
            metrics = MODEL.artifact.get("metrics", {})
            review = metrics.get("test_metrics", {})
            binary = metrics.get("classification_metrics", {})
            self.send_json({
                "modes": [
                    {"name": "Broad claim screening", "threshold": MODEL.thresholds.get("review"), "metrics": review, "description": "High recall: route more images to a human review queue."},
                    {"name": "Manual-review alert", "threshold": MODEL.thresholds.get("classification", MODEL.thresholds.get("review")), "metrics": binary, "description": "Balanced Model Lab alert: catches fraud while reducing false alerts."},
                    {"name": "High-confidence alert", "threshold": MODEL.thresholds.get("investigate"), "metrics": {}, "description": "Strict priority band. Used to focus investigators; never an automatic claim decision."},
                ],
                "note": "Threshold choices change workload and missed-fraud risk. They do not change the model itself.",
            })
            return
        if path == "/api/session":
            self.send_json({"user": self.public_user(self.current_user())})
            return
        if path == "/api/portal":
            user = self.require_user()
            if not user:
                return
            with LOCK:
                visible_cases = list(reversed(CASES)) if user["role"] == "staff" else [case for case in reversed(CASES) if case.get("customer_email") == user["email"]]
                messages = [message for message in MESSAGES if user["role"] == "staff" or message.get("customer_email") == user["email"]]
                notifications = [notice for notice in NOTIFICATIONS if notice.get("email") == ("staff" if user["role"] == "staff" else user["email"])]
            matrix = MODEL.artifact.get("metrics", {}).get("test_metrics", {}).get("confusion_matrix", {})
            self.send_json({
                "user": self.public_user(user),
                "policies": POLICIES if user["role"] == "customer" else [],
                "claims": [self.public_case(case, include_evidence_details=user["role"] == "staff") for case in visible_cases[:50]],
                "messages": messages[-50:],
                "notifications": notifications[-20:],
                "draft": DRAFTS.get(user["email"]),
                "analytics": {"pending": sum(case.get("status") not in {"Settled", "Rejected"} for case in CASES), "alerts": sum(case.get("risk_tier") in {"medium", "high"} for case in CASES), "settled": sum(case.get("status") == "Settled" for case in CASES), "model_recall": MODEL.artifact.get("metrics", {}).get("test_metrics", {}).get("recall"), "false_negatives": matrix.get("fn"), "feedback": {label: sum(case.get("reviewer_feedback") == label for case in CASES) for label in ("Confirmed fraud", "Legitimate", "Inconclusive")}},
            })
            return
        if path == "/api/cases":
            user = self.require_user("staff")
            if not user:
                return
            with LOCK:
                self.send_json({"cases": [self.public_case(case, include_evidence_details=True) for case in reversed(CASES[-50:])]})
            return
        attention_match = re.fullmatch(r"/api/claims/([A-Za-z0-9-]+)/evidence/(EV-\d{3})/attention", path)
        if attention_match:
            self.handle_evidence_attention(attention_match.group(1), attention_match.group(2))
            return
        evidence_match = re.fullmatch(r"/api/claims/([A-Za-z0-9-]+)/evidence/(EV-\d{3})", path)
        if evidence_match:
            self.handle_evidence_file(evidence_match.group(1), evidence_match.group(2))
            return
        report_match = re.fullmatch(r"/api/claims/([A-Za-z0-9-]+)/report", path)
        if report_match:
            self.handle_report(report_match.group(1))
            return
        receipt_match = re.fullmatch(r"/api/claims/([A-Za-z0-9-]+)/receipt", path)
        if receipt_match:
            self.handle_receipt(receipt_match.group(1))
            return
        if path == "/":
            path = "/index.html"
        if path.startswith("/assets/"):
            content_root = ASSET_DIR.resolve()
            requested = (ASSET_DIR / path.removeprefix("/assets/")).resolve()
        else:
            content_root = STATIC_DIR.resolve()
            requested = (STATIC_DIR / path.lstrip("/")).resolve()
        if content_root not in requested.parents and requested != content_root:
            self.send_error(HTTPStatus.FORBIDDEN)
            return
        if not requested.is_file():
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        data = requested.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(requested.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, max-age=0")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data: blob:; style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'")
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        try:
            if path == "/api/auth/login":
                self.handle_login()
                return
            if path == "/api/auth/signup":
                self.handle_signup()
                return
            if path == "/api/auth/logout":
                self.handle_logout()
                return
            if path == "/api/drafts":
                self.handle_draft()
                return
            if path == "/api/claim-passport":
                self.handle_claim_passport()
                return
            if path == "/api/model-test":
                self.handle_model_test()
                return
            if path == "/api/analyze":
                self.handle_analyze()
                return
            message_match = re.fullmatch(r"/api/claims/([A-Za-z0-9-]+)/messages", path)
            if message_match:
                self.handle_message(message_match.group(1))
                return
            status_match = re.fullmatch(r"/api/claims/([A-Za-z0-9-]+)/status", path)
            if status_match:
                self.handle_status(status_match.group(1))
                return
            feedback_match = re.fullmatch(r"/api/claims/([A-Za-z0-9-]+)/feedback", path)
            if feedback_match:
                self.handle_feedback(feedback_match.group(1))
                return
            decision_match = re.fullmatch(r"/api/cases/([A-Za-z0-9-]+)/decision", path)
            if decision_match:
                self.handle_decision(decision_match.group(1))
                return
            self.send_error(HTTPStatus.NOT_FOUND)
        except (ValueError, json.JSONDecodeError) as exc:
            self.send_json({"error": str(exc)}, status=400)
        except Exception as exc:
            print(f"Analysis failure: {exc}", file=sys.stderr)
            self.send_json({"error": "Analysis failed safely. Check the image format and retry."}, status=500)

    def handle_analyze(self) -> None:
        user = self.require_user("customer")
        if not user:
            return
        payload = self.read_json()
        policy_id = str(payload.get("policy_id", "")).strip()[:80]
        if not any(policy["policy_id"] == policy_id for policy in POLICIES):
            raise ValueError("Choose an active policy before submitting a claim")
        prior_claims = previous_claim_count(user["email"], policy_id)
        passport_used = False
        passport_token: str | None = None
        if prior_claims:
            passport_token = str(payload.get("claim_passport_token", ""))
            if not passport_token or not claim_passport_is_valid(passport_token, user["email"], policy_id):
                raise ValueError("Repeat claim requires a valid unused Secure Claim Passport. Request a fresh token and submit within 10 minutes.")
            passport_used = True
        images = payload.get("images", [])
        if not isinstance(images, list) or not (1 <= len(images) <= MAX_IMAGES):
            raise ValueError(f"Upload between 1 and {MAX_IMAGES} images")
        amount = payload.get("claim_amount")
        claim_amount = float(amount) if amount not in (None, "") else None
        if claim_amount is not None and not (0 <= claim_amount <= 100_000_000):
            raise ValueError("Claim amount is outside the supported range")

        image_results = []
        image_inputs: list[tuple[dict, bytes]] = []
        for item in images:
            raw = parse_data_url(str(item.get("data_url", "")))
            result = MODEL.analyze_image(raw)
            result["name"] = str(item.get("name", "claim-image"))[:160]
            result["evidence_dna"] = build_evidence_dna(raw)
            image_results.append(result)
            image_inputs.append((result, raw))

        score = MODEL.score_claim(image_results, claim_amount)
        with LOCK:
            prior_case_snapshot = list(CASES)
        historical_matches = find_historical_matches(image_results, prior_case_snapshot)
        historical_similarity = historical_matches[0]["similarity"] if historical_matches else 0.0
        score["signals"]["historical_evidence_similarity"] = historical_similarity
        score["historical_evidence_matches"] = historical_matches
        if historical_matches:
            best = historical_matches[0]
            score["factors"].insert(
                0,
                f"Transformation-resistant Evidence DNA matched prior claim {best['previous_case_id']} "
                f"({best['similarity']}%, {best['match_type']})",
            )
            # Reused evidence is a claim-linkage concern, not proof of fraud.
            # It therefore forces human review without issuing an automatic denial.
            if score["risk_tier"] == "low":
                score["risk_tier"] = "medium"
                score["decision"] = "Manual review"
                score["risk_score"] = max(float(score["risk_score"]), 55.0)
        case_id = f"VC-{uuid.uuid4().hex[:8].upper()}"
        attachment_inputs = payload.get("attachments", [])[:12]
        if not isinstance(attachment_inputs, list):
            raise ValueError("Invalid evidence attachments")
        evidence_manifest = persist_evidence(case_id, image_inputs, attachment_inputs)
        case = {
            "case_id": case_id,
            "created_at": utc_now(),
            "claimant": str(payload.get("claimant") or user["name"])[:120],
            "customer_email": user["email"],
            "policy_id": policy_id,
            "claim_security": {
                "authenticated_account": True,
                "repeat_claim": bool(prior_claims),
                "prior_claim_count": prior_claims,
                "secure_claim_passport_used": passport_used,
                "token_policy": "One-time, account-and-policy bound, SHA-256 hashed at rest, 10-minute expiry.",
            },
            "incident_type": str(payload.get("incident_type") or "Not specified")[:120],
            "claim_amount": claim_amount,
            "image_count": len(image_results),
            "status": "Under Review",
            "customer_status": "Under Review",
            "incident_date": str(payload.get("incident_date", ""))[:20],
            "location": str(payload.get("location", ""))[:180],
            "description": str(payload.get("description", ""))[:2000],
            "attachments": [{"name": str(item.get("name", "evidence"))[:160], "type": str(item.get("type", "file"))[:80], "size": int(item.get("size", 0))} for item in attachment_inputs],
            "evidence_manifest": evidence_manifest,
            "timeline": [{"status": "Submitted", "at": utc_now(), "complete": True}, {"status": "Under Review", "at": utc_now(), "complete": True}, {"status": "Decision", "at": None, "complete": False}, {"status": "Settled", "at": None, "complete": False}],
            **score,
        }
        case["evidence_passport"] = evidence_passport(image_results, score)
        with LOCK:
            persist_claim_submission(case, passport_token)
            CASES.append(case)
            DRAFTS.pop(user["email"], None)
            NOTIFICATIONS.append({"email": user["email"], "title": "Claim submitted", "message": f"{case['case_id']} is now under review.", "at": utc_now(), "read": False})
            if score["risk_tier"] in {"medium", "high"}:
                NOTIFICATIONS.append({"email": "staff", "title": "Fraud review alert", "message": f"{case['case_id']} crossed the review threshold.", "at": utc_now(), "read": False})
        public_image_results = [{key: value for key, value in row.items() if key != "evidence_dna"} for row in image_results]
        self.send_json({"case": self.public_case(case), "images": public_image_results})

    def handle_message(self, case_id: str) -> None:
        user = self.require_user()
        if not user:
            return
        payload = self.read_json()
        body = str(payload.get("message", "")).strip()[:2000]
        if not body:
            raise ValueError("Message cannot be empty")
        with LOCK:
            case = next((item for item in CASES if item["case_id"] == case_id), None)
            if not case:
                self.send_json({"error": "Claim not found"}, status=404)
                return
            if user["role"] != "staff" and case.get("customer_email") != user["email"]:
                self.send_json({"error": "You do not have access to this claim"}, status=403)
                return
            message = {"id": uuid.uuid4().hex, "case_id": case_id, "customer_email": case.get("customer_email"), "sender": user["name"], "sender_role": user["role"], "message": body, "at": utc_now()}
            MESSAGES.append(message)
            recipient = case.get("customer_email") if user["role"] == "staff" else "staff"
            NOTIFICATIONS.append({"email": recipient, "title": f"New message on {case_id}", "message": body[:140], "at": utc_now(), "read": False})
        self.send_json({"message": message}, status=201)

    def handle_status(self, case_id: str) -> None:
        user = self.require_user("staff")
        if not user:
            return
        payload = self.read_json()
        status = str(payload.get("status", ""))
        allowed = {"Under Review", "Approved", "Rejected", "Settled"}
        if status not in allowed:
            raise ValueError("Unsupported claim status")
        with LOCK:
            case = next((item for item in CASES if item["case_id"] == case_id), None)
            if not case:
                self.send_json({"error": "Claim not found"}, status=404)
                return
            case["status"] = status
            case["customer_status"] = status
            case["reviewer_decision"] = status
            case["reviewed_at"] = utc_now()
            for step in case.get("timeline", []):
                if (status in {"Approved", "Rejected"} and step["status"] == "Decision") or (status == "Settled" and step["status"] in {"Decision", "Settled"}):
                    step.update({"status": status if step["status"] == "Decision" else "Settled", "at": utc_now(), "complete": True})
            NOTIFICATIONS.append({"email": case.get("customer_email"), "title": f"Claim {status.lower()}", "message": f"{case_id} status changed to {status}.", "at": utc_now(), "read": False})
        self.send_json({"case": case})

    def handle_feedback(self, case_id: str) -> None:
        user = self.require_user("staff")
        if not user:
            return
        label = str(self.read_json().get("feedback", ""))
        if label not in {"Confirmed fraud", "Legitimate", "Inconclusive"}:
            raise ValueError("Unsupported feedback outcome")
        with LOCK:
            case = next((item for item in CASES if item["case_id"] == case_id), None)
            if not case:
                self.send_json({"error": "Claim not found"}, status=404)
                return
            case["reviewer_feedback"] = label
            case["feedback_by"] = user["name"]
            case["feedback_at"] = utc_now()
        self.send_json({"case": case})

    def handle_report(self, case_id: str) -> None:
        user = self.require_user("staff")
        if not user:
            return
        with LOCK:
            case = next((item for item in CASES if item["case_id"] == case_id), None)
        if not case:
            self.send_json({"error": "Claim not found"}, status=404)
            return
        signals = case.get("signals", {})
        report_lines = [
            f"Case: {case_id}",
            f"Generated: {utc_now()} | Analyst workspace: {user['name']}",
            "", "CLAIM CONTEXT",
            f"Claimant: {case.get('claimant', 'Not specified')} | Policy: {case.get('policy_id', 'Not specified')}",
            f"Incident type: {case.get('incident_type', 'Not specified')} | Claim amount: {case.get('claim_amount', 'Not specified')}",
            f"Workflow status: {case.get('status', 'Open')} | Recommendation: {case.get('decision', 'Not assessed')}",
            "", "MODEL EVIDENCE",
            f"Visual fraud screen: {signals.get('visual_model', 'N/A')}% | Risk score: {case.get('risk_score', 'N/A')}/100",
            f"Fraud archive similarity: {signals.get('fraud_archive_similarity', 'N/A')}% | Legitimate archive similarity: {signals.get('legitimate_archive_similarity', 'N/A')}%",
            f"Image integrity: {signals.get('image_integrity', 'N/A')}% | Evidence quality: {signals.get('evidence_quality', 'N/A')}",
            "", "INVESTIGATIVE REASONS",
            *[f"- {factor}" for factor in case.get("factors", [])],
            "", "EVIDENCE INVENTORY",
            *[f"- {item.get('evidence_id', 'EV')} | {item.get('kind', 'evidence')} | {item.get('name', 'evidence')} | SHA-256: {item.get('sha256', 'N/A')} | quality: {item.get('quality', 'N/A')}" for item in case.get("evidence_manifest", [])],
            "", "GOVERNANCE",
            "This report is decision support only. A model signal is not proof of fraud and cannot approve, reject, cancel or deny a claim.",
            "The authorized reviewer must verify documents, customer context and claim linkage before making a disposition.",
        ]
        self.send_pdf(report_lines, f"VeriClaim_{case_id}_evidence_report.pdf")

    def handle_receipt(self, case_id: str) -> None:
        user = self.require_user()
        if not user:
            return
        with LOCK:
            case = next((item for item in CASES if item["case_id"] == case_id), None)
        if not case:
            self.send_json({"error": "Claim not found"}, status=404)
            return
        if user["role"] != "staff" and case.get("customer_email") != user["email"]:
            self.send_json({"error": "You do not have access to this claim"}, status=403)
            return
        manifest = case.get("evidence_manifest", [])
        receipt_lines = [
            f"Claim evidence receipt: {case_id}",
            f"Issued: {utc_now()} | Claimant: {case.get('claimant', 'Not specified')}",
            "", "EVIDENCE RECEIVED",
            *[f"- {item.get('evidence_id', 'EV')} | {item['name']} | SHA-256: {item['sha256']} | quality: {item.get('quality', 'N/A')} | received: {item['received_at']}" for item in manifest],
            "", "RECEIPT PURPOSE",
            "This receipt records the image evidence received by the local prototype. It is not a coverage decision or confirmation that a claim will be approved.",
            "Retain original files and this receipt. Any later file replacement should create a separate evidence event.",
        ]
        self.send_pdf(receipt_lines, f"VeriClaim_{case_id}_evidence_receipt.pdf")

    def handle_decision(self, case_id: str) -> None:
        payload = self.read_json()
        decision = str(payload.get("decision", ""))
        allowed = {"Approve", "Escalate", "Request evidence", "Close"}
        if decision not in allowed:
            raise ValueError("Unsupported reviewer decision")
        with LOCK:
            case = next((item for item in CASES if item["case_id"] == case_id), None)
            if case is None:
                self.send_json({"error": "Case not found"}, status=404)
                return
            case["reviewer_decision"] = decision
            case["reviewed_at"] = utc_now()
            case["status"] = "Reviewed"
        self.send_json({"case": case})


def main() -> None:
    host = os.environ.get("VERICLAIM_HOST", "127.0.0.1")
    port = int(os.environ.get("VERICLAIM_PORT", "8080"))
    print(f"VeriClaim AI ready at http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()


if __name__ == "__main__":
    main()
