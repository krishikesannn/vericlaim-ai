# Solution architecture

## Design objective

Produce a review-ready evidence package in seconds while keeping claim adjudication with an authorized human.

## Logical flow

```mermaid
flowchart TD
  A[Claim intake] --> B[Format and quality validation]
  B --> C[Visual fraud model]
  B --> D[EXIF and integrity analysis]
  B --> E[Perceptual-hash retrieval]
  C --> F[Calibrated risk fusion]
  D --> F
  E --> F
  F --> G{Uncertainty gate}
  G -->|Low| H[Fast-track eligible]
  G -->|Medium| I[Manual review]
  G -->|High| J[Priority investigation]
  H --> K[Audit and monitoring]
  I --> K
  J --> K
```

## Prototype components

| Component | Prototype choice | Production alternative |
|---|---|---|
| Image intake | Base64 JSON over HTTPS | Object storage presigned upload with malware scanning |
| Visual model | Calibrated hybrid: frozen EfficientNetV2B0 ImageNet backbone + 5 grouped sigmoid heads + 5 MLPs + 5 class-weighted ExtraTrees + 20 rotating balanced ExtraTrees | Fine-tuned EfficientNet/ConvNeXt with insurer-owned temporal validation |
| Duplicate retrieval | Perceptual hash and Hamming distance | Embedding vector database with claim-level entity graph |
| Image integrity | EXIF, editor tags, quality and compression proxies | Dedicated manipulation detector and C2PA verification |
| Risk fusion | Cross-fitted class-weighted logistic stacker with Platt probability calibration | Validated stacking model plus configurable business rules |
| API | Python standard-library HTTP server | FastAPI/gRPC behind an API gateway |
| Case queue | In-memory session store | PostgreSQL + event stream + insurer case-management integration |
| Monitoring | Model-card endpoint | Drift, calibration, latency, override and fairness dashboards |

## Risk fusion

The prototype score is intentionally legible:

```text
risk = 0.74 visual_model
     + 0.18 confirmed_fraud_archive_similarity
     + 0.08 image_integrity
```

Evidence quality, legitimate-reference similarity and amount consistency remain visible to the investigator but do not independently increase the fraud score. Weights are a demonstration policy, not production coefficients. They must be validated against insurer losses, investigator capacity and false-positive costs.

## Security and privacy

- Reject unsupported types and images over the configured limit.
- Decode server-side; do not trust extensions or browser MIME labels.
- Use encryption in transit and at rest in production.
- Tokenize policy and claimant identifiers before analytics.
- Set evidence retention by jurisdiction and policy requirements.
- Separate model recommendation from the authoritative claims record.
- Log model version, threshold, component scores, reviewer action and reason.
- Run third-party image parsers in a sandboxed worker in production.

## Secure Claim Passport for repeat claims

The prototype adds a security control that is deliberately independent from
the fraud score. A first claim is authenticated by the customer session. When
the same authenticated account files another claim for the same policy, the
server issues a **Secure Claim Passport** immediately before submission.

## Transformation-resistant Evidence DNA

After account and policy validation, every submitted image receives an exact
SHA-256 fingerprint, whole-image perceptual signatures across rotation,
mirror, flip and photographic-negative variants, and overlapping multi-scale
regional signatures. Compact colour-and-edge descriptors provide additional
crop tolerance. The new evidence is searched against manifests persisted with
all earlier claims, including claims from other accounts.

A strong match records the previous claim ID, image name, similarity and match
type (`exact`, `transformed` or `partial`). It forces human review but never an
automatic rejection. Claim Passport consumption and claim persistence occur
in one SQLite transaction, preventing both token replay and token loss when
image analysis fails before submission.

```text
Authenticated customer + policy
        -> request repeat-claim passport
        -> revoke any earlier unused passport for that account/policy
        -> issue random one-time token (10-minute expiry)
        -> store only SHA-256 token digest in SQLite
        -> submit claim with token
        -> atomically mark token used
        -> reject replay, expired, revoked, wrong-account or wrong-policy use
```

Claims, user records and token audit records are persisted in the local SQLite
state database, so the repeat-claim control survives a server restart. The raw
passport token is never saved to the database and is held in browser memory
only until submission. Possession of a valid passport verifies an authenticated
submission path; it must not be treated as proof of legitimacy or used as a
fraud feature.

## Deployment alternatives

### Hackathon / local

Single process, CPU inference, static dashboard and saved model artifact. Best for a reliable offline demo.

### Cloud pilot

API gateway → validation worker → model service → vector search → case database → dashboard. Add object storage, identity, secrets management, queue-based retries and centralized observability.

### Enterprise integration

Publish a `ClaimEvidenceAssessed` event and attach the returned risk package to the existing claims platform. Preserve asynchronous operation so an ML outage does not block claim intake.
