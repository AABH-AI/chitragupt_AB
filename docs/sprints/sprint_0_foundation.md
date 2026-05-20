# Sprint 0: Foundation, Technology Selection & Project Scaffolding

**Phase:** Architecture Kickoff & Technology Setup
**Duration:** 2 Weeks (Milestone 0)
**Sprint Goal:** Evaluate, select, and document every technology and architectural decision that subsequent sprints build on. Leave the sprint with a running project skeleton and a locked set of ADRs. No business logic is written in this sprint.

---

## 0. Purpose & Scope

Sprint 0 is a decision sprint, not a build sprint. Its output is a set of locked Architecture Decision Records (ADRs) and a project scaffold that reflects those decisions. Subsequent sprints treat Sprint 0 ADRs as constraints — they do not re-open decisions unless a formal ADR revision is raised.

Every decision made in this sprint must be traceable to at least one of the three governing axes:

| Axis | Definition |
| :--- | :--- |
| **Security** | Tenant isolation, data residency, no-training guarantees, compliance posture |
| **Budget** | Total cost of ownership: hosting, API, and engineering hours to operate |
| **Operational Simplicity** | Fewer moving parts, managed services where appropriate, sustainable on-call burden |

A candidate that fails the Security axis is disqualified regardless of its score on the other two.

---

## 1. Decision Areas

The following areas require a formal decision and a written ADR before Sprint 0 closes. Each area lists the questions the team must answer and the evaluation criteria to use.

---

### 1.1 Language & Runtime

**Decision needed:** Primary application language and version.

**Evaluation criteria:**
- Maturity of the orchestration and LLM SDK ecosystem in that language
- Static type safety and tooling support
- Team proficiency

**Required output:** ADR-001 — Language & Runtime Selection

---

### 1.2 Agentic Orchestration Framework

**Decision needed:** Framework for building and executing the multi-step LangGraph (or equivalent) agent pipeline.

**Evaluation criteria:**
- Support for explicit, inspectable state machines (required by INV-PERF-01 and INV-PERF-02)
- Native support for human-in-the-loop interrupts (required by INV-HITL-01 through INV-HITL-04)
- Horizontal scalability — agents must be stateless between invocations
- Observability and tracing integration
- Vendor lock-in risk

**Required output:** ADR-002 — Orchestration Framework Selection

---

### 1.3 Primary LLM Models

**Decision needed:** Pinned model IDs for each agent role. Floating aliases are prohibited in production (INV-MODEL-03).

**Agent roles that require a model assignment:**

| Role | Purpose | Tier constraint |
| :--- | :--- | :--- |
| Classification / routing | Document type detection, intent classification | Fast / low-cost |
| Primary reasoning | Synthesis, conflict detection, gap analysis | Quality |
| Premium reasoning | Final specification review (if used) | Premium — must be gated by plan tier |
| Fallback | Activates when primary provider is unavailable | Must be a different vendor |

**Evaluation criteria:**
- Quality on long-context reasoning over technical business documents
- Context window size (requirements corpus can be large)
- Structured output reliability (INV-MODEL-04 requires schema-valid JSON every time)
- Cost per token relative to quality
- Data retention policy — enterprise/zero-retention endpoints required (security axis)
- Provider resilience and rate limit posture

**Required output:** ADR-003 — LLM Model Selection per Agent Role

---

### 1.4 Embedding Model

**Decision needed:** A single embedding model and dimension size for the entire vector namespace. Once chosen and data is written, this cannot be changed without a full re-embedding (INV-MODEL-05).

**Evaluation criteria:**
- Retrieval quality on technical, domain-specific prose (benchmark: MTEB retrieval subset)
- Native output dimensions (prefer models that do not require truncation)
- Cost per token
- Data retention and privacy posture of the embedding API provider
- Availability of a cross-encoder / re-ranking model from the same vendor (reduces distribution shift between embedding and re-ranking)
- Fallback story if the provider is unavailable (INV-PERF-03 — ingestion must queue, not fail silently)

