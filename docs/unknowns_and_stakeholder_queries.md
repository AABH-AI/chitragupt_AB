# Unknowns & Stakeholder Input Requirements

**Phase:** Product Discovery
**Version:** 2.0 — Expanded (Client Approved & Answered)
**Purpose:** To aggregate all unknown variables, edge cases, open architectural questions, and critical stakeholder queries, populated with client responses. Each section represents a resolved domain of unknowns that the BA and system architect teams can use to commit to Sprint deliverables.

---

## How to Use This Document

Each section represents a domain of unknowns. For each question:

- **Why it matters** states the risk of proceeding without an answer.
- Questions marked **[BLOCKING]** cannot be deferred — they must be resolved before Sprint 1 begins.
- Questions marked **[SPRINT 2+]** can be deferred but must be scheduled for resolution before the relevant feature is built.
- Questions marked **[NICE TO KNOW]** are low-risk to defer.

---

## 1. Input & Ingestion Unknowns

Before the ingestion pipeline is built, the following must be established:

### 1.1 Volume & Scale [BLOCKING]

**Question:** What is the maximum size of a single requirements dump expected in Phase 1?

- Sub-question A: Is a 5-page PDF typical, or are 200–500-page legacy system manuals expected?
- Sub-question B: What is the expected number of documents per project (e.g., 3 docs, or 30 docs)?
- Sub-question C: What is the maximum project corpus size in tokens?

**Why it matters:** Chunking strategy, vector store capacity planning, and the decision between sync vs. async processing pipelines all depend on this. A 5-page PDF is sync-capable in < 15 seconds. A 500-page manual needs background processing, a job queue, and progress notifications.

**Client Response & Decision:**

- **Sub-question A (Typical vs. Max Size):** A typical upload will consist of 10–50 page documents (such as RFPs, business requirement specifications, and product briefs). However, the system must support legacy manuals running up to **150–200 pages** as an upper limit. For Sprint 1, the architecture must support an **asynchronous background processing pipeline** with a job queue and progress status notification for any document exceeding 30 pages. Documents under 30 pages can be processed in a synchronous fashion but with a clear loading indicator.
- **Sub-question B (Documents per Project):** A typical project corpus will consist of **3 to 10 source documents** (e.g., 1 RFP, 2 specifications, 3–4 meeting transcripts, and a couple of slack/chat export files). We do not expect 30+ documents per project on Day 1; let's establish 10 documents as the MVP ingestion ceiling.
- **Sub-question C (Max Corpus Tokens):** The maximum active corpus size per project in Phase 1 should be budgeted at **250,000 to 300,000 tokens** (approximately 500 pages of text). The RAG architecture must be designed to fetch precise contexts from this corpus rather than overloading LLM context windows, which will help us keep operational costs low and guarantee high semantic retrieval precision.

---

### 1.2 Format Priority [BLOCKING]

**Question:** If the MVP can only support 3 input formats, which must be included on Day 1?

Proposed ranking for discussion:

1. PDF (most common for formal requirements)
2. Free-text chat (core elicitation UX)
3. DOCX (widespread in enterprise)
4. Jira/Linear links (structured, already ticketed projects)
5. Confluence URL (common internal documentation)

**Why it matters:** Each format requires a different parsing strategy. PDF requires OCR for scanned documents; Jira requires API authentication and pagination; Confluence requires HTML-to-text normalization. Supporting all 5 from Day 1 triples ingestion complexity.

**Client Response & Decision:**

We approve the proposed ranking with **PDF, Microsoft Word (DOCX), and Free-text chat (Elicitation UX)** as our mandatory Day 1 formats.

- **PDF Ingestion:** Must support high-fidelity text extraction and basic tabular data parsing. Scanned PDFs requiring full visual OCR can be deferred to Sprint 2 as a stretch goal, but standard text-based PDFs must work flawlessly on Day 1.
- **DOCX Ingestion:** Since many of our legacy system specs are structured as MS Word templates, a clean XML/text extraction pathway is mandatory.
- **Free-text chat:** This is the heart of the active elicitation cycle and must stream directly into the active session state.
- **Jira/Confluence integrations** are highly valuable but are officially deferred to **Sprint 4**.

---

### 1.3 Multimedia Inputs [SPRINT 2+]

**Question:** Will the system be expected to extract meaningful requirements from:

- Architecture diagrams embedded in PDFs or uploaded as images?
- Audio recordings of stakeholder meetings?
- Short video walkthroughs of existing systems?

**Why it matters:** Each multimedia type requires a specialized extraction path. Image analysis requires a vision-capable LLM (cost uplift ~$0.002/image). Audio requires Whisper transcription (cost: ~$0.006/minute). If these are not Day 1 requirements, they can be excluded from the ingestion architecture entirely for Sprint 1.

**Client Response & Decision:**

- **Architecture Diagrams / Images:** **High Priority for Sprints 2–3**. Our requirement specifications frequently contain visual flowcharts, database schemas, and system topology diagrams. The system must support extracting these using vision-capable LLMs (e.g., Claude 3.5 Sonnet / GPT-4o Vision). In accordance with **INV-EPI-06**, any requirement synthesized from a visual extraction must carry the `[VISUAL EXTRACTION — VERIFY]` tag and have its confidence score capped at 0.80.
- **Audio Recordings:** **Moderate Priority, deferred to Sprint 3/4**. We record workshops, but a post-meeting Whisper-to-text transcription step is acceptable.
- **Video Walkthroughs:** **Out of Scope**. We will not require video analysis in Phase 1 or 2.
- *System Architect Guidance:* The database schema developed in Sprint 1 must support the `visual_extraction` source type and metadata fields for image storage paths (**INV-SEC-03**), but the active visual parsing execution pipeline should be kept out of the Sprint 1 MVP build.

---

### 1.4 Document Update & Versioning Policy [BLOCKING]

**Question:** If a source document (e.g., a Confluence page) is updated after it has been ingested, what should the system do?

Options for stakeholder to choose:

- **A. Manual re-ingest:** Require the BA to explicitly re-upload the updated document. System does not auto-detect changes.
- **B. Auto re-ingest on change:** System polls linked URLs or listens to webhooks; automatically re-ingests when the source changes and flags affected requirements for re-review.
- **C. Notify only:** System detects the source has changed and notifies the BA; re-ingest is manual but prompted.

**Why it matters:** Option A is simplest to build in Sprint 1. Option B requires webhook integrations and a diffing pipeline. The wrong choice creates confusion when stakeholders update documents mid-project.

**Client Response & Decision:**

We select **Option C (Notify only)**.

