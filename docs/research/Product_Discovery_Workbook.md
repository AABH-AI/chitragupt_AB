# PRODUCT DISCOVERY WORKBOOK: Business Requirement Analyzer (BRA)

**Subtitle:** First-Principles Sprint Planning & Stakeholder Questionnaire

## Document Info

| Details | Value |
| :--- | :--- |
| **Phase** | Product Discovery & Sprint Definition |
| **Version** | 2.0 — Expanded |
| **Audience** | Product Managers, Stakeholders, Solutions Architects, Engineering Leads |
| **Purpose** | To define the ontological foundations, system invariants, technology selections, budget constraints, and functional queries required to confidently plan the first six engineering sprints. |

---

## PURPOSE

This document serves as the primary artifact for the **Discovery Phase** of the Business Requirement Analyzer (Chitragupt). Before defining user-facing features, the product team must align with stakeholders on the *first principles* of the system: its ontology (what concepts exist), its invariants (what must always be true), its technology selections (what we build on), its cost model (what we can afford), and its boundaries (what the system will explicitly not do).

This approach ensures that initial sprints build a resilient, structurally sound data model and knowledge graph before layering on the agentic orchestration.

---

## 1. First Principles Definition (Sprints 0–1 Focus)

The earliest sprints must focus on establishing the "ground truth" architecture. The following areas need immediate stakeholder consensus.

### 1.1 Ontology (Entities & Relationships)

We must define the structural grammar the LLM will use to understand business requirements.

| Entity Type | Definition Needed from Stakeholders |
| :--- | :--- |
| **Requirement Objects** | How do we categorize inputs? (Functional, Non-Functional, Constraint, Assumption, Compliance). Are there domain-specific sub-types? |
| **Actors & Roles** | Who are the entities interacting with the requirements? (Admin, Client, System, Third-Party API). Are there domain-specific actors (e.g., "Cardholder" in fintech)? |
| **Traceability Nodes** | How do we define a "source"? Is a Slack thread treated the same as a PDF document? Is a chat elicitation answer considered primary or secondary source? |
| **Output Artifacts** | What constitutes a "Specification"? Is it a monolithic document, or a collection of Epics and Stories? What is the mandatory schema for each requirement? |
| **Domain Templates** | Which industry verticals need pre-built templates on Day 1? What are the mandatory sections and completeness checklists per domain? |

### 1.2 System Invariants (The "Unbreakables")

Invariants are rules that must hold true at all times regardless of the state of the system.

- **Traceability Invariant:** Every generated requirement **must** map to at least one ingested source chunk. Zero-shot ungrounded generation is prohibited.
- **Conflict Non-Resolution Invariant:** Contradicting sources of equal trust tier must surface a Conflict Flag for human resolution — never auto-resolved.
- **Tenant Isolation Invariant:** Embeddings and chunks from Client A cannot be retrieved during a Client B session under any circumstances.
- **Human Override Invariant:** A human reviewer's explicit edit is the absolute ground truth and cannot be overwritten by subsequent re-generation.
- **Budget Cap Invariant:** Agent processing must halt and alert the owner before exceeding a configured cost cap.
- **Model Version Pinning Invariant:** Production LLM calls must use pinned model versions; floating aliases are prohibited.

See `invariants.md` for the complete, binding list of invariants.

### 1.3 Boundary Constraints

What the system is *not* responsible for in Phase 1:

- It will **not** automatically execute code or deploy infrastructure.
- It will **not** generate UI/UX wireframes.
- It will **not** handle real-time synchronous voice transcriptions.
- It will **not** push specifications to Jira or Confluence without explicit human approval.
- It will **not** generate cost estimates or effort sizing.
- It will **not** auto-resolve conflicts between contradicting requirements.

---

## 2. Stakeholder Discovery Questionnaire

Product teams should use these specific queries during stakeholder interviews to extract the necessary requirements for Sprint Planning. Each section should be run as a structured 45–60 minute workshop session with the relevant stakeholders.