**Required output:** ADR-004 — Embedding Model Selection

---

### 1.5 Retrieval Strategy

**Decision needed:** How chunks are retrieved from the vector store for each synthesis query: dense-only, sparse-only (keyword), hybrid, or some variant.

**Evaluation criteria:**
- Precision on exact-match queries (requirement IDs, regulatory clause numbers, named entities) — dense-only tends to miss these
- Precision on semantic queries (conceptual similarity) — sparse-only tends to miss these
- Latency budget per retrieval call
- Complexity of maintaining dual indexes in production
- Whether a re-ranking step is needed and at what retrieval depth

**Required output:** ADR-005 — Retrieval Strategy (dense / sparse / hybrid + re-ranking decision)

---

### 1.6 Relational & Vector Database

**Decision needed:** Where structured relational data and vector embeddings are stored. May be the same system or separate systems.

**Evaluation criteria:**
- Ability to enforce Row-Level Security at the database layer (INV-SEC-01 requires tenant isolation that survives application bugs)
- Query performance for filtered vector similarity search (mandatory filters: `tenant_id`, `project_id`, `is_active`)
- Operational complexity of running two separate datastores vs. a combined solution
- Managed service availability on the target cloud provider
- Cost at expected data volume (number of chunks × embedding dimensions)
- Compliance: data residency, encryption at rest and in transit

**Required output:** ADR-006 — Database Architecture (relational + vector)

---

### 1.7 Caching Layer

**Decision needed:** Technology and topology for session state caching, idempotency keys, and LLM prompt caching metadata.

**Evaluation criteria:**
- Sub-millisecond read latency for session state warm cache
- Support for TTL-based expiry (session state should expire after inactivity)
- Managed service availability
- Cost at expected concurrency

**Required output:** ADR-007 — Caching Layer Selection

---

### 1.8 Object Storage

**Decision needed:** Where raw uploaded documents are stored.

**Evaluation criteria:**
- Path-based tenant isolation (INV-SEC-03 requires `/{tenant_id}/{project_id}/` prefix enforcement)
- Presigned URL generation scoped to a single object
- Integration with the target deployment platform
- Retention policy and WORM support for locked specifications

**Required output:** ADR-008 — Object Storage Selection

---

### 1.9 Infrastructure & Deployment Platform

**Decision needed:** How the application is deployed and scaled.

**Evaluation criteria:**
- Cold start latency (streaming LLM responses require fast container readiness — INV-UX-01)
- Auto-scaling behavior under variable load (ingestion jobs are bursty)
- Managed vs. self-hosted operational model
- Cost at baseline and peak load
- Integration with secrets management and IAM for least-privilege access

**Required output:** ADR-009 — Deployment Platform Selection

---

### 1.10 Observability Stack

**Decision needed:** How LLM traces, costs, latencies, and model outputs are captured and monitored.

**Evaluation criteria:**
- Native support for LLM-specific telemetry (token counts, model IDs, prompt/completion capture)
- Per-tenant and per-project cost attribution (required by INV-COST-03)
- Alerting when budget thresholds are approached (INV-COST-01 and INV-COST-02)
- Data retention and privacy posture of the observability provider
- Self-hosted vs. managed tradeoff

**Required output:** ADR-010 — Observability Stack Selection

---

### 1.11 CI/CD Pipeline

**Decision needed:** Toolchain for automated testing, building, and deploying the application.

**Evaluation criteria:**
- Native integration with the source repository
- Support for containerized test environments (integration tests require a real database)
- Security scanning (dependency vulnerabilities, static analysis)
- Cost at expected PR frequency

**Required output:** ADR-011 — CI/CD Pipeline Selection

---

## 2. Interfaces & External Sources Inventory

This section enumerates every external system or service category that Chitragupt is likely to touch. The purpose is to surface integration surface area early so that authentication, data contracts, and security posture decisions are made before Sprint 1 builds anything that depends on them. Each entry lists the integration direction, the mechanism, and the data that flows — not a chosen product.

