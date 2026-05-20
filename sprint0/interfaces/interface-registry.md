# Interface Registry

**Sprint:** 0
**Status:** DRAFT — requires PM review and sprint assignment confirmation before Sprint 0 closes (Deliverable D-02)

This document is the authoritative list of all external interfaces Chitragupt touches. Each interface is assigned to the sprint in which it is first implemented. Assignments marked `TBD` require PM decision.

---

## How to Use This Document

- **Direction:** Inbound = data flows into Chitragupt. Outbound = Chitragupt sends data out. Internal = infrastructure the app depends on.
- **Sprint:** The sprint in which the interface is first wired up (not designed — design happens in the sprint before).
- **Status:** PLANNED | IN SCOPE | DEFERRED | DESCOPED
- **ADR:** The decision record governing the vendor/technology choice for this interface.

---

## Inbound Interfaces (Data flows into Chitragupt)

| ID | Interface | Mechanism | Data Ingested | Sprint | Status | ADR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| I-01 | Direct file upload (PDF, DOCX, XLSX, TXT, MD) | HTTP multipart POST | Raw document binary | Sprint 1 | PLANNED | — |
| I-02 | Direct file upload (images: PNG, JPG, SVG) | HTTP multipart POST | Image binary → vision extraction pipeline | Sprint 2 | PLANNED | — |
| I-03 | Direct file upload (audio: MP3, MP4, WAV, M4A) | HTTP multipart POST → async queue | Audio binary → transcription pipeline | TBD | TBD | ADR-015 |
| I-04 | Jira (inbound) — epics, stories, custom fields | Jira REST API v3 + OAuth 2.0 | Issue body, custom fields, attachments, comments | Sprint 1 | TBD | ADR-014 |
| I-05 | Confluence (inbound) — pages, spaces | Confluence REST API v2 + OAuth 2.0 | Page content, page hierarchy, child pages | Sprint 1 | TBD | ADR-014 |
| I-06 | Notion (inbound) — pages, databases | Notion REST API + OAuth 2.0 | Page content, database rows as structured text | Sprint 1 | TBD | ADR-014 |
| I-07 | Google Docs / Drive (inbound) | Google Drive API v3 + OAuth 2.0 | Document content, spreadsheet rows | Sprint 1 | TBD | ADR-014 |
| I-08 | SharePoint / OneDrive (inbound) | Microsoft Graph API + Azure AD OAuth 2.0 | Document content, wiki pages | Sprint 1 | TBD | ADR-014 |
| I-09 | GitHub — repo file content (inbound) | GitHub REST API v3 + OAuth 2.0 | Markdown and text files at a specified path | Sprint 1 | TBD | ADR-014 |
| I-10 | Linear (inbound) — issues, project docs | Linear GraphQL API + OAuth 2.0 | Issue descriptions, project documents | Sprint 2 | TBD | ADR-014 |
| I-11 | Slack export (inbound) | Slack Export API or manual export upload | Channel message threads in JSON/HTML | Sprint 2 | TBD | ADR-014 |
| I-12 | Web URL ingestion | HTTP GET + HTML parser | Web page text content | Sprint 1 | PLANNED | — |
| I-13 | API push endpoint (programmatic ingestion) | REST API POST to `/api/v1/documents/ingest` | Any supported file format via multipart | Sprint 1 | PLANNED | — |

---

## Authentication & Identity Interfaces

| ID | Interface | Protocol | Direction | Sprint | Status | ADR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| I-14 | Email / password login | Custom (Argon2 + JWT) | Bidirectional | Sprint 0 | PLANNED | ADR-012 |
| I-15 | SAML 2.0 SSO (Okta, Azure AD, Google Workspace) | SAML 2.0 SP-initiated | Bidirectional | Sprint 0 | PLANNED | ADR-012 |
| I-16 | Social login (Google, Microsoft, GitHub) | OIDC / OAuth 2.0 | Bidirectional | Sprint 0 | PLANNED | ADR-012 |
| I-17 | API key authentication | HMAC / bearer token | Inbound | Sprint 1 | PLANNED | ADR-012 |

---

## AI & ML Service Interfaces (Outbound — Chitragupt calls these)

| ID | Interface | Role | Mechanism | Sprint | Status | ADR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| I-18 | Primary LLM provider | Reasoning, synthesis, conflict detection | Provider SDK + REST | Sprint 0 | PLANNED | ADR-003 |
| I-19 | Fast LLM provider | Classification, routing, PII pre-scan | Provider SDK + REST | Sprint 0 | PLANNED | ADR-003 |
| I-20 | Premium LLM provider | Final specification review | Provider SDK + REST | Sprint 3 | PLANNED | ADR-003 |
| I-21 | Fallback LLM provider (different vendor) | Activated on primary failure | Provider SDK + REST | Sprint 0 | PLANNED | ADR-003 |
| I-22 | Embedding model API | Chunk embedding | Provider SDK (batch) | Sprint 1 | PLANNED | ADR-004 |
| I-23 | Re-ranking model API | Top-K re-ranking after retrieval | Provider SDK | Sprint 1 | PLANNED | ADR-005 |
| I-24 | Vision / multimodal model API | Diagram and image extraction | Provider SDK | Sprint 2 | PLANNED | ADR-003 |
| I-25 | Speech-to-text API | Audio transcription | Provider REST + webhook | TBD | TBD | ADR-015 |