---

### Section A: Ontological & Data Questions

> *Goal: Understand the shape of the data before designing the vector schema and database models.*

**A1. Taxonomy:** When your team writes a specification today, what are the absolute mandatory fields? (e.g., ID, Priority, Description, Acceptance Criteria, Source, Affected Actor)

**A2. Definition of Done:** What makes a requirement "complete"? Which of these are mandatory for every requirement?

- At least one positive acceptance criterion
- At least one negative acceptance criterion
- Edge case scenario
- Priority (MoSCoW)
- Source citation
- Performance target (for NFRs)

**A3. Data Hierarchy:** Do requirements map one-to-one to Epics? Or can one requirement spawn multiple User Stories? Do you use a standard hierarchy (Theme → Epic → Story → Task)?

**A4. Non-Functional Requirements:** How does your team currently handle NFRs? Are they standalone requirements or attached to functional requirements?

**A5. Requirement Identity:** What is your naming convention for requirements? (e.g., `FR-001`, `US-1234`, or free-form). Should the system generate IDs, or follow an existing scheme?

---

### Section B: Ingestion & Boundary Questions

> *Goal: Understand what the Ingestion Agent must support on Day 1.*

**B1. Format Prioritization:** If you could only support 3 input formats for the MVP, what are they? Please rank in order of business impact:

- PDF documents
- DOCX files
- Free-text chat (elicitation)
- Jira epic/issue links
- Confluence page URLs
- Excel/spreadsheet requirement matrices
- Notion pages
- Plain text

**B2. Volume:** What is the average size of a requirements dump?

- Small: 1–10 pages / 1–3 documents
- Medium: 10–50 pages / 3–10 documents
- Large: 50–200 pages / 10–30 documents
- XL: 200+ pages / 30+ documents

**B3. Staleness:** If a Confluence page changes *after* it has been ingested, should the system:

- Automatically detect the change and re-ingest?
- Notify the BA and wait for manual re-ingest?
- Ignore it (BA is responsible for re-uploading)?

**B4. Multimedia:** Will the system be required to extract requirements from diagrams, images, or audio recordings in Phase 1?

**B5. Sensitive Data:** Will any requirement documents contain PII, PHI, or financial secrets? If so, what is the handling policy?

---

### Section C: Agentic Behavior & Human-in-the-Loop

> *Goal: Define the guardrails for the LLM and the human review workflow.*

**C1. Confidence Thresholds:** If the AI is only 70% confident in a synthesized requirement, should it:

- Include it with an `[INFERRED]` tag and surface it as a flagged item?
- Omit it entirely and raise it as an Open Question for the user to clarify?
- Ask the user a targeted clarifying question in the chat before including it?

**C2. Elicitation Style:** How proactive should the Elicitation Agent be?

- Ask all gap questions in a numbered list at once
- Ask one question at a time, sequentially
- Only ask questions for gaps that affect "must have" requirements

**C3. Output Delivery:** How do you want the final document delivered?

- Live preview that streams as it generates
- Single generation then display (user waits for complete output)
- Background job with email notification when ready

**C4. Review Workflow:** Who reviews the AI-generated spec, and in what sequence?

- BA reviews first → PM approves → client receives clean version
- BA reviews → client reviews and comments → BA finalizes
- Single-reviewer (BA is the only reviewer and approver)

**C5. Conflict Resolution:** When two sources contradict each other, how should the UI present this?

- Side-by-side view of the two conflicting excerpts with resolution options
- Simple alert with links to both sources
- Email/Slack notification asking for resolution

---

### Section D: AI Model & Technology Questions

> *Goal: Establish technology constraints and preferences before architecture decisions are made.*

**D1. LLM Provider Requirement:** Does the organization have a contract, preference, or compliance requirement for a specific LLM provider?