Entries marked **[Decision Required]** need an ADR or a confirmed selection before the relevant sprint begins. Entries marked **[Fixed Interface]** are standard protocols where the product category is known but the vendor is still open.

---

### 2.1 Ingestion Sources (Inbound — data flows into Chitragupt)

These are the external systems from which source documents and structured data are pulled or pushed into the ingestion pipeline.

| Category | Likely Platforms | Mechanism | Data Ingested | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Direct file upload** | Browser, API client | HTTP multipart form / REST API POST | PDF, DOCX, XLSX, TXT, MD, images, audio, video | Primary ingestion path for most clients; applies to all source types |
| **Project management** | Jira, Linear, GitHub Issues, Azure DevOps, Shortcut | REST API (OAuth 2.0) + webhooks | Epics, stories, custom fields, descriptions, comments, attachments | Structured data with high trust tier; pulls issue body as text + metadata |
| **Documentation & wikis** | Confluence, Notion, SharePoint, Google Docs, GitBook | REST API (OAuth 2.0) or export API | Page content, page hierarchy, embedded images, last-modified timestamps | Treated as primary source documents; page version used for staleness detection |
| **Cloud file storage** | Google Drive, Dropbox, OneDrive, Box | REST API (OAuth 2.0) | File content (any format in the supported set), folder structure | User selects files to ingest; Chitragupt downloads and processes them |
| **Version control repositories** | GitHub, GitLab, Bitbucket | REST API (OAuth 2.0 or PAT) | Markdown files, plain-text specs, README files in a selected path | Useful for teams that store requirement docs as files in a repo |
| **Communication platforms** | Slack, Microsoft Teams | Export API or Slack Events API | Thread exports, channel message exports, meeting transcripts | Low trust tier (secondary source); must be explicitly scoped by user — not bulk-pulled |
| **Web / URL** | Any public URL | HTTP GET + HTML parser | Web page text, publicly accessible documentation | Marked as `source_type: web_url`; no authoritativeness guarantee |
| **Audio & video files** | Zoom, Teams, Google Meet exports; MP3/MP4 | File upload → speech-to-text pipeline | Transcribed text with speaker labels | Meeting recordings transcribed before embedding; speakers mapped to stakeholders where possible |
| **API push (custom)** | Customer-built integrations | REST API POST to Chitragupt ingestion endpoint | Any structured or unstructured document content | Authenticated with API key; enables programmatic ingestion from internal systems |

**Integration decisions needed for Sprint 1:**
- Which project management platforms are supported in the MVP connector set?
- Which documentation platforms are supported in the MVP connector set?
- OAuth 2.0 app registrations needed per platform before connectors can be built

---

### 2.2 Authentication & Identity Providers

| Protocol | Use Case | Mechanism | Notes |
| :--- | :--- | :--- | :--- |
| **Email / password** | Default internal user accounts | Argon2 password hash + JWT session tokens | Baseline for all tiers |
| **SAML 2.0** | Enterprise SSO (Okta, Azure AD, Google Workspace, Ping Identity) | SP-initiated SAML 2.0 assertion | Required for enterprise and business plan workspaces; workspace-level configuration |
| **OIDC / OAuth 2.0** | Social login and SSO (Google, Microsoft, GitHub) | Authorization code flow with PKCE | Convenience login for non-enterprise users |
| **API keys** | Service-to-service, webhook senders, programmatic ingestion | Long-lived scoped tokens | Scoped to workspace; rotatable; stored hashed |
| **JWT (internal)** | Session token issued after any login method | HS256 or RS256 signed, short-lived with refresh | Must carry `tenant_id`, `user_id`, `role`, and `plan_tier` claims |

**[Decision Required]:** Authentication provider selection — self-built vs. managed identity service (e.g., Auth0, AWS Cognito, Clerk). See ADR-012.

---

### 2.3 AI & ML Service APIs (Outbound — Chitragupt calls these)