---

## Notification & Alerting Interfaces (Outbound)

| ID | Interface | Events | Mechanism | Sprint | Status | ADR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| I-26 | Transactional email | Budget alerts, conflict raised, approval request, export complete, ingestion failure | Email delivery API | Sprint 0 | PLANNED | ADR-013 |
| I-27 | In-app real-time notifications | Agent progress, conflict detected, requirement ready for review | WebSocket / Server-Sent Events | Sprint 1 | PLANNED | — |
| I-28 | Outbound webhook (post-approval) | Specification approved, requirement approved | HTTP POST (HMAC-signed) | Sprint 1 | PLANNED | — |
| I-29 | Slack notification | Conflict raised, budget alert, approval request | Slack Incoming Webhook or Slack API | Sprint 4 | PLANNED | ADR-014 |
| I-30 | Microsoft Teams notification | Same as Slack | Teams Incoming Webhook | Sprint 4 | TBD | ADR-014 |

---

## Export & Downstream Interfaces (Outbound — post human approval only)

| ID | Interface | What is Written | Mechanism | Sprint | Status | ADR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| I-31 | Jira (outbound) — create epics and stories | Requirements → Jira issues; AC → sub-tasks | Jira REST API v3 + OAuth 2.0 | Sprint 4 | PLANNED | ADR-014 |
| I-32 | Confluence (outbound) — publish spec as page | Specification → Confluence page tree | Confluence REST API v2 + OAuth 2.0 | Sprint 4 | PLANNED | ADR-014 |
| I-33 | Notion (outbound) — publish spec as database | Specification → Notion page/database | Notion API + OAuth 2.0 | Sprint 4 | TBD | ADR-014 |
| I-34 | GitHub Issues (outbound) | Requirements → GitHub Issues with labels | GitHub REST API v3 + OAuth 2.0 | Sprint 4 | TBD | ADR-014 |
| I-35 | Linear (outbound) | Requirements → Linear issues | Linear GraphQL + OAuth 2.0 | Sprint 4 | TBD | ADR-014 |
| I-36 | File export — DOCX | Specification rendered as Word document | In-process (python-docx or equivalent) | Sprint 3 | PLANNED | — |
| I-37 | File export — PDF | Specification rendered as PDF | In-process (headless browser or PDF lib) | Sprint 3 | PLANNED | — |
| I-38 | File export — Markdown | Specification rendered as structured Markdown | In-process string rendering | Sprint 3 | PLANNED | — |
| I-39 | File export — JSON | Specification serialized as raw JSON | In-process serialization | Sprint 1 | PLANNED | — |
| I-40 | Custom webhook | Event envelope + specification/requirement JSON | HTTP POST (HMAC-signed) to user URL | Sprint 1 | PLANNED | — |

---

## Infrastructure Interfaces (Internal — application depends on these)

| ID | Interface | Role | Mechanism | Sprint | Status | ADR |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| I-41 | Object storage | Raw document upload, download, presigned URLs | Cloud SDK | Sprint 0 | PLANNED | ADR-008 |
| I-42 | Secrets management | API keys, DB credentials, JWT signing keys | Cloud SDK | Sprint 0 | PLANNED | ADR-009 |
| I-43 | Relational database | All entity persistence + vector embeddings | TCP + SQL driver | Sprint 0 | PLANNED | ADR-006 |
| I-44 | Cache | Session state, idempotency keys, rate-limit counters | Redis protocol / SDK | Sprint 0 | PLANNED | ADR-007 |
| I-45 | Observability / tracing | LLM span ingestion, cost attribution, alerting | SDK | Sprint 0 | PLANNED | ADR-010 |
| I-46 | Email delivery service | Transactional email dispatch | REST API / SMTP | Sprint 0 | PLANNED | ADR-013 |
| I-47 | Container image registry | Store built application images | Docker push/pull | Sprint 0 | PLANNED | ADR-009 |
| I-48 | CI runner | Automated test, build, deploy pipeline | Platform-managed | Sprint 0 | PLANNED | ADR-011 |

---

## Sprint Assignment Summary

| Sprint | Interfaces Going Live |
| :--- | :--- |
| Sprint 0 | I-14, I-15, I-16, I-18, I-19, I-21, I-26, I-41, I-42, I-43, I-44, I-45, I-46, I-47, I-48 |
| Sprint 1 | I-01, I-04\*, I-05\*, I-06\*, I-07\*, I-08\*, I-09\*, I-12, I-13, I-17, I-22, I-23, I-27, I-28, I-39, I-40 |
| Sprint 2 | I-02, I-10, I-11, I-20\*, I-24 |
| Sprint 3 | I-36, I-37, I-38 |
| Sprint 4 | I-29, I-30\*, I-31, I-32, I-33\*, I-34\*, I-35\* |
| TBD | I-03, I-25 (audio — PM must confirm MVP scope) |

\* Scope confirmed by ADR-014 (connector platform MVP set)

---

> Last updated: Sprint 0 • Chitragupt • May 2026
