# Delivery roadmap and estimate

## Prototype completed

| Workstream | Deliverable | Status |
|---|---|---|
| Data | Dataset audit, split statistics, duplicate check | Complete |
| Model | CPU ensemble, metrics, saved artifact | Complete |
| Novel signals | Similarity, EXIF/integrity, quality, amount mismatch | Complete |
| Experience | Intake, results, dashboard, review queue, model card | Complete |
| Engineering | Tests, container template, CI template, documentation | Complete |

## Production roadmap

| Phase | Duration | Team | Exit criteria |
|---|---:|---:|---|
| 1. Discovery and data contract | 2 weeks | Product, claims SME, data engineer, ML engineer | Approved labels, loss function, privacy and retention rules |
| 2. Multimodal model pilot | 4 weeks | 2 ML, 1 data, 1 backend | Claim-level holdout, calibrated model, retrieval benchmark |
| 3. Case workflow integration | 3 weeks | Backend, frontend, platform, claims SME | SSO, audit trail, case-system integration, accessibility |
| 4. Shadow deployment | 4 weeks | ML, MLOps, operations | Latency SLO, drift baseline, override analysis, red-team review |
| 5. Controlled rollout | 4–8 weeks | Cross-functional | Approved thresholds, rollback drill, documented operating model |

Estimated effort: **25–32 person-weeks** for a controlled pilot, excluding procurement and enterprise security lead time.

## Team split for the hackathon presentation

| Role | Demo responsibility |
|---|---|
| Product / claims lead | Problem framing, workflow and business value |
| Data lead | Dataset quality, imbalance and leakage audit |
| ML lead | Architecture, metrics, threshold and limitations |
| Full-stack lead | Live analysis and review queue |
| Platform / MLOps lead | Deployment, monitoring, security and roadmap |