| Role | Service Category | Mechanism | Data Sent | Data Received | Constraint |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary LLM reasoning** | LLM provider API | REST / provider SDK | System prompt, retrieved chunks, user query | Structured JSON requirement/conflict/gap objects | Zero data retention endpoint required |
| **Fast / classification LLM** | LLM provider API (same or different vendor) | REST / provider SDK | Short classification prompt, document excerpt | Classification label, confidence | Same zero retention requirement |
| **Fallback LLM** | Secondary LLM provider API (different vendor) | REST / provider SDK | Same payload as primary | Same schema as primary | Must be a different vendor from primary (INV-MODEL-01) |
| **Embedding model** | Embedding provider API | REST / provider SDK (batch) | Chunk text (batch of N chunks) | Float vector per chunk | Single model pinned for entire namespace (INV-MODEL-05); fallback = queue, not switch model |
| **Re-ranking model** | Cross-encoder provider API | REST / provider SDK | Query + top-N candidate chunk texts | Re-ranked list with scores | Latency-sensitive; called inline during retrieval |
| **Vision / multimodal** | Vision-capable LLM API | REST / provider SDK | Image bytes or base64 encoded image | Extracted text description of diagram/screenshot | All output tagged `[VISUAL EXTRACTION — VERIFY]`; confidence capped at 0.80 (INV-EPI-06) |
| **Speech-to-text** | Audio transcription API | REST / provider SDK | Audio file (MP3/MP4/WAV) | Timestamped transcript with speaker diarisation | Transcript is then processed as a text document through the standard ingestion pipeline |
| **PII detection** | Dedicated PII scan service or LLM call | REST | Chunk text before embedding | PII entity spans + classification | Mandatory step before any embedding call (INV-SEC-02, INV-COMP-03) |

**[Decision Required]:** For each AI role, the vendor and pinned model ID must be selected and recorded in ADR-003 (LLM) and ADR-004 (Embedding). The vision and speech-to-text providers may require separate ADRs if the vendor differs from the primary LLM provider.

---

### 2.4 Notification & Alerting Channels (Outbound — Chitragupt sends to these)

| Channel | Trigger Events | Mechanism | Notes |
| :--- | :--- | :--- | :--- |
| **Transactional email** | Budget cap approaching (80%), budget cap reached, conflict raised, approval request, export complete, ingestion failure | SMTP or email delivery API | Required for all plan tiers; must support HTML templates |
| **In-app / real-time** | Any live event during an active session: agent progress, conflict detected, gap raised, requirement ready for review | WebSocket or Server-Sent Events (SSE) | Required by INV-UX-01 (visible response within 2 seconds) |
| **Outbound webhook** | Human approval of a specification, spec exported | HTTP POST to user-configured URL | Fires only after human approval (INV-HITL-02); configurable per workspace; signed with HMAC |
| **Slack notification** | Conflict raised, approval request, budget alert | Slack Incoming Webhook or Slack API | Optional workspace integration; not required for MVP |
| **Microsoft Teams notification** | Same as Slack | Teams Incoming Webhook | Optional workspace integration; not required for MVP |

**[Decision Required]:** Transactional email delivery provider (self-hosted SMTP vs. managed service). See ADR-013.

---

### 2.5 Export & Downstream Integrations (Outbound — triggered after human approval only)

These integrations fire **only** after an explicit human approval action on a finalized specification (INV-HITL-02). They are write operations on external systems.