- *Rationale:* Option B (Auto re-ingest) creates significant risks of automatically overwriting human-validated requirements or invalidating active session states mid-synthesis, directly violating our **Human Override Invariant (INV-HITL-01)**. Option A is too passive and could lead to stale data being used to build engineering specs.
- *Implementation Details:* The system must detect a mismatch (via file hash comparison on manual uploads, or metadata modification timestamps on connected integrations) and raise a **Staleness Alert** in the UI. The BA is notified: *"Source Document X has been modified. Would you like to re-ingest?"* If the BA clicks confirm, the system tombstones the old chunks (`is_active = false`, `valid_until = NOW()`) in accordance with **INV-VER-03** and embeds the new version, prompting a scoped re-review of any requirements linked to the old chunks.

---

### 1.5 Deduplication Policy [SPRINT 2+]

**Question:** If the same document (or a very similar one) is submitted twice — either by the same user or across different projects — what should happen?

- Silently deduplicate (one set of chunks serves both)?
- Re-embed separately (simpler, slight cost duplication)?
- Warn the user that a near-duplicate was detected?

**Why it matters:** Determines whether hash-based deduplication is a Day 1 feature or a Phase 2 optimization.

**Client Response & Decision:**

The system must **warn the user that a near-duplicate was detected** and provide a choice:

1. *Replace/Update:* Supersede the existing document (triggering the tombstone and version upgrade workflow).
2. *Keep Both:* Allow separate ingestion (treating them as distinct baselines, which is common in milestone tracking).
3. *Cancel:* Halt the ingestion.

- *Sprint 1 Baseline:* Implement simple **SHA-256 file hash-based deduplication** at the project level. If a user attempts to upload a file with an identical hash to an active document in that specific project, block the upload and display a warning. Cross-tenant sharing or deduplication is strictly prohibited due to our **Tenant Isolation Invariant (INV-SEC-01)**.

---

### 1.6 Language & Localization [SPRINT 2+]

**Question:** Will the system need to process requirements documents in languages other than English?

- If yes, which languages are priority (e.g., Spanish, French, German, Arabic)?
- Should the output specification be in the same language as the input, or always in English?

**Why it matters:** Multilingual support requires a multilingual embedding model (e.g., BGE-M3) rather than English-optimized models. The Elicitation Agent's chat prompts must be translated or templated in the target language. This is a significant scope expansion if not planned from the start.

**Client Response & Decision:**

- **Sprints 1–3 Scope:** **English-only processing is acceptable** to keep prompt engineering and token consumption highly optimized.
- **Architectural Guardrail:** To prevent an expensive index migration later, the System Architect team must select a high-performance multilingual embedding model (e.g., `text-embedding-3-large` or `BGE-M3` with 1536 dimensions) for Sprints 1–3. This ensures that when we add European localization in Sprint 4+, we do not have to rebuild our historical database.
- **Output Policy:** The generated specification document must **always be written in English**, regardless of the language of the source inputs.

---

## 2. Output & Formatting Requirements

Before the Specification Writer Agent is designed:

### 2.1 Definition of "Done" for a Specification [BLOCKING]

**Question:** What exactly constitutes a "complete" specification for your team? Which of the following are mandatory for every requirement in the final spec?

- [ ] Functional description text
- [ ] At least one positive acceptance criterion (Gherkin Given/When/Then)
- [ ] At least one negative acceptance criterion
- [ ] Edge case test scenarios
- [ ] Assigned priority (MoSCoW)
- [ ] Linked source citation
- [ ] Affected actor/persona
- [ ] Dependency on other requirements
- [ ] Performance SLA (for NFRs)

**Why it matters:** The Gap Detection Agent's completeness checklist is derived directly from this definition. If the definition is wrong, the agent will flag false gaps (annoying) or miss real gaps (dangerous).

**Client Response & Decision:**

The mandatory criteria for a requirement to be marked "done" in our final specification are:

- [x] **Functional description text** (clear, unambiguous requirement statement).
- [x] **At least one positive acceptance criterion** (written in Gherkin BDD format).
- [x] **At least one negative acceptance criterion** (to guard against error states/misuse).
- [x] **Assigned priority (MoSCoW)** (Must, Should, Could, Won't).
- [x] **Linked source citation** (traceable to an active vector chunk as per **INV-EPI-01**).
- [x] **Affected actor/persona** (must map to a validated System/Human Actor).
- [x] **Performance SLA / Metric** (mandatory *only* for Non-Functional Requirements, such as API latency limits).

*Deferred to Nice-To-Have:* "Edge case test scenarios" and "Dependency on other requirements" are highly valued but should not be marked as blocking completeness checklist failures in Phase 1.

---

### 2.2 Export Destinations [BLOCKING]

**Question:** Where does the final specification need to land? (Select all applicable)

- [ ] Downloadable Markdown file
- [ ] Downloadable Word Document (DOCX)
- [ ] Downloadable PDF
- [ ] Pushed directly to Jira as Epics and Stories
- [ ] Published to a Confluence page
- [ ] Emailed to stakeholders
- [ ] Delivered via API (JSON payload to your own system)

**Why it matters:** Each destination requires a different output module. Jira push requires OAuth and Epic/Story schema mapping. Confluence push requires page template management. Building all of these in Phase 1 is not feasible — the top 2 must be selected as mandatory.

**Client Response & Decision:**

For the Phase 1 MVP, we require exactly two export options:

1. **Downloadable Markdown (.md) file:** Essential for developer local review, standard version control, and rapid parsing testing.
2. **Downloadable Word Document (.docx) template-based:** Standard format for formal client hand-offs and internal management sign-off.

- **Jira & Confluence Integration Pushes** are deferred to **Sprint 4**.
- **PDF Generation** is deferred; we can easily print-to-pdf from Word/Markdown in the interim.
- **JSON via API** is deferred to Phase 2.

---

### 2.3 Requirement Granularity [BLOCKING]

**Question:** What level of granularity is preferred for the output?

- **Epic-level:** Large, high-level business goals (e.g., "Support payment reconciliation")
- **Feature-level:** Named, scoped capabilities (e.g., "Export reconciliation CSV")
- **User Story-level:** Standard format ("As an [Actor], I want [Feature] so that [Value]")
- **Acceptance Criteria-level:** Gherkin BDD format for each story

**Why it matters:** The Spec Writer Agent's output template and the completeness checklist are calibrated to a specific granularity level. Epic-level specs take fewer tokens (cheaper, faster); story-level specs are more actionable for engineering but take 3–5x more tokens per project.

**Client Response & Decision:**

We require **User Story-level** granularity complete with **Acceptance Criteria-level** Gherkin BDD scenarios.

- *Deep Rationale:* Epic-level or feature-level specifications are too abstract. Our primary goal is to provide engineering teams with highly actionable, "ready-to-code" backlog items. This reduces the manual decomposition effort required by BAs. The system should generate standard Agile User Stories (`"As a [role], I want to [feature] so that [benefit]"`) directly coupled with positive and negative Gherkin scenarios.

---

### 2.4 Traceability Matrix Format [SPRINT 2+]

**Question:** How do stakeholders want to consume the traceability matrix?

- Embedded table within the spec document
- Separate CSV export
- Interactive clickable links in the review UI only

**Why it matters:** Embedded tables in DOCX are complex to generate programmatically. A separate CSV export is simpler but requires a separate download step.

**Client Response & Decision:**

We require a hybrid approach:

1. **Interactive Clickable Links in the Review UI (Primary):** BAs must be able to click any requirements block or Gherkin criteria and immediately see the source document highlighted with the corresponding source chunks and similarity scores.
2. **Embedded Markdown/DOCX Table (Secondary):** A structured table appended to the end of the exported specification, mapping the `Requirement Code` (e.g., `FR-001`) to the `Source Document Name`, `Page Number`, and `Section Heading`.

- *Separate CSV export* is deferred as a nice-to-have.

---

### 2.5 Confidence Tag Display in Exports [BLOCKING]

**Question:** Should confidence tags (`[INFERRED — VERIFY]`, `[SYNTHESIZED]`) appear in the exported DOCX and PDF that is shared with the client?

- **Yes:** Full transparency to the client about what was synthesized.
- **No:** Tags are internal review tools only; the client sees a clean, tag-free document.
- **Configurable per export:** BA can choose whether to include tags in client-facing exports.

**Why it matters:** This is a product positioning decision with significant UX implications. Showing tags to clients sets expectations about AI limitations; hiding them creates a cleaner client experience but reduces transparency.

**Client Response & Decision:**

We select **No (Internal Review Only)** with a future path for **Configurable per export**.

- *Deep Rationale:* During the active draft and review phase, these confidence tags (and the strict compliance checks mandated by **INV-UX-04**) are critical for our internal teams (BAs, SAs) to verify AI inferences. However, when exporting the final, locked specification for client delivery, the document must look polished, professional, and authoritative. Displaying `[INFERRED — VERIFY]` or `[SPECULATIVE]` to our clients would erode trust and lead to unconstructive pushback on the validity of the work.
- *Actionable Requirement:* The export engine must strip these tags by default on final locked specifications, but allow BAs to include them if they explicitly choose to export an "Internal Draft" version.

---

## 3. Human-in-the-Loop & Workflow

### 3.1 The Review Process & Roles [BLOCKING]

**Question:** Who is in the review chain, and in what order?

- Who reviews the AI-generated spec first? (BA? PM? SA?)
- Does the client/stakeholder directly review and edit the AI output, or do they only see the finalized, BA-curated version?
- Is there a multi-stage review (BA reviews → PM approves → SA signs off) or a single-review gate?

**Why it matters:** The review workflow determines the permission model, notification system, and state machine design. A single-stage review is a simpler product. A multi-stage review requires role-based views, conditional approval workflows, and hand-off notifications.

**Client Response & Decision:**

We require a strict **multi-stage review pipeline**:

1. **Primary BA Review:** The Business Analyst runs the initial generation, runs elicitation sessions with stakeholders, resolves conflict flags, edits requirements, and moves the status from `Draft` to `BA Approved`.
2. **Technical SA Verification:** The Solutions Architect reviews Non-Functional Requirements (NFRs), security assertions, and technical constraints to verify architectural feasibility. The SA marks the status as `SA Approved`.
3. **Client Sign-off:** The end-client receives a clean, exported copy. The client has **no direct write access or login access** to the system in Phase 1; all their feedback is gathered out-of-band and updated manually by the BA.

- *Workflow Status States:* Requirements and Specifications must transition through `Draft` ➔ `BA Approved` ➔ `SA Approved` ➔ `Locked (Spec Completed)`.

---

### 3.2 Elicitation Aggressiveness [BLOCKING]

**Question:** How proactive should the Elicitation Agent be in asking clarifying questions?

- **Option A — Batched:** Ask all identified gap questions at once (e.g., a list of 8 questions) so the user can answer efficiently.
- **Option B — Sequential drip:** Ask one question at a time, use the answer to inform the next question. Slower but more conversational.
- **Option C — Threshold-gated:** Only ask clarifying questions for gaps that would affect requirements marked "must have" priority.

**Why it matters:** Option A is simpler to implement but can overwhelm users. Option B requires more complex conversational state management. The choice affects the Elicitation Agent's prompt design and session state schema significantly.

**Client Response & Decision:**

We select **Option A — Batched elicitation**.

- *Rationale:* BAs and project stakeholders find real-time, sequential chat interruptions ("drips") highly distracting and inefficient. They prefer to let the RAG ingestion and analysis run to completion, compile all identified gaps and ambiguities into a structured "Open Questions Checklist" organized by functional category, and address them at their own convenience.
- *Implementation:* The Elicitation Agent should batch gap questions by domain area (e.g., "Gaps in Payment Gateway," "Gaps in User Authentication") and present them as a clean batch in the UI.

---

### 3.3 Conflict Resolution UI [SPRINT 2+]

**Question:** How do stakeholders want to resolve detected conflicts?

- Side-by-side diff view showing both conflicting source excerpts with "Accept A / Accept B / Provide clarification" buttons
- An email or Slack notification with the conflict summary and a link to the resolution UI
- A simple dropdown choice from within the spec document inline

**Why it matters:** The conflict resolution UI is a critical product experience differentiator. A poor conflict UI leads to unresolved conflicts being deferred and requirements remaining in `[CONFLICT — PENDING]` status indefinitely.

**Client Response & Decision:**

We require a **Side-by-side comparison interface** in the review panel.

- *Layout Requirements:*
  - Left side: The conflicting excerpt from Source A (with metadata: date, author, trust tier).
  - Right side: The conflicting excerpt from Source B.
  - Center/Bottom: Option A button, Option B button, or a "Provide Custom Clarification / Manual Override" text box.
- *In accordance with INV-EPI-02 & INV-HITL-04:* The system must never attempt to resolve conflicts autonomously. A human reviewer must explicitly trigger resolution, which instantly cascades to update all affected requirements.

---

### 3.4 Asynchronous Review & Notification [SPRINT 2+]

**Question:** How should stakeholders be notified when the spec is ready for review or when a conflict requires their input?

- In-app notification only (requires user to be logged in)
- Email notification with a direct link
- Slack / Teams message to a configured channel
- All of the above (configurable per workspace)

**Why it matters:** If the review workflow is asynchronous (BA generates spec → client reviews next day), the notification system is critical. Without it, specs sit unreviewed.

**Client Response & Decision:**

- **Phase 1 MVP:** **In-app notifications** and **Email alerts** are mandatory.
- BAs and SAs must receive structured email summaries upon generation completion: *"Chitragupt has completed analysis on project 'Phoenix-Pay'. We generated 15 Requirements, identified 4 Gaps, and flagged 2 Conflicts that require your review."*
- *Slack / Teams integrations* are deferred to Phase 2 (Sprint 4+).

---

## 4. Performance & SLA Expectations

### 4.1 Acceptable Generation Latency [BLOCKING]

**Question:** For a mid-complexity project (3 documents, ~50 pages total), what is the acceptable wait time for the complete specification to be generated?

- **Under 2 minutes** — requires parallel agent execution, potentially higher cost per run
- **2–10 minutes** — allows sequential processing; lower cost; likely requires streaming progress UI
- **Up to 30 minutes** — acceptable as an async background job with email notification on completion
- **Same day** — specification batch processed overnight

**Why it matters:** The latency target determines the architecture (sync vs. async pipeline, parallel vs. sequential agents, streaming vs. bulk delivery). Targeting 2 minutes requires significantly more infrastructure than targeting 30 minutes.

**Client Response & Decision:**

We select **2–10 minutes** as the acceptable baseline target.

- *Deep Rationale:* In traditional workflows, a high-quality requirements specification takes a human BA days to draft. If Chitragupt can perform a thorough multi-agent analysis (Gap detection, conflict checks, and story synthesis) in 5 to 8 minutes, it represents an outstanding productivity gain. We do not want to sacrifice quality or synthesis recall by forcing a sub-2-minute rush.
- *SLA Guardrail:* In accordance with **INV-UX-01 & INV-UX-02**, the system must provide a **live streaming progress log** (e.g., "Ingesting sources... 100%", "Synthesizing requirements... 20%", "Checking for contradictions...") so the user has immediate feedback and is never left with a blank, unresponsive screen.

---

### 4.2 Quality vs. Verbosity [BLOCKING]

**Question:** Which does the business prefer?

- **Comprehensive (verbose):** The system catches everything, including inferred edge cases — but the output may be 30–50% longer and require more pruning by the BA.
- **Concise (targeted):** The system generates only high-confidence requirements explicitly stated in the sources — shorter, cleaner output but potentially missing edge cases.
- **Configurable per project:** BA can select the mode at the start of each project.

**Why it matters:** This is a fundamental prompt engineering and output design decision. Comprehensive mode requires more tokens (higher cost), longer review time, but lower risk of missing critical requirements.

**Client Response & Decision:**

We prefer **Comprehensive (verbose) with high recall**.

- *Strategic Decision:* In software development and regulatory audits, a missing requirement (e.g., a critical security assertion or SLA constraint) is a catastrophic risk. In contrast, an unnecessary or duplicate user story is a minor inconvenience that a BA can easily delete or merge with a single click. The prompt engineering and LLM system prompts must be calibrated to maximize **recall** over precision. The system must catch all potential edge cases, assumptions, and implicit constraints, relying on the human-in-the-loop review interface to prune the excess.

---

### 4.3 Simultaneous Project Limit [SPRINT 2+]

**Question:** How many projects will be running the full agentic pipeline simultaneously at peak load?

- 5–10 concurrent projects (small team, internal tooling)
- 50–100 concurrent projects (agency or mid-size enterprise)
- 500–1000 concurrent projects (platform / SaaS scale)

**Why it matters:** Concurrent project volume determines vector store capacity, worker pool sizing, and LLM rate limit management. A single-tenant tool needs very different infrastructure from a multi-tenant SaaS platform.

**Client Response & Decision:**

We expect a **small-to-medium team scale** in Phase 1:

- Peak load of **5–10 concurrent project generations** at any one time, with 10–20 active BAs in the system.
- *Architectural Recommendation:* A dedicated task queue (Redis and BullMQ) processing jobs with a reasonable worker pool is highly sufficient. We do not need multi-region Kubernetes auto-scaling on Day 1, but we do need a robust rate-limiting and fallback handler to prevent API rate limits from crashing concurrent jobs.

---

## 5. AI Model & Technology Questions

### 5.1 LLM Provider Preference [BLOCKING]

**Question:** Does the organization have an existing contract, preference, or compliance requirement for a specific LLM provider?

- Existing Azure OpenAI Service subscription (enterprise agreement, data residency controls)
- Preference for Anthropic Claude (no pre-existing contract)
- Requirement to use only open-source, self-hosted models (Llama 3) due to data classification
- No preference — evaluate on quality and cost

**Why it matters:** The LLM provider determines the client library, auth mechanism, rate limits, pricing tier, and data residency story. Switching providers after the fact requires significant refactoring.

**Client Response & Decision:**

We have a strong corporate preference for **Anthropic Claude (Sonnet 3.5/4.5/4.6)** as our primary reasoning engine, with **Google Gemini (1.5 Pro)** as our fallback or large document ingestion processor.

- *Reasoning:* Our evaluation benchmarks show Claude Sonnet provides the most cohesive and grammatically precise requirements output and Gherkin criteria. Gemini's massive context window is perfect for parsing 200-page legacy specifications in the ingestion phase.
- *Compliance Mandate:* Any selected provider configuration must route through enterprise-tier endpoints (or Azure-hosted endpoints) that guarantee a **zero data retention policy** for model training.

---

### 5.2 On-Premise vs. SaaS Deployment [BLOCKING]

**Question:** Does the organization require the system to run within their own cloud account or data center?

- **SaaS (recommended for Phase 1):** Hosted by the Chitragupt team; no infrastructure management by the customer.
- **Customer-hosted (BYOC):** Full stack deployed in the customer's AWS/Azure/GCP account. Customer controls all data.
- **Air-gapped:** No external API calls permitted; all LLM inference must run on-premise.

**Why it matters:** SaaS is a 2-week deployment. BYOC is a 6–8 week engagement. Air-gapped requires open-source LLMs and a fundamentally different model stack with lower output quality.

**Client Response & Decision:**

We will launch on the **Chitragupt-managed SaaS deployment model** for Phase 1 MVP to accelerate validation and reduce initial capital spend.

- *Architectural Guardrail:* The System Architects must containerize the entire application stack using Docker. All database schemas, data storage paradigms, and API endpoints must remain strictly decoupled, ensuring we can transition to a **Customer-hosted (BYOC) AWS deployment** for our enterprise banking clients in Sprint 5+ without rebuilding core logic.

---

### 5.3 Embedding Model Selection Criteria [SPRINT 2+]

**Question:** Are there any constraints on the embedding model?

- Must it be the same provider as the LLM (e.g., OpenAI embeddings if using GPT-4o)?
- Is multilingual embedding support required?
- Is there a maximum embedding dimensionality for the planned vector store?

**Why it matters:** Mixing providers (e.g., Anthropic for LLM, OpenAI for embeddings) is technically fine but adds a second billing relationship and a second API key management requirement. Embedding dimensions affect vector store storage and query latency.

**Client Response & Decision:**

We select **voyage-large-2** or **text-embedding-3-large (1536 dimensions)**.

- *Rationale:* We prefer high dimensional precision to ensure semantic search and retrieval accuracy. In compliance with **INV-MODEL-05**, the embedding model must be held entirely consistent across all namespaces, and we do not mind managing a separate API key for embeddings if it guarantees superior search performance.

---

### 5.4 Agentic Framework Preference [SPRINT 2+]

**Question:** Does the engineering team have an existing investment or preference in an agentic orchestration framework?

- LangGraph (recommended — Python; stateful; graph-based)
- CrewAI (multi-agent; role-based)
- AutoGen (Microsoft Research)
- Custom state machine (maximum control; maximum build effort)

**Why it matters:** Switching agentic frameworks after the pipeline is built is extremely expensive. The choice locks in the team's tooling, debugging approach, and deployment model.

**Client Response & Decision:**

We select and mandate **LangGraph (Python)**.

- *Deep Rationale:* The requirements analysis workflow is a deterministic state cycle (Ingest ➔ Classify ➔ Synthesize ➔ Gap Detect ➔ Conflict Resolve ➔ Review ➔ Re-generate). LangGraph’s stateful, graph-based architecture gives us absolute control over this loop and perfectly enforces our epistemological invariants. Custom state machines introduce too much maintenance overhead, while multi-agent frameworks like CrewAI lack the granular, deterministic state control required for safe enterprise deployments.

---

### 5.5 Vector Store Selection [BLOCKING]

**Question:** Which vector store approach is preferred?

- **Pinecone** (SaaS; managed; simple to start; namespace-based tenant isolation)
- **Qdrant** (self-hosted or managed; high performance; collection-per-tenant isolation)
- **pgvector** (PostgreSQL extension; simplest if already using PostgreSQL; lower performance at scale)
- **Weaviate** (managed or self-hosted; GraphQL API; good for multi-modal)

**Why it matters:** The vector store is a core infrastructure dependency. Migrating between vector stores requires re-embedding all chunks (expensive and time-consuming). The wrong choice at scale degrades retrieval performance significantly.

**Client Response & Decision:**

We select **pgvector (PostgreSQL extension)**.

- *Strategic Decision:* Since PostgreSQL is already our selected relational database for transaction, project, and user entity tracking, utilizing `pgvector` drastically simplifies our deployment topology. It eliminates a separate SaaS vendor relationship, allows us to run standard SQL table joins directly on our chunk embeddings, guarantees atomic database transaction states, and drastically simplifies the implementation of our **Tenant Isolation Invariant (INV-SEC-01)** via standard PostgreSQL Row-Level Security (RLS). Our current scale does not justify the added operational complexity or licensing costs of a dedicated Pinecone/Qdrant cluster.

---

## 6. Budget & Commercial Model Questions

### 6.1 Per-Project Cost Tolerance [BLOCKING]

**Question:** What is the acceptable LLM API cost per requirements analysis project?

- Under $1 per project (aggressively optimized; constrains model selection)
- $1–$5 per project (moderate; allows quality-tier models with caching)
- $5–$20 per project (generous; allows premium-tier models for complex projects)
- Not a concern — prioritize quality over cost

**Why it matters:** The per-project cost target directly determines which LLM tiers are available, how aggressively caching must be implemented, and whether premium conflict-resolution models are affordable.

**Client Response & Decision:**

We select the **$1–$5 per project** range as our target tolerance limit.

- *Rationale:* Since a successful requirement analysis project saves our BAs dozens of manual drafting hours, a cost of $3.00 is highly negligible. We want the system to leverage high-fidelity reasoning models (Claude Sonnet) and execute thorough agentic checks. We must implement aggressive **Prompt Caching** (caching our massive agent instructions and source document headers) to ensure normal project runs remain under $2.00, reserving the remaining budget for intensive conflict resolution loops. We do *not* want to compromise synthesis quality by down-grading to low-cost models.

---

### 6.2 Monthly Infrastructure Budget [BLOCKING]

**Question:** What is the monthly infrastructure budget for the system?

- Under $500/month (startup; minimal infra; shared/managed services only)
- $500–$2,000/month (small team; dedicated instances; managed vector store)
- $2,000–$10,000/month (mid-scale; multi-region; high availability)
- $10,000+/month (enterprise scale; dedicated infra; 24/7 on-call SRE)

**Why it matters:** Infrastructure budget determines hosting provider choice, vector store tier, database configuration, and whether background job workers can scale horizontally or must be pre-provisioned.

**Client Response & Decision:**

We budget **$500–$2,000/month** for dedicated, secure staging and production hosting.

- This envelope easily accommodates a high-performance PostgreSQL (pgvector) instance, Redis/BullMQ task queue nodes, secure S3 file storage buckets, horizontal backend container hosting (AWS ECS), and comprehensive observability tooling (Langfuse).

---

### 6.3 Pricing Model for End Customers [SPRINT 2+]

**Question:** How should the system be priced for paying customers?

- **Per-seat:** Fixed monthly fee per user (predictable revenue; can lead to over-consumption)
- **Per-project:** Charge per requirements analysis run (aligns cost to value; variable revenue)
- **Tiered plans:** Starter / Professional / Business tiers with project volume limits (recommended)
- **Enterprise custom:** Negotiated volume pricing for large accounts

**Why it matters:** The pricing model must be implemented in the billing system (Stripe, etc.) before public launch. It affects the rate limiting logic, the usage tracking schema, and the cost circuit breaker design.

**Client Response & Decision:**

We select **Tiered plans (Starter / Professional / Enterprise)** with integrated project volume caps.

- *Example:* "Professional Plan: Up to 20 projects/month, $150 per user/month."
- This pricing model gives us highly predictable recurring revenue while protecting our systems from malicious or runaway consumption. It aligns perfectly with enterprise procurement standards.

---

### 6.4 Cost Alerts & Budget Controls [SPRINT 2+]

**Question:** Who should receive cost alerts, and at what thresholds?

- Project owner when project reaches 50%, 80%, and 100% of budget cap
- Workspace admin when monthly workspace spend exceeds 80% of monthly cap
- Ops/finance team when total platform spend exceeds a configured threshold

**Why it matters:** Without proactive alerting, cost overruns are discovered at billing time (too late). Alert routing must be defined before the billing module is built.

**Client Response & Decision:**

In strict alignment with **INV-COST-01 & INV-COST-02**:

- **Project Owner:** Must receive immediate in-app and email notifications when a project reaches **80% and 100% of its budget cap** (default project cap is set to $20.00). At 100%, the system must halt all active agent executions for that project and require manual admin intervention to raise the cap.
- **Workspace Admin:** Must receive alerts when monthly workspace spend reaches **80% and 100% of the workspace cap**. At 100%, all agent executions across all projects in that workspace are paused.
- **Finance/Ops:** Receives total platform spend alerts at monthly intervals.

---

## 7. Deployment & Infrastructure Questions

### 7.1 Cloud Provider Requirement [BLOCKING]

**Question:** Does the organization require deployment on a specific cloud provider?

- AWS (EC2, ECS, RDS, S3)
- Azure (AKS, Cosmos DB, Azure Blob)
- GCP (GKE, Cloud SQL, GCS)
- No preference / multi-cloud acceptable

**Why it matters:** Cloud provider determines managed service choices, networking model, IAM design, and compliance certification paths. Azure is preferred for HIPAA and government workloads due to FedRAMP-authorized services.

**Client Response & Decision:**

Our primary deployment standard is **AWS (Amazon Web Services)**.

- *Directives:* All storage bucket implementations (S3), relational database hosting (RDS PostgreSQL), and task execution containers must be architected for AWS. Multi-cloud deployment capability is a nice-to-have, but Day 1 staging and production deployments will run on AWS.

---

### 7.2 Containerization & Orchestration [SPRINT 2+]

**Question:** Does the organization have an existing Kubernetes platform or container orchestration preference?

- Managed Kubernetes (EKS, AKS, GKE)
- Docker Compose / ECS (simpler; lower operational overhead; less scalable)
- Serverless (AWS Lambda, Cloud Run) — not recommended for long-running agentic tasks
- No existing platform

**Why it matters:** Agentic pipelines with background job workers are not well-suited to serverless execution (timeout limits, cold start latency). Kubernetes is recommended for production at any meaningful scale.

**Client Response & Decision:**

We select **Docker Containers managed via AWS ECS (Fargate)**.

- *Rationale:* Fargate allows us to run standard containerized environments without the massive operational and management overhead of a Kubernetes (EKS) cluster. It is highly cost-effective for our Phase 1 concurrent volumes (5–10 parallel projects) while providing clean container isolation. Serverless is excluded due to the potential 10-minute runtime limits of agent loops.

---

### 7.3 High Availability Requirements [SPRINT 2+]

**Question:** What is the required uptime SLA?

- Best effort (no SLA; development/prototype phase)
- 99% uptime (~3.6 days downtime/year; acceptable for internal tooling)
- 99.5% uptime (~1.8 days downtime/year; standard SaaS)
- 99.9% uptime (~8.7 hours downtime/year; enterprise SLA)
- 99.99% uptime (~52 minutes downtime/year; mission-critical)

**Why it matters:** Each nine of availability requires progressively more complex infrastructure (multi-AZ deployment, load balancers, database read replicas, automated failover). 99% is achievable with basic infrastructure; 99.99% requires significant investment.

**Client Response & Decision:**

We require a **99.5% uptime SLA (Standard SaaS)**.

- *Architecture Impact:* We require dedicated, isolated **Staging and Production environments** in AWS. The production environment must run a Multi-AZ RDS PostgreSQL database with daily automated backups and automated failover. The web and container layers must run behind an Application Load Balancer (ALB) across multiple availability zones.

---

### 7.4 CI/CD & Deployment Pipeline [SPRINT 2+]

**Question:** What is the team's existing CI/CD toolchain?

- GitHub Actions
- GitLab CI
- CircleCI / Jenkins
- Azure DevOps

**Why it matters:** The CI/CD pipeline must run the evaluation dataset against each LLM model version upgrade before promoting to production (per INV-MODEL-03). The toolchain choice affects how this quality gate is implemented.

**Client Response & Decision:**

We utilize **GitHub Actions** exclusively.

- *Pipeline Integration:* The CI/CD workflow must run automated code linting, security scanning, unit testing, and execute our core RAG evaluation benchmark (comparing synthesized outputs against the ground-truth dataset) before any code is promoted to our AWS staging or production environments.

---

## 8. Compliance & Regulatory Questions

### 8.1 Data Classification of Requirements Content [BLOCKING]

**Question:** At what data classification level are the client requirements expected to operate?

- **Public / General:** No restrictions; standard cloud SaaS is acceptable.
- **Confidential / Internal:** Standard encryption and access controls required; no data sharing between tenants.
- **Restricted / Sensitive:** Regulated data (PII, financial data); requires SOC 2 compliance and data processing agreements.
- **Highly Restricted / Classified:** Healthcare (HIPAA), government, or defense; requires on-premise or air-gapped deployment.

**Why it matters:** This is the single most important compliance question. The answer determines deployment model, LLM provider choice, encryption requirements, and compliance certifications needed before the product can be sold to regulated industries.

**Client Response & Decision:**

We operate at the **Confidential / Internal** baseline, with some enterprise projects rising to **Restricted / Sensitive (SOC 2, GDPR, HIPAA)**.

- *Deep Architectural Requirements:*
  - Full encryption-in-transit (TLS 1.3) and encryption-at-rest (AES-256 via KMS keys) is mandatory for all databases, vector tables, and file stores.
  - Strict, physically guaranteed multi-tenancy and data isolation (**INV-SEC-01 & INV-SEC-03**) is non-negotiable.
  - Under no circumstances can client requirements data be leaked or co-mingled.

---

### 8.2 Geographic Data Residency [BLOCKING for EU customers]

**Question:** Are any clients in the European Union or subject to EU data protection law?

- If yes: Data must remain within EU boundaries; EU-region deployments and LLM endpoints are mandatory.
- If yes: A Data Processing Agreement (DPA) must be signed before client data is ingested.
- Data residency requirements by region must be confirmed for each client engagement.

**Why it matters:** GDPR fines for cross-border data transfer violations can reach 4% of global annual revenue. This cannot be discovered after client data has been processed.

**Client Response & Decision:**

**Yes, absolutely.** A significant portion of our customer base is located in the European Union and subject to GDPR.

- *Actionable Requirement:* In strict compliance with **INV-COMP-01**, the architecture must support **Geographic Data Residency routing**. The system must detect a workspace's region flag (e.g., `eu`) and route all its file uploads, vector embeddings, transactional databases, and LLM calls strictly to EU-region cloud infrastructure (e.g., AWS `eu-west-1` and Azure OpenAI EU endpoints).

---

### 8.3 Compliance Certifications Required for Sales [SPRINT 2+]

**Question:** Which compliance certifications are required before enterprise customers can sign contracts?

- SOC 2 Type II (typically required by US enterprises; takes 6–12 months)
- ISO 27001 (European enterprise standard)
- HIPAA BAA (healthcare clients; must be in place before any PHI is processed)
- PCI-DSS (fintech; only if the system processes card data — unlikely for spec generation)
- FedRAMP (US government; typically 12–18 months)

**Why it matters:** SOC 2 Type II is the baseline requirement for most enterprise SaaS sales. Starting the audit process requires audit logging and access controls to be in place from the beginning — retroactively adding them is significantly more expensive.

**Client Response & Decision:**

**SOC 2 Type II** is our immediate priority (target: within 6 months of public release), followed by strict **GDPR compliance**.

- *Design Guidance:* We must build access controls, immutable append-only audit logs (**INV-SEC-04**), and system version controls directly into Sprints 1–3 so that we have clean evidence trails when our SOC 2 audit begins. We do not need a HIPAA BAA on Day 1, but the system must be architected to support PII scrubbing to make HIPAA validation seamless in Sprints 5+.

---

### 8.4 PII & Sensitive Data Handling Policy [BLOCKING]

**Question:** What is the organization's policy on PII appearing in requirements documents?

- Requirements documents frequently contain PII (client names, contact info, project financials) — how should the system handle this?
- Should PII be automatically redacted before embedding, or flagged for human review?
- Should the system refuse to ingest documents that contain certain sensitive data types (e.g., SSNs, credit card numbers)?

**Why it matters:** This determines the PII detection module's configuration and the user workflow when PII is found. Automatic redaction changes the source document before embedding — the user must be notified.

**Client Response & Decision:**

We enforce a strict **Automated PII Scrubbing & Redaction policy**.

- *Rationale:* In formal requirements specifications, real PII (such as a stakeholder's cell phone number, personal email, or security keys) is completely unnecessary and represents an unacceptable liability if embedded in our vector store.
- *Implementation:* In accordance with **INV-SEC-02**, the ingestion pipeline must run an automated PII detector (redacting emails, SSNs, credit card patterns, and phone numbers) and replace them with `[PII_REDACTED]` prior to the chunking and embedding steps. The raw uploaded document is stored securely in an isolated bucket prefix (**INV-SEC-03**), but the searchable vectors must remain entirely PII-free.

---

## 9. Integration Ecosystem Questions

### 9.1 Jira Integration Scope [BLOCKING]

**Question:** For the Jira integration, what is the required scope in Phase 1?

- **Read only:** Import existing epics and issues as requirements sources (ingestion only).
- **Read + Write:** Import existing epics, and push generated requirements back as new Jira stories/epics.
- **Bidirectional sync:** Changes to Jira epics after ingestion are reflected back in the BRA spec; changes to the spec push back to Jira.

**Why it matters:** Read-only is a 1-week integration. Read + Write requires mapping the spec schema to Jira's Epic/Story schema (non-trivial). Bidirectional sync is 4+ weeks and requires webhook infrastructure.

**Client Response & Decision:**

We require **Read + Write capability** for Phase 1.

- *Required Scope:* BAs must be able to connect to their Jira instance, import existing high-level Epics/tickets as source inputs, and then push the finalized, human-approved User Stories and Gherkin Acceptance Criteria *directly* back to Jira as engineering tickets. Bidirectional synchronization is too complex and is officially deferred.
- *Safety Guardrail:* In accordance with **INV-HITL-02**, the system must never auto-create tickets. A human must click an explicit "Export to Jira" button on the approved specification dashboard.

---

### 9.2 Single Sign-On (SSO) [SPRINT 2+]

**Question:** Is SSO required for enterprise customers, and which protocols must be supported?

- SAML 2.0 (enterprise standard; required by most large organizations)
- OpenID Connect (OIDC; modern; used by Google, Microsoft, Okta)
- Both (common requirement; SAML for legacy, OIDC for modern)

**Why it matters:** SSO is typically a hard blocker for enterprise sales. It affects the auth library choice and the user provisioning model (SCIM for automatic user creation/deprovisioning).

**Client Response & Decision:**

Yes, SSO is a mandatory blocker for our enterprise engagements. We must support **OIDC (OpenID Connect)** for Google Workspace, Okta, and Microsoft Azure AD on Day 1. SAML 2.0 is deferred to Phase 2.

---

### 9.3 Webhook vs. Polling for Source Updates [SPRINT 2+]

**Question:** For connected integrations (Jira, Confluence, Notion), which update detection method is acceptable?

- **Webhooks (preferred):** Source system pushes a notification when content changes; low latency, low API usage.
- **Polling:** Chitragupt polls the source system on a schedule (e.g., every 15 minutes); higher API usage, potential rate limit issues.
- **Manual trigger only:** BA explicitly triggers a re-ingest when they know the source has changed.

**Why it matters:** Webhooks require the Chitragupt API to be publicly accessible with a stable endpoint. Polling adds recurring API call costs and may hit rate limits on connected systems.

**Client Response & Decision:**

We prefer a hybrid of **Manual Trigger and scheduled Polling**.

- *Rationale:* Constructing and exposing stable webhook endpoints to external systems (Jira/Confluence) introduces significant security and networking overhead in Sprints 1–3. A prominent "Check for Updates" button on the project dashboard, combined with a background polling job that runs every 30 minutes, is extremely robust and simple to build.

---

### 9.4 API Rate Limits on Connected Systems [BLOCKING]

**Question:** For Jira and Confluence integrations, what are the API rate limits on the organization's instance?

- Jira Cloud: Default 10,000 API calls/hour per OAuth app
- Confluence Cloud: Default 60 requests/minute per user
- Are there additional enterprise-tier rate limits available?

**Why it matters:** If a project has 50 Jira epics, each with 10 sub-issues, and each with 5 comments, that is 500 API calls just to ingest one project. This can hit rate limits quickly and must be designed for with batching and backoff.

**Client Response & Decision:**

Our system architects must design the integration client with **Token Bucket Rate Limiting** and **Exponential Backoff with Jitter** from Day 1. We must operate within standard cloud limits (e.g., Confluence's 60 requests/minute), ensuring that bulk requirement imports are queued and throttled programmatically rather than failing mid-process or getting our integration API key blacklisted.

---

## 10. UX, Adoption & Training Questions

### 10.1 Target User's Technical Comfort Level [BLOCKING]

**Question:** What is the AI/technical literacy of the primary users (Business Analysts)?

- **Low:** No prior experience with AI tools; expect significant hand-holding and guided UI.
- **Medium:** Familiar with AI tools (ChatGPT, Copilot); comfortable with natural language interaction; needs clear explanations of confidence scores and citations.
- **High:** Power users who want API access, configurable prompts, and direct model tier selection.

**Why it matters:** This determines the default UI mode (Guided vs. Express vs. Expert) and the vocabulary used in the interface. Showing raw confidence scores (0.87) to a low-literacy user is confusing; showing a simple "High / Medium / Low" indicator is actionable.

**Client Response & Decision:**

Our target BAs have a **Medium technical comfort level**.

- *UI Implications:* They are comfortable with natural language and AI assistants, but they do not want to see raw statistics, floats, or machine code. The UI must display clear, color-coded status badges: `[HIGH CONFIDENCE]` (green), `[INFERRED - REVIEW REQUIRED]` (amber), `[CONFLICT DETECTED]` (red). Hover tooltips must provide simple, human-readable explanations of *why* an item was flagged (e.g., *"This requirement was synthesized based on a combination of Document X and Document Y. Please review acceptance criteria."*).

---

### 10.2 Change Management & Adoption Risk [SPRINT 2+]

**Question:** What is the primary adoption risk?

- "BA resistance" — fear that the tool will replace BA jobs
- "Trust gap" — stakeholders don't believe the AI output is accurate enough to use
- "Workflow disruption" — the tool requires changing existing processes
- "Learning curve" — the tool is too complex to learn quickly

**Why it matters:** Different adoption risks require different mitigation strategies in the product. Fear of replacement → position as "BA copilot," keep human in control prominently. Trust gap → invest in confidence visualization and citation transparency. Workflow disruption → integrate into existing tools (Jira, Confluence) rather than requiring users to come to a new system.

**Client Response & Decision:**

Our primary risk is the **"Trust Gap"**.

- *Strategic Mitigation:* If our BAs or engineering leads suspect the AI is producing ungrounded assertions or hallucinated criteria, they will abandon the tool immediately. To combat this, we must strictly enforce **Traceability (INV-EPI-01)**. By ensuring that every single synthesized user story has an explicit, clickable highlight showing the exact source sentence and paragraph it was drawn from, we demystify the AI output, build rapid user trust, and establish Chitragupt as a reliable copilot.

---

### 10.3 Training & Onboarding Support [SPRINT 2+]

**Question:** What level of onboarding support is expected for each customer tier?

- **Self-serve:** Video documentation, in-app tooltips, and an interactive sample project.
- **Guided onboarding:** A 1-hour live session with a Customer Success Manager for Professional tier.
- **Hands-on implementation:** 2–4 day onsite or remote implementation engagement for Enterprise tier.

**Why it matters:** The onboarding scope determines Customer Success team sizing and the documentation investment required before launch.

**Client Response & Decision:**

We require a robust **Self-serve onboarding** experience.

- The product must ship with comprehensive video walkthroughs, context-sensitive in-app tooltips, and a **pre-built interactive sample project (sandbox)** that allows new BAs to run elicitation and resolve a pre-seeded conflict within their first 5 minutes of logging in.

---

### 10.4 Feedback Mechanism for AI Output Quality [SPRINT 2+]

**Question:** How should users provide feedback when the AI makes a mistake that they want to report (beyond just editing it)?

- Thumbs up / thumbs down on individual requirements (lightweight, anonymized)
- Detailed feedback form: what was wrong, what was expected
- No in-product feedback channel; collect feedback via CS team

**Why it matters:** User feedback on AI quality is the primary signal for model improvement and calibration recalibration. Without a structured feedback channel, quality regressions are only discovered via churn, not proactively.

**Client Response & Decision:**

We require an inline **Thumbs Up / Thumbs Down** feedback button directly next to each requirement draft.

- *Elicitation Loop:* When a user clicks Thumbs Down, the system must trigger a lightweight, 3-choice dropdown checklist (e.g., `Incorrect Interpretation`, `Hallucinated Detail`, `Too Verbose / Out of Scope`) with an optional text box. This data must be logged securely and fed directly into our CI/CD evaluation dataset to help calibrate future prompt versions.

---

## 11. Key Dependencies & Assumptions

### 11.1 Upstream LLM Uptime & Schema Stability [BLOCKING]

**Question:** How will the system mitigate breaking changes in upstream LLM provider API schemas, deprecation cycles, or sudden model rate limit exhaustions?

- Sub-question A: What is our fallback policy if Anthropic Claude experiences a regional service outage?
- Sub-question B: How do we prevent upstream API payload updates from breaking our multi-agent LangGraph schema?

**Why it matters:** A sudden breaking change in a third-party LLM's API response schema or a regional service outage can immediately crash our multi-agent orchestration, resulting in hanging jobs and broken progress indicators.

**Client Response & Decision:**

- **Fallback Policy (Sub-question A):** We mandate the implementation of an automated model fallback chain in Sprints 0-1. Anthropic Claude remains our primary reasoning model, but the orchestration layer must automatically detect 5xx server errors or rate limit codes (429) and route the active LangGraph node execution to Google Gemini 1.5 Pro within the same execution context.
- **Model Version Pinning (Sub-question B):** In strict accordance with **INV-MODEL-03**, floating aliases (e.g., `claude-3-5-sonnet-latest`) are absolutely prohibited in production code. The system must use explicitly pinned API model identifiers (e.g., `claude-3-5-sonnet-20241022`). Any upstream model migration must first run through our automated CI/CD evaluation dataset to verify semantic consistency before promotion.

---

### 11.2 Ingested Document Semantics & Relevance [SPRINT 2+]

**Question:** Does the system assume that all uploaded files are valid requirement baselines, or will it guard against irrelevant uploads (e.g., invoices, marketing slide decks, vacation plans)?

**Why it matters:** Ingesting irrelevant files pollutes our vector namespace, drives up RAG token costs, causes high recall of semantic noise, and violates our Epistemic Traceability Invariant (INV-EPI-01) by linking stories to non-functional noise.

**Client Response & Decision:**

The ingestion pipeline must implement a **Pre-Ingestion Classification Scan** at the start of Sprint 1.

- *Execution Flow:* Prior to executing the semantic chunker and embedding pipeline, a fast-tier model (e.g., Claude Haiku or GPT-4o-mini) must scan the first 1,500 tokens of the document.
- *Outcome:* If the model classifies the document as irrelevant to software requirements, system architectures, or business processes, the upload is halted. The UI displays an alert: *"Upload Stopped: Source Document does not appear to contain requirements content."* This protects pgvector database hygiene and keeps our API costs optimized.

---

### 11.3 Vector Store Co-location & Scaling Thresholds [SPRINT 2+]

**Question:** Is it assumed that pgvector will remain co-located on our primary RDS database indefinitely, and what metric triggers a migration to a dedicated vector store?

**Why it matters:** High-dimensional vector searches (1536 dimensions) are CPU-intensive. If concurrent user volumes scale rapidly, sharing a single RDS database for both transactional queries (billing, auth, user management) and vector similarity searches will lead to query timeouts and UI freezing.

**Client Response & Decision:**

We assume that for Sprints 0–4, co-locating pgvector in our primary AWS RDS PostgreSQL instance is extremely cost-effective and sufficient.

- *Performance SLA:* SAs must track the retrieval latency of the semantic search API. If the P95 latency of similarity retrieval searches crosses **2.5 seconds**, or if RDS CPU utilization consistently crosses **80%** under peak concurrent project generation loads (5-10 runs), the team must trigger a scheduled migration to a dedicated, high-performance vector store (e.g., managed Qdrant) in Sprint 6. The DB repository layer must use a clean repository interface pattern in Sprint 0 to make this transition seamless.

---

### 11.4 Asynchronous Pipeline State & Execution Lockouts [BLOCKING]

**Question:** Does the system assume a project workspace is locked or frozen while a BA reviews a draft, or can elicitation and synthesis continue in parallel?

**Why it matters:** If BAs are locked out of adding documents or running chats while a previous requirement draft is pending review, it creates massive scheduling deadlocks and destroys BA productivity.

**Client Response & Decision:**

We assume the review pipeline is **fully asynchronous and non-blocking**.

- *Workspace States:* BAs must be able to upload new source documents, run elicitation chats, and trigger incremental requirement drafts even if there are active requirements marked as `Draft` or `Pending Conflict Resolution`.
- *Human Override Invariant (INV-HITL-01):* Any requirements that have been explicitly modified or approved (`BA Approved` status) are completely locked. Subsequent agentic synthesis runs can only modify, merge, or create requirements that are in a `Draft` or `Inferred` status, ensuring BAs never lose their manual review work.

---

> End of Document • Chitragupt Unknowns & Stakeholder Queries • v2.0 • May 2026