- Existing Azure OpenAI Service subscription (enterprise agreement)
- Preference for Anthropic Claude
- Must use open-source / self-hosted models (Llama 3) due to data classification
- No preference — evaluate on quality and cost

**D2. Deployment Model:** Where must the system run?

- Chitragupt-managed SaaS (data leaves the organization's network)
- Customer-hosted (Chitragupt stack deployed in our cloud account)
- On-premise / air-gapped (no external API calls permitted)

**D3. Vector Store Preference:** Does the team have a preference or constraint on the vector database?

- Pinecone (SaaS, managed, simplest to start)
- Qdrant (self-hosted or managed, high performance)
- pgvector (PostgreSQL extension, already in use)
- No preference

**D4. Existing Data Infrastructure:** What databases and data platform tools does the engineering team already operate?

- This informs whether pgvector (reuse existing PostgreSQL) is preferred over a separate vector store.

**D5. Agentic Framework:** Does the engineering team have a preference or existing expertise in an agentic framework?

- LangGraph (Python, stateful, recommended)
- CrewAI
- Custom state machine
- No preference

---

### Section E: Budget & Cost Questions

> *Goal: Establish cost constraints that will drive architecture decisions on model selection, caching, and processing mode.*

**E1. Per-Project Cost Tolerance:** What is the maximum acceptable LLM API cost per requirements analysis run?

- Under $1 (requires aggressive caching and model tier optimization)
- $1–$5 (allows quality-tier models with caching)
- $5–$20 (allows premium-tier for complex conflict resolution)
- Not constrained — prioritize quality

**E2. Monthly Infrastructure Budget:** What is the total monthly infrastructure budget?

- Under $500 (managed services, shared infrastructure)
- $500–$2,000 (dedicated instances, managed vector store)
- $2,000–$10,000 (multi-AZ, high availability)
- Over $10,000 (enterprise scale)

**E3. Budget Alerting:** Who should receive alerts when cost thresholds are reached?

- Project owner at 80% of project budget cap
- Workspace admin at 80% of monthly cap
- Finance/Ops team at 100% of monthly cap

**E4. Open-Source vs. Managed Services:** Is there a preference for open-source tooling to reduce vendor license costs (e.g., Qdrant self-hosted vs. Pinecone managed)?

---

### Section F: Deployment, Compliance & Security Questions

> *Goal: Surface blockers that require compliance certifications or data residency constraints before the system can be sold to specific customer segments.*

**F1. Data Classification:** At what level are client requirement documents classified?

- General / Public (no restrictions)
- Confidential / Internal (standard encryption; no external sharing)
- Restricted / Sensitive (SOC 2 required; DPA needed)
- Highly Restricted / Regulated (HIPAA / FedRAMP required)

**F2. Geographic Residency:** Are any clients in the EU or subject to GDPR?

- If yes, EU-region infrastructure and a DPA are mandatory before ingesting their data.

**F3. SSO Requirement:** Is SSO required for enterprise customers?

- SAML 2.0
- OIDC (Google, Microsoft, Okta)
- Both
- Not required for Phase 1

**F4. Audit & Compliance Reporting:** Is a downloadable audit trail report required for SOC 2 or ISO 27001 evidence?

**F5. Retention Policy:** How long must requirement documents and generated specifications be retained?

- 30 days
- 90 days (default)
- 1 year
- 7 years (regulated / legal archiving)

---

## 3. Technology Evaluation Matrix

Before Sprint 0, the engineering team must evaluate and select from the following options. This matrix should be completed and signed off by the tech lead before any code is written.

| Category | Option A | Option B | Option C | Selected | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **LLM (Quality tier)** | Claude Sonnet 4.6 | GPT-4o | Gemini 1.5 Pro | TBD | |
| **LLM (Fast tier)** | Claude Haiku 4.5 | GPT-4o-mini | Llama 3.1 8B | TBD | |
| **LLM (Premium tier)** | Claude Opus 4.7 | o1 (OpenAI) | Self-hosted 70B | TBD | |
| **Embedding model** | voyage-large-2 | text-embedding-3-large | BGE-M3 (OSS) | TBD | |
| **Vector store** | Pinecone | Qdrant | pgvector | TBD | |
| **Agentic framework** | LangGraph | CrewAI | Custom | TBD | |
| **API framework** | FastAPI (Python) | Node.js/Express | Django | TBD | |
| **Relational DB** | PostgreSQL | MySQL | SQLite (dev only) | TBD | |
| **Job queue** | BullMQ (Redis) | Celery + Redis | AWS SQS | TBD | |
| **Auth** | Auth0 | Clerk | Supabase Auth | TBD | |
| **File storage** | AWS S3 | Azure Blob | GCS | TBD | |
| **Observability** | Langfuse | LangSmith | Custom (OTEL) | TBD | |
| **Re-ranker** | Cohere Rerank v3 | ColBERT | FlashRank (OSS) | TBD | |

---

## 4. MVP Definition Criteria

Before Sprint 1 begins, the team must agree on the Minimum Viable Product definition. The MVP is the smallest, most useful version of the system that a BA can use to generate a real specification for a real project.

### MVP Must-Have Features

- [ ] File upload: at least PDF and DOCX
- [ ] Free-text chat elicitation
- [ ] Document ingestion → chunking → embedding → vector storage
- [ ] Synthesis agent generates requirement drafts from retrieved chunks
- [ ] Confidence scoring and `[INFERRED]` tagging
- [ ] Gap detection with Open Questions list
- [ ] Conflict detection (flag only; no auto-resolution)
- [ ] Specification document generation in Markdown format
- [ ] Traceability: each requirement linked to source chunk
- [ ] Human review: approve / reject / edit individual requirements
- [ ] Export to Markdown file (download)
- [ ] Tenant-isolated vector store
- [ ] Basic user auth (email/password)
- [ ] Per-project cost tracking and basic budget cap

### MVP Nice-to-Have (Phase 1.1)

- [ ] DOCX export
- [ ] Jira read integration
- [ ] Confluence read integration
- [ ] Domain template selection at project creation
- [ ] SSO (SAML/OIDC)
- [ ] Real-time streaming spec preview

### Explicitly Out of MVP

- Jira write (ticket creation from spec)
- Confluence write (page publish)
- Audio/video ingestion
- Multi-language support
- Fine-tuning
- Effort estimation
- Automated spec approval workflows

---

## 5. Recommended Sprint Phasing

### Sprint 0: Foundation, Ontology & Technology Selection (2 weeks)

**Objective:** Finalize all technology selections, data models, and system invariants. No production code — spikes and decisions only.

**Key Deliverables:**

- Technology Evaluation Matrix completed and signed off.
- Database schema for all entities (see `ontology.md` for full schema).
- Vector store namespace strategy and metadata schema documented.
- Embedding strategy confirmed (model, chunk size, overlap, hybrid search).
- Tenant isolation design reviewed and security-approved.
- Evaluation dataset assembled: 5–10 historical requirements packages with accepted spec outputs as ground truth.
- CI/CD pipeline and observability (Langfuse) scaffolding deployed.
- All blocking unknowns from `unknowns_and_stakeholder_queries.md` Section 1–4 resolved.

**Definition of Done:** Tech stack selected; database migrations written; vector namespace provisioned; ground truth dataset available; all INV-SEC-* invariants have a testable verification plan.

---

### Sprint 1: Core Ingestion & Retrieval — The RAG Baseline (2 weeks)

**Objective:** Build the pipeline that turns files into searchable, traceable knowledge. No LLM synthesis yet.

**Key Deliverables:**

- Document Parser: PDF, TXT, DOCX.
- Semantic chunker (target: 300–600 tokens, 15% overlap).
- Embedding generation pipeline (selected embedding model).
- Chunk writing to tenant-isolated vector store with full metadata envelope.
- Metadata storage to PostgreSQL (Document, Chunk, Project, Workspace entities).
- Semantic search API: query → retrieve top-K chunks with scores → return with metadata.
- Deduplication: file hash-based check before re-embedding.
- Ingestion status tracking (pending → processing → indexed / failed).
- Basic file upload UI (no chat yet).
- Audit log for document ingestion events.
- Cost log for embedding API calls.

**Performance Target:** Ingest and embed a 50-page PDF in < 60 seconds.

**Quality Gate:** Retrieval precision@5 ≥ 0.70 on the evaluation dataset before Sprint 2 begins.

---

### Sprint 2: Synthesis & Elicitation — The Agentic Layer (2 weeks)

**Objective:** Introduce the LLM to reason over retrieved chunks and generate a requirements draft.

**Key Deliverables:**

- LLM model router (fast / quality / premium tiers) with fallback chain.
- Prompt caching implementation for agent system prompts.
- Synthesis Agent: retrieves chunks → drafts requirements with confidence scores.
- Elicitation Agent: identifies gaps in ingested content → generates clarifying questions in chat.
- Classification Agent: classifies each requirement (Functional / NFR / Constraint / Assumption).
- Confidence scoring and tier assignment (`explicit`, `synthesized`, `inferred`, `speculative`).
- Conflict Detection Agent: identifies contradicting chunks → creates Conflict objects.
- Gap Detection Agent: runs spec against domain completeness checklist → creates Gap objects.
- All invariants INV-EPI-01 through INV-EPI-04 implemented and unit-tested.
- Per-project LLM cost tracking (LLMCallLog entity writing).
- Budget cap enforcement (INV-COST-01).
- Chat UI (elicitation interface).

**Quality Gate:** End-to-end test using evaluation dataset: ≥ 80% of human-validated requirements present in draft; ≤ 15% false positives (non-requirements flagged as requirements).

---

### Sprint 3: Output & Review Loop (2 weeks)

**Objective:** Assemble the final specification document and implement the human review cycle.

**Key Deliverables:**

- Specification Writer Agent: assembles requirements into structured document using domain template.
- Domain template library (at least 1 general template; 1 domain-specific template).
- Spec preview UI: collapsible sections, confidence badges, citation viewer.
- Human review toolbar: Approve / Reject / Edit / Request Re-generation per requirement.
- Inline comment capability on requirements.
- Human override enforcement (INV-HITL-01): approved requirements cannot be overwritten by re-generation.
- Re-generation scoped to flagged sections only (INV-HITL-03).
- Conflict resolution UI: side-by-side source comparison with Accept A / Accept B / Clarify.
- Open Questions list with assignment and status tracking.
- Version history for requirements (RequirementVersion entity).
- Markdown export (download).
- Spec Lock action: moves spec to `locked` status; triggers `spec.completed` webhook.
- Audit trail for all human review actions.
- Streaming spec preview (INV-UX-02).

**Quality Gate:** Stakeholder acceptance rate ≥ 75% on evaluation dataset specs (measured by domain expert review panel).

---

### Sprint 4: Integrations & Export (2 weeks)

**Objective:** Connect the system to the tools where requirements already live, and expand export options.

**Key Deliverables:**

- Jira read integration: OAuth flow, epic/issue ingestion, pagination handling.
- Confluence read integration: OAuth flow, page URL ingestion, HTML-to-text normalization.
- Linear read integration: GraphQL API, issue/project ingestion.
- DOCX export (using a DOCX template with all requirement fields, confidence tags, citations).
- PDF export.
- Traceability Matrix export (CSV).
- Outbound webhooks: `spec.completed`, `conflict.raised`, `gap.raised`, `requirement.approved`.
- Rate limit handling for Jira/Confluence API (exponential backoff, retry logic).
- Document staleness detection: webhook listener for Confluence/Jira update events.

**Quality Gate:** Jira ingestion of a 20-epic project completes in < 5 minutes without hitting rate limits; DOCX export matches Markdown content 1:1.

---

### Sprint 5: Security, Compliance & Multi-Tenancy Hardening (2 weeks)

**Objective:** Harden the system for production security, compliance readiness, and multi-tenant scale.

**Key Deliverables:**

- PostgreSQL Row-Level Security (RLS) enabled for all tenant-scoped tables.
- Penetration test (OWASP Top 10 scope) — commission external party.
- Prompt injection containment (INV-SEC-05) — validation and automated test suite.
- PII detection and redaction pipeline (INV-SEC-02) — integrated into ingestion before embedding.
- GDPR right-to-erasure endpoint: cascade delete from vector store, PostgreSQL, and file storage.
- Audit log immutability enforcement (INV-SEC-04).
- File storage isolation (INV-SEC-03) — path policy audit and automated verification.
- SSO: SAML 2.0 and OIDC integration (Auth0 or Clerk).
- Data residency routing: EU-region endpoint for EU-flagged workspaces.
- SOC 2 Type II audit scope documentation — evidence collection for logging and access controls.
- Security headers (HSTS, CSP, X-Frame-Options) on all API responses.
- Rate limiting: API key and session-level rate limits.

**Quality Gate:** Third-party pen test report with no Critical findings; RLS verification test passes for 100% of cross-tenant query scenarios.

---

### Sprint 6: Performance Optimization, Observability & GA Readiness (2 weeks)

**Objective:** Optimize system performance, establish production observability, and validate against acceptance criteria before General Availability.

**Key Deliverables:**

- Langfuse (or LangSmith) integration for full LLM trace capture: agent name, model, tokens, latency, cost, cache hit.
- Retrieval precision@5 measurement dashboard — ongoing evaluation against ground truth.
- Semantic cache implementation: reduce redundant retrievals for repeated queries.
- Parallel agent execution for Gap Detection + Conflict Resolution (LangGraph `Send` API).
- Async processing pipeline for large documents (> 20 pages): BullMQ job queue + WebSocket progress.
- P50/P95/P99 latency dashboards per operation (ingestion, synthesis, full spec generation).
- Cost per project dashboard for workspace admins.
- Alert system: budget cap alerts, LLM provider failure alerts, queue depth alerts.
- Load testing: simulate 50 concurrent project processing runs; validate latency SLAs.
- Calibration evaluation: Brier Score < 0.15, ECE < 0.10 on evaluation dataset.
- Full QA regression against all sprint deliverables.
- Customer-facing documentation: API reference, integration guides, onboarding guide.
- In-app onboarding: sample project walkthrough, contextual tooltips, guided mode.

**Quality Gate:** All success metrics from BRA_Research_Document.md Section 14 met or exceeded. P95 spec generation latency < 10 minutes. Retrieval precision@5 ≥ 0.75. Per-project cost < $2.00 (pre-optimization) / < $0.75 (post-caching).

---

## 6. Risk Register for Discovery Phase

| Risk | Likelihood | Impact | Owner | Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| Blocking unknowns not resolved before Sprint 1 | High | High | PM | Time-box stakeholder workshops; escalate blockers to executive sponsor |
| Technology evaluation spike reveals no viable option | Low | High | Tech Lead | Evaluate ≥ 2 options per category; have fallback ranked |
| Evaluation dataset not available by Sprint 0 end | Medium | High | PM + BA | Identify 3 BAs who will contribute 2 historical projects each |
| Budget constraints force model downgrade | Medium | Medium | PM + Finance | Model tier analysis in Sprint 0 spike; confirm cost tolerance in Section E interviews |
| Compliance requirement discovered after architecture is set | Medium | High | PM + Legal | Run Section F questionnaire before any architecture decisions |
| Stakeholder availability for Section A–F workshops | High | Medium | PM | Book workshops as first action; define async fallback (written questionnaire) |

---

> End of Discovery Workbook • Chitragupt • v2.0 • May 2026