| Downstream System | What is Written | Mechanism | Data Contract | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Jira** | Epics and Stories created from approved requirements; acceptance criteria mapped to Jira fields | Jira REST API (OAuth 2.0) | Requirement → Jira Issue; AC items → sub-tasks or description fields | User maps Chitragupt requirement types to Jira issue types at workspace setup |
| **Linear** | Issues created from approved requirements | Linear GraphQL API (OAuth 2.0) | Requirement → Linear Issue | Linear supports markdown in descriptions; AC can be embedded |
| **GitHub Issues** | Issues created from approved requirements | GitHub REST API (OAuth 2.0 or PAT) | Requirement → GitHub Issue with labels | Labels map to requirement type and priority |
| **Azure DevOps** | Work items created from approved requirements | Azure DevOps REST API (PAT or OAuth) | Requirement → Work Item (User Story / Feature) | |
| **Confluence** | Approved specification published as a Confluence page or page tree | Confluence REST API (OAuth 2.0) | Specification → Confluence storage format page | Page is created under a user-configured space and parent page |
| **Notion** | Approved specification published as a Notion database entry or page | Notion API (OAuth 2.0) | Specification → Notion page with property blocks | |
| **File export (DOCX)** | Specification rendered as a Word document | In-process template rendering (python-docx or equivalent) | Specification JSON → formatted DOCX | Downloaded via browser; not pushed to external system |
| **File export (PDF)** | Specification rendered as a PDF | In-process rendering via headless browser or PDF library | Specification JSON → PDF | Downloaded via browser |
| **File export (Markdown)** | Specification rendered as structured Markdown | In-process string rendering | Specification JSON → Markdown | Suitable for committing to a repository |
| **File export (JSON)** | Specification exported as raw structured JSON | In-process serialization | Full Requirement schema objects | For custom downstream tooling |
| **Custom webhook** | Any approval event; payload is the specification or requirement JSON | HTTP POST to workspace-configured URL | Chitragupt event envelope + specification/requirement object | HMAC-signed; receiver must verify signature |

**Integration decisions needed for Sprint 4 (Integrations Sprint):**
- Which downstream connectors are in the MVP set vs. later releases?
- OAuth app registrations needed per platform
- Field mapping configuration UI design

---

### 2.6 Infrastructure Service APIs (Internal — application depends on these)

These are the cloud and platform services the application calls for its own operation. They are not user-facing integrations but must be evaluated and provisioned in Sprint 0.

| Service Role | Category | Mechanism | What it provides |
| :--- | :--- | :--- | :--- |
| **Object storage** | Cloud blob store | SDK | Raw document upload, download, presigned URL scoped to `/{tenant_id}/{project_id}/` |
| **Secrets management** | Cloud secrets vault | SDK | API keys, database credentials, JWT signing keys — never stored in environment variables or code |
| **Container orchestration** | Cloud container platform | Platform API / control plane | Deploy, scale, and health-check application containers |
| **Database** | Managed relational DB | TCP + SQL (asyncpg driver) | All relational data + vector embeddings (if co-located) |
| **Cache** | Managed in-memory store | SDK / Redis protocol | Session state, idempotency keys, rate-limit counters |
| **Email delivery** | Transactional email service | REST API or SMTP | Outbound notification emails |
| **Observability / tracing** | LLM tracing platform | SDK | Span ingestion, cost attribution, alert rules |
| **DNS & TLS** | Cloud DNS + certificate manager | Control plane | Domain resolution and automatic TLS certificate provisioning |
| **Container image registry** | Cloud container registry | Docker push/pull | Stores built application container images |
| **CI runner** | CI/CD compute | Platform-managed | Runs lint, test, build, and deploy pipelines |

**[Decision Required]:** Cloud provider selection (if not already fixed by client constraint) — this determines which managed services are available for each role above. See ADR-009.

---

### 2.7 Interface Inventory Summary

