# Sprint 0 — Working Directory

**Goal:** Produce 15 locked ADRs, a confirmed interface inventory, and a running project skeleton before Sprint 1 begins.

All decisions made here are binding. Changes after Sprint 0 closes require a new ADR that supersedes the original.

---

## ADR Progress Tracker

| ADR | Title | Status | Owner | Decided |
| :--- | :--- | :--- | :--- | :--- |
| [ADR-001](decisions/ADR-001-language-runtime.md) | Language & Runtime | OPEN | Tech Lead | — |
| [ADR-002](decisions/ADR-002-orchestration-framework.md) | Agentic Orchestration Framework | OPEN | Tech Lead | — |
| [ADR-003](decisions/ADR-003-llm-model-selection.md) | LLM Model Selection per Agent Role | OPEN | Tech Lead + SA | — |
| [ADR-004](decisions/ADR-004-embedding-model.md) | Embedding Model | OPEN | Tech Lead + SA | — |
| [ADR-005](decisions/ADR-005-retrieval-strategy.md) | Retrieval Strategy | OPEN | Tech Lead | — |
| [ADR-006](decisions/ADR-006-database-architecture.md) | Database Architecture | OPEN | SA | — |
| [ADR-007](decisions/ADR-007-caching-layer.md) | Caching Layer | OPEN | SA + DevOps | — |
| [ADR-008](decisions/ADR-008-object-storage.md) | Object Storage | OPEN | SA + DevOps | — |
| [ADR-009](decisions/ADR-009-deployment-platform.md) | Deployment Platform | OPEN | DevOps | — |
| [ADR-010](decisions/ADR-010-observability-stack.md) | Observability Stack | OPEN | Tech Lead + DevOps | — |
| [ADR-011](decisions/ADR-011-cicd-pipeline.md) | CI/CD Pipeline | OPEN | DevOps | — |
| [ADR-012](decisions/ADR-012-authentication-provider.md) | Authentication & Identity Provider | OPEN | SA + Tech Lead | — |
| [ADR-013](decisions/ADR-013-email-delivery.md) | Notification & Email Delivery | OPEN | DevOps | — |
| [ADR-014](decisions/ADR-014-connector-platforms.md) | External Connector Platforms (MVP Set) | OPEN | PM + Tech Lead | — |
| [ADR-015](decisions/ADR-015-speech-to-text.md) | Speech-to-Text Provider | OPEN | Tech Lead | — |

---

## Deliverable Progress Tracker

| # | Deliverable | Status | Owner | Done |
| :--- | :--- | :--- | :--- | :--- |
| D-01 | ADRs 001–015 written and merged | NOT STARTED | All | — |
| D-02 | Interface inventory reviewed and sprint assignments confirmed | NOT STARTED | PM | — |
| D-03 | Dependency manifest (all deps pinned) | NOT STARTED | Tech Lead | — |
| D-04 | Database migration (all ontology entities + RLS) | NOT STARTED | SA | — |
| D-05 | LangGraph graph skeleton with typed state and stub nodes | NOT STARTED | Tech Lead | — |
| D-06 | API skeleton with auth middleware and `/health` endpoint | NOT STARTED | Tech Lead | — |
| D-07 | 4 invariant integration tests passing in CI | NOT STARTED | QA | — |
| D-08 | CI/CD pipeline running on every PR | NOT STARTED | DevOps | — |
| D-09 | Observability connected to staging | NOT STARTED | DevOps | — |
| D-10 | Staging environment deployed and reachable | NOT STARTED | DevOps | — |
| D-11 | Evaluation dataset (3–5 historical requirement packages) | NOT STARTED | BA | — |
| D-12 | `CLAUDE.md` onboarding guide at repo root | NOT STARTED | Tech Lead | — |

---

## Decision Sequence

ADRs have dependencies. Evaluate them in this order to avoid re-work:

```
ADR-001 (Language)
    └── ADR-002 (Orchestration) — depends on language ecosystem
    └── ADR-009 (Deployment) — influences infra choices
            └── ADR-008 (Object Storage) — same cloud provider
            └── ADR-007 (Caching) — same cloud provider

ADR-003 (LLM Models)
    └── ADR-004 (Embedding) — ideally same vendor or compatible
    └── ADR-005 (Retrieval) — strategy depends on embedding vendor capabilities
            └── ADR-006 (Database) — schema depends on retrieval approach

ADR-012 (Auth) — independent; decide early as it affects API skeleton (D-06)
ADR-013 (Email) — independent; needed for D-06 notification wiring
ADR-014 (Connectors) — depends on PM deciding MVP scope
ADR-015 (Speech-to-Text) — can be deferred to Sprint 2 if audio not in MVP
ADR-010 (Observability) — independent; needed before D-09
ADR-011 (CI/CD) — independent; needed before D-08
```

---

## Interface Inventory

See [interfaces/interface-registry.md](interfaces/interface-registry.md) for the full enumeration of all 26 interfaces, their direction, mechanism, and sprint assignment.

---

## Governance

- Every ADR must be reviewed by at least two people before status moves to `ACCEPTED`.
- Once `ACCEPTED`, the ADR is locked. A new ADR must be written to supersede it — the original is never edited.
- All ADRs must be merged to `main` before Sprint 0 closes.