| # | Interface | Direction | Sprint | ADR |
| :--- | :--- | :--- | :--- | :--- |
| I-01 | Direct file upload | Inbound | Sprint 1 | — |
| I-02 | Project management connectors (Jira, Linear, GitHub Issues, Azure DevOps) | Inbound + Outbound | Sprint 1 (inbound) / Sprint 4 (outbound) | ADR-014 |
| I-03 | Documentation & wiki connectors (Confluence, Notion, SharePoint, Google Docs) | Inbound + Outbound | Sprint 1 (inbound) / Sprint 4 (outbound) | ADR-014 |
| I-04 | Cloud file storage connectors (Drive, Dropbox, OneDrive, Box) | Inbound | Sprint 1 | ADR-014 |
| I-05 | Version control repository connectors (GitHub, GitLab) | Inbound | Sprint 1 | ADR-014 |
| I-06 | Communication platform exports (Slack, Teams) | Inbound | Sprint 2 | ADR-014 |
| I-07 | Web URL ingestion | Inbound | Sprint 1 | — |
| I-08 | Audio / video file ingestion | Inbound | Sprint 2 | ADR-015 (speech-to-text provider) |
| I-09 | API push endpoint (custom integrations) | Inbound | Sprint 1 | — |
| I-10 | Authentication providers (email/password, SAML, OIDC) | Bidirectional | Sprint 0 | ADR-012 |
| I-11 | LLM provider APIs (primary, fast, premium, fallback) | Outbound | Sprint 0 | ADR-003 |
| I-12 | Embedding model API | Outbound | Sprint 0 | ADR-004 |
| I-13 | Re-ranking model API | Outbound | Sprint 0 | ADR-005 |
| I-14 | Vision / multimodal model API | Outbound | Sprint 2 | ADR-003 or separate |
| I-15 | Speech-to-text API | Outbound | Sprint 2 | ADR-015 |
| I-16 | PII detection | Outbound | Sprint 0 | ADR-003 or separate |
| I-17 | Transactional email | Outbound | Sprint 0 | ADR-013 |
| I-18 | In-app real-time notifications (WebSocket / SSE) | Outbound | Sprint 1 | — |
| I-19 | Outbound webhooks (post-approval) | Outbound | Sprint 1 | — |
| I-20 | Slack / Teams notifications | Outbound | Sprint 4 | — |
| I-21 | Jira / Linear / GitHub Issues export (post-approval) | Outbound | Sprint 4 | ADR-014 |
| I-22 | Confluence / Notion export (post-approval) | Outbound | Sprint 4 | ADR-014 |
| I-23 | File exports (DOCX, PDF, Markdown, JSON) | Outbound | Sprint 3 | — |
| I-24 | Object storage service | Internal | Sprint 0 | ADR-008 |
| I-25 | Secrets management service | Internal | Sprint 0 | ADR-009 |
| I-26 | Observability / tracing service | Internal | Sprint 0 | ADR-010 |

---

## 3. RAG Pipeline Architecture Decisions

Beyond individual tool selection, the team must define and document the RAG pipeline shape before any ingestion code is written. The following sub-decisions feed into the overall retrieval architecture ADR (ADR-005) and also inform the database schema (ADR-006).

### 3.1 Chunking Strategy

**Questions to answer:**
- How are documents segmented into chunks? (fixed size, recursive character split, structure-aware, semantic boundary detection)
- What is the target token size and overlap per chunk type?
- How are structured elements handled differently? (tables, numbered lists, headers, images)
- What is the minimum viable chunk size below which chunks are discarded or merged?

**Constraint:** The chunking strategy determines the granularity of traceability. INV-EPI-01 requires that every requirement links to at least one chunk — overly large chunks reduce citation precision.

### 3.2 Metadata Schema per Chunk

**Questions to answer:**
- What metadata fields are stored alongside each embedding for filtered retrieval?
- Which fields are mandatory filters on every query (never relaxed)?
- How is the trust tier (from `epistemology.md`) encoded and applied at retrieval time?

### 3.3 Context Assembly

**Questions to answer:**
- How are retrieved chunks ordered before being passed to the synthesis LLM?
- How is the token budget managed when retrieved context is large?
- How is the prompt structured to separate system instructions, schema definitions, source context, and the user query?
- Which parts of the prompt are candidates for LLM-provider-level prompt caching?

---

## 4. Project Scaffolding

The team must agree on and implement the following structural elements before Sprint 1 begins. The specific directory layout is a Sprint 0 deliverable, not a Sprint 0 pre-decision.

### 4.1 Required Top-Level Structure

The scaffold must include, at minimum:

- Application source directory with clear separation between: API layer, agent/orchestration layer, RAG pipeline components, ORM models, Pydantic schemas, and shared services
- Database migrations directory (managed by the chosen migration tool)
- Test directory with separate folders for unit, integration, and evaluation tests
- Infrastructure-as-code directory
- CI/CD workflow configuration
- Local development environment configuration (e.g., Docker Compose)

### 4.2 Required Configuration Patterns

- All secrets and environment-specific values in environment variables, never hardcoded
- A settings file (backed by environment variables) that exposes all configurable values with type validation
- A `.env.example` file documenting every required environment variable with a description and example value

---

## 5. Invariant Verification Tests

Sprint 0 must produce automated tests that verify the structural scaffolding of four critical invariants. These tests use a real database (not mocks) and must pass in CI.

| Test | Invariant Verified | What it proves |
| :--- | :--- | :--- |
| Tenant isolation test | INV-SEC-01 | A query executed in Tenant B's session returns 0 rows from Tenant A's data |
| No floating model alias test | INV-MODEL-03 | No model ID in the codebase contains a floating alias (e.g., `-latest`) |
| Grounding invariant test | INV-EPI-01 | Every requirement produced by a synthesis agent has a non-empty `source_chunks` array pointing to active DB records |
| Human override immutability test | INV-HITL-01 | A human-approved requirement description is unchanged after re-running synthesis on the same source documents |

---

## 6. Sprint 0 Deliverables

| # | Deliverable | Acceptance Criteria |
| :--- | :--- | :--- |
| D-01 | ADRs 001–015 covering all decision areas in Sections 1 and 2 | Each ADR has Status, Context, Decision, and Consequences sections; all merged to `main` |
| D-02 | Interface inventory reviewed and sprint assignment confirmed for all 26 interfaces in Section 2.7 | All interfaces have a confirmed sprint assignment and owner; MVP connector set agreed |
| D-03 | Dependency manifest with all production and dev dependencies pinned to exact versions | No unpinned dependencies; `install` reproduces a deterministic environment |
| D-04 | Database migration covering all entities in `ontology.md` | Migration runs `upgrade` and `downgrade` cleanly on a fresh database; RLS enabled on all tenant tables |
| D-05 | LangGraph graph skeleton with typed state and stub nodes for each agent role | Graph executes end-to-end with static mock payloads; state transitions are observable in traces |
| D-06 | API skeleton with authentication middleware and tenant context injection | JWT middleware rejects requests missing required claims; a `GET /health` endpoint returns 200 |
| D-07 | 4 invariant integration tests | All 4 pass in CI against a real database |
| D-08 | CI/CD pipeline running on every PR | Lint → type check → unit tests → integration tests → build; failing pipeline blocks merge |
| D-09 | Observability connected to staging environment | At least one test trace visible with `tenant_id` and `project_id` span metadata |
| D-10 | Staging environment deployed and reachable | Application health check returns 200 from the staging load balancer |
| D-11 | Evaluation dataset: 3–5 historical requirement packages in structured JSON | Each file has `source_documents`, `ground_truth_requirements`, and `human_notes` fields |
| D-12 | `CLAUDE.md` onboarding guide at repo root | A new engineer can run local dev environment from scratch using only this guide |

---

## 7. Definition of Done

Sprint 0 is complete when **all** of the following are true:

- [ ] All 15 ADRs (ADR-001 through ADR-015) are written, reviewed, and merged to `main`
- [ ] All 12 deliverables (D-01 through D-12) are merged to `main`
- [ ] CI pipeline is green on `main`
- [ ] All 4 invariant tests pass in CI
- [ ] Staging environment is reachable and returning healthy responses
- [ ] At least one test trace is visible in the observability tool with correct tenant and project metadata
- [ ] No floating model alias exists anywhere in the codebase
- [ ] Strict type checking passes with 0 errors
- [ ] All team members can run the local development environment from scratch

---

> End of Sprint 0 Plan • Chitragupt • v5.0 • May 2026
