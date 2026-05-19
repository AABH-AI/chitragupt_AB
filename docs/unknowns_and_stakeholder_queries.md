# Unknowns & Stakeholder Input Requirements

**Phase:** Product Discovery
**Version:** 2.0 — Expanded
**Purpose:** To aggregate all unknown variables, edge cases, open architectural questions, and critical stakeholder queries that must be answered before the engineering team can commit to Sprint 1 deliverables with confidence. Each question identifies what is at stake if it goes unanswered.

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

### 1.2 Format Priority [BLOCKING]
**Question:** If the MVP can only support 3 input formats, which must be included on Day 1?

Proposed ranking for discussion:
1. PDF (most common for formal requirements)
2. Free-text chat (core elicitation UX)
3. DOCX (widespread in enterprise)
4. Jira/Linear links (structured, already ticketed projects)
5. Confluence URL (common internal documentation)

**Why it matters:** Each format requires a different parsing strategy. PDF requires OCR for scanned documents; Jira requires API authentication and pagination; Confluence requires HTML-to-text normalization. Supporting all 5 from Day 1 triples ingestion complexity.

### 1.3 Multimedia Inputs [SPRINT 2+]
**Question:** Will the system be expected to extract meaningful requirements from:
- Architecture diagrams embedded in PDFs or uploaded as images?
- Audio recordings of stakeholder meetings?
- Short video walkthroughs of existing systems?

**Why it matters:** Each multimedia type requires a specialized extraction path. Image analysis requires a vision-capable LLM (cost uplift ~$0.002/image). Audio requires Whisper transcription (cost: ~$0.006/minute). If these are not Day 1 requirements, they can be excluded from the ingestion architecture entirely for Sprint 1.

### 1.4 Document Update & Versioning Policy [BLOCKING]
**Question:** If a source document (e.g., a Confluence page) is updated after it has been ingested, what should the system do?

Options for stakeholder to choose:
- **A. Manual re-ingest:** Require the BA to explicitly re-upload the updated document. System does not auto-detect changes.
- **B. Auto re-ingest on change:** System polls linked URLs or listens to webhooks; automatically re-ingests when the source changes and flags affected requirements for re-review.
- **C. Notify only:** System detects the source has changed and notifies the BA; re-ingest is manual but prompted.

**Why it matters:** Option A is simplest to build in Sprint 1. Option B requires webhook integrations and a diffing pipeline. The wrong choice creates confusion when stakeholders update documents mid-project.

### 1.5 Deduplication Policy [SPRINT 2+]
**Question:** If the same document (or a very similar one) is submitted twice — either by the same user or across different projects — what should happen?
- Silently deduplicate (one set of chunks serves both)?
- Re-embed separately (simpler, slight cost duplication)?
- Warn the user that a near-duplicate was detected?

**Why it matters:** Determines whether hash-based deduplication is a Day 1 feature or a Phase 2 optimization.

### 1.6 Language & Localization [SPRINT 2+]
**Question:** Will the system need to process requirements documents in languages other than English?
- If yes, which languages are priority (e.g., Spanish, French, German, Arabic)?
- Should the output specification be in the same language as the input, or always in English?

**Why it matters:** Multilingual support requires a multilingual embedding model (e.g., BGE-M3) rather than English-optimized models. The Elicitation Agent's chat prompts must be translated or templated in the target language. This is a significant scope expansion if not planned from the start.

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

### 2.3 Requirement Granularity [BLOCKING]
**Question:** What level of granularity is preferred for the output?
- **Epic-level:** Large, high-level business goals (e.g., "Support payment reconciliation")
- **Feature-level:** Named, scoped capabilities (e.g., "Export reconciliation CSV")
- **User Story-level:** Standard format ("As an [Actor], I want [Feature] so that [Value]")
- **Acceptance Criteria-level:** Gherkin BDD format for each story

**Why it matters:** The Spec Writer Agent's output template and the completeness checklist are calibrated to a specific granularity level. Epic-level specs take fewer tokens (cheaper, faster); story-level specs are more actionable for engineering but take 3–5x more tokens per project.

### 2.4 Traceability Matrix Format [SPRINT 2+]
**Question:** How do stakeholders want to consume the traceability matrix?
- Embedded table within the spec document
- Separate CSV export
- Interactive clickable links in the review UI only

**Why it matters:** Embedded tables in DOCX are complex to generate programmatically. A separate CSV export is simpler but requires a separate download step.

### 2.5 Confidence Tag Display in Exports [BLOCKING]
**Question:** Should confidence tags (`[INFERRED — VERIFY]`, `[SYNTHESIZED]`) appear in the exported DOCX and PDF that is shared with the client?
- **Yes:** Full transparency to the client about what was synthesized.
- **No:** Tags are internal review tools only; the client sees a clean, tag-free document.
- **Configurable per export:** BA can choose whether to include tags in client-facing exports.

**Why it matters:** This is a product positioning decision with significant UX implications. Showing tags to clients sets expectations about AI limitations; hiding them creates a cleaner client experience but reduces transparency.

---

## 3. Human-in-the-Loop & Workflow

### 3.1 The Review Process & Roles [BLOCKING]
**Question:** Who is in the review chain, and in what order?
- Who reviews the AI-generated spec first? (BA? PM? SA?)
- Does the client/stakeholder directly review and edit the AI output, or do they only see the finalized, BA-curated version?
- Is there a multi-stage review (BA reviews → PM approves → SA signs off) or a single-review gate?

**Why it matters:** The review workflow determines the permission model, notification system, and state machine design. A single-stage review is a simpler product. A multi-stage review requires role-based views, conditional approval workflows, and hand-off notifications.

### 3.2 Elicitation Aggressiveness [BLOCKING]
**Question:** How proactive should the Elicitation Agent be in asking clarifying questions?
- **Option A — Batched:** Ask all identified gap questions at once (e.g., a list of 8 questions) so the user can answer efficiently.
- **Option B — Sequential drip:** Ask one question at a time, use the answer to inform the next question. Slower but more conversational.
- **Option C — Threshold-gated:** Only ask clarifying questions for gaps that would affect requirements marked "must have" priority.

**Why it matters:** Option A is simpler to implement but can overwhelm users. Option B requires more complex conversational state management. The choice affects the Elicitation Agent's prompt design and session state schema significantly.

### 3.3 Conflict Resolution UI [SPRINT 2+]
**Question:** How do stakeholders want to resolve detected conflicts?
- Side-by-side diff view showing both conflicting source excerpts with "Accept A / Accept B / Provide clarification" buttons
- An email or Slack notification with the conflict summary and a link to the resolution UI
- A simple dropdown choice from within the spec document inline

**Why it matters:** The conflict resolution UI is a critical product experience differentiator. A poor conflict UI leads to unresolved conflicts being deferred and requirements remaining in `[CONFLICT — PENDING]` status indefinitely.

### 3.4 Asynchronous Review & Notification [SPRINT 2+]
**Question:** How should stakeholders be notified when the spec is ready for review or when a conflict requires their input?
- In-app notification only (requires user to be logged in)
- Email notification with a direct link
- Slack / Teams message to a configured channel
- All of the above (configurable per workspace)

**Why it matters:** If the review workflow is asynchronous (BA generates spec → client reviews next day), the notification system is critical. Without it, specs sit unreviewed.

---

## 4. Performance & SLA Expectations

### 4.1 Acceptable Generation Latency [BLOCKING]
**Question:** For a mid-complexity project (3 documents, ~50 pages total), what is the acceptable wait time for the complete specification to be generated?
- **Under 2 minutes** — requires parallel agent execution, potentially higher cost per run
- **2–10 minutes** — allows sequential processing; lower cost; likely requires streaming progress UI
- **Up to 30 minutes** — acceptable as an async background job with email notification on completion
- **Same day** — specification batch processed overnight

**Why it matters:** The latency target determines the architecture (sync vs. async pipeline, parallel vs. sequential agents, streaming vs. bulk delivery). Targeting 2 minutes requires significantly more infrastructure than targeting 30 minutes.

### 4.2 Quality vs. Verbosity [BLOCKING]
**Question:** Which does the business prefer?
- **Comprehensive (verbose):** The system catches everything, including inferred edge cases — but the output may be 30–50% longer and require more pruning by the BA.
- **Concise (targeted):** The system generates only high-confidence requirements explicitly stated in the sources — shorter, cleaner output but potentially missing edge cases.
- **Configurable per project:** BA can select the mode at the start of each project.

**Why it matters:** This is a fundamental prompt engineering and output design decision. Comprehensive mode requires more tokens (higher cost), longer review time, but lower risk of missing critical requirements.

### 4.3 Simultaneous Project Limit [SPRINT 2+]
**Question:** How many projects will be running the full agentic pipeline simultaneously at peak load?
- 5–10 concurrent projects (small team, internal tooling)
- 50–100 concurrent projects (agency or mid-size enterprise)
- 500–1000 concurrent projects (platform / SaaS scale)

**Why it matters:** Concurrent project volume determines vector store capacity, worker pool sizing, and LLM rate limit management. A single-tenant tool needs very different infrastructure from a multi-tenant SaaS platform.

---

## 5. AI Model & Technology Questions

### 5.1 LLM Provider Preference [BLOCKING]
**Question:** Does the organization have an existing contract, preference, or compliance requirement for a specific LLM provider?
- Existing Azure OpenAI Service subscription (enterprise agreement, data residency controls)
- Preference for Anthropic Claude (no pre-existing contract)
- Requirement to use only open-source, self-hosted models (Llama 3) due to data classification
- No preference — evaluate on quality and cost

**Why it matters:** The LLM provider determines the client library, auth mechanism, rate limits, pricing tier, and data residency story. Switching providers after the fact requires significant refactoring.

### 5.2 On-Premise vs. SaaS Deployment [BLOCKING]
**Question:** Does the organization require the system to run within their own cloud account or data center?
- **SaaS (recommended for Phase 1):** Hosted by the Chitragupt team; no infrastructure management by the customer.
- **Customer-hosted (BYOC):** Full stack deployed in the customer's AWS/Azure/GCP account. Customer controls all data.
- **Air-gapped:** No external API calls permitted; all LLM inference must run on-premise.

**Why it matters:** SaaS is a 2-week deployment. BYOC is a 6–8 week engagement. Air-gapped requires open-source LLMs and a fundamentally different model stack with lower output quality.

### 5.3 Embedding Model Selection Criteria [SPRINT 2+]
**Question:** Are there any constraints on the embedding model?
- Must it be the same provider as the LLM (e.g., OpenAI embeddings if using GPT-4o)?
- Is multilingual embedding support required?
- Is there a maximum embedding dimensionality for the planned vector store?

**Why it matters:** Mixing providers (e.g., Anthropic for LLM, OpenAI for embeddings) is technically fine but adds a second billing relationship and a second API key management requirement. Embedding dimensions affect vector store storage and query latency.

### 5.4 Agentic Framework Preference [SPRINT 2+]
**Question:** Does the engineering team have an existing investment or preference in an agentic orchestration framework?
- LangGraph (recommended — Python; stateful; graph-based)
- CrewAI (multi-agent; role-based)
- AutoGen (Microsoft Research)
- Custom state machine (maximum control; maximum build effort)

**Why it matters:** Switching agentic frameworks after the pipeline is built is extremely expensive. The choice locks in the team's tooling, debugging approach, and deployment model.

### 5.5 Vector Store Selection [BLOCKING]
**Question:** Which vector store approach is preferred?
- **Pinecone** (SaaS; managed; simple to start; namespace-based tenant isolation)
- **Qdrant** (self-hosted or managed; high performance; collection-per-tenant isolation)
- **pgvector** (PostgreSQL extension; simplest if already using PostgreSQL; lower performance at scale)
- **Weaviate** (managed or self-hosted; GraphQL API; good for multi-modal)

**Why it matters:** The vector store is a core infrastructure dependency. Migrating between vector stores requires re-embedding all chunks (expensive and time-consuming). The wrong choice at scale degrades retrieval performance significantly.

---

## 6. Budget & Commercial Model Questions

### 6.1 Per-Project Cost Tolerance [BLOCKING]
**Question:** What is the acceptable LLM API cost per requirements analysis project?
- Under $1 per project (aggressively optimized; constrains model selection)
- $1–$5 per project (moderate; allows quality-tier models with caching)
- $5–$20 per project (generous; allows premium-tier models for complex projects)
- Not a concern — prioritize quality over cost

**Why it matters:** The per-project cost target directly determines which LLM tiers are available, how aggressively caching must be implemented, and whether premium conflict-resolution models are affordable.

### 6.2 Monthly Infrastructure Budget [BLOCKING]
**Question:** What is the monthly infrastructure budget for the system?
- Under $500/month (startup; minimal infra; shared/managed services only)
- $500–$2,000/month (small team; dedicated instances; managed vector store)
- $2,000–$10,000/month (mid-scale; multi-region; high availability)
- $10,000+/month (enterprise scale; dedicated infra; 24/7 on-call SRE)

**Why it matters:** Infrastructure budget determines hosting provider choice, vector store tier, database configuration, and whether background job workers can scale horizontally or must be pre-provisioned.

### 6.3 Pricing Model for End Customers [SPRINT 2+]
**Question:** How should the system be priced for paying customers?
- **Per-seat:** Fixed monthly fee per user (predictable revenue; can lead to over-consumption)
- **Per-project:** Charge per requirements analysis run (aligns cost to value; variable revenue)
- **Tiered plans:** Starter / Professional / Business tiers with project volume limits (recommended)
- **Enterprise custom:** Negotiated volume pricing for large accounts

**Why it matters:** The pricing model must be implemented in the billing system (Stripe, etc.) before public launch. It affects the rate limiting logic, the usage tracking schema, and the cost circuit breaker design.

### 6.4 Cost Alerts & Budget Controls [SPRINT 2+]
**Question:** Who should receive cost alerts, and at what thresholds?
- Project owner when project reaches 50%, 80%, and 100% of budget cap
- Workspace admin when monthly workspace spend exceeds 80% of monthly cap
- Ops/finance team when total platform spend exceeds a configured threshold

**Why it matters:** Without proactive alerting, cost overruns are discovered at billing time (too late). Alert routing must be defined before the billing module is built.

---

## 7. Deployment & Infrastructure Questions

### 7.1 Cloud Provider Requirement [BLOCKING]
**Question:** Does the organization require deployment on a specific cloud provider?
- AWS (EC2, ECS, RDS, S3)
- Azure (AKS, Cosmos DB, Azure Blob)
- GCP (GKE, Cloud SQL, GCS)
- No preference / multi-cloud acceptable

**Why it matters:** Cloud provider determines managed service choices, networking model, IAM design, and compliance certification paths. Azure is preferred for HIPAA and government workloads due to FedRAMP-authorized services.

### 7.2 Containerization & Orchestration [SPRINT 2+]
**Question:** Does the organization have an existing Kubernetes platform or container orchestration preference?
- Managed Kubernetes (EKS, AKS, GKE)
- Docker Compose / ECS (simpler; lower operational overhead; less scalable)
- Serverless (AWS Lambda, Cloud Run) — not recommended for long-running agentic tasks
- No existing platform

**Why it matters:** Agentic pipelines with background job workers are not well-suited to serverless execution (timeout limits, cold start latency). Kubernetes is recommended for production at any meaningful scale.

### 7.3 High Availability Requirements [SPRINT 2+]
**Question:** What is the required uptime SLA?
- Best effort (no SLA; development/prototype phase)
- 99% uptime (~3.6 days downtime/year; acceptable for internal tooling)
- 99.5% uptime (~1.8 days downtime/year; standard SaaS)
- 99.9% uptime (~8.7 hours downtime/year; enterprise SLA)
- 99.99% uptime (~52 minutes downtime/year; mission-critical)

**Why it matters:** Each nine of availability requires progressively more complex infrastructure (multi-AZ deployment, load balancers, database read replicas, automated failover). 99% is achievable with basic infrastructure; 99.99% requires significant investment.

### 7.4 CI/CD & Deployment Pipeline [SPRINT 2+]
**Question:** What is the team's existing CI/CD toolchain?
- GitHub Actions
- GitLab CI
- CircleCI / Jenkins
- Azure DevOps

**Why it matters:** The CI/CD pipeline must run the evaluation dataset against each LLM model version upgrade before promoting to production (per INV-MODEL-03). The toolchain choice affects how this quality gate is implemented.

---

## 8. Compliance & Regulatory Questions

### 8.1 Data Classification of Requirements Content [BLOCKING]
**Question:** At what data classification level are the client requirements expected to operate?
- **Public / General:** No restrictions; standard cloud SaaS is acceptable.
- **Confidential / Internal:** Standard encryption and access controls required; no data sharing between tenants.
- **Restricted / Sensitive:** Regulated data (PII, financial data); requires SOC 2 compliance and data processing agreements.
- **Highly Restricted / Classified:** Healthcare (HIPAA), government, or defense; requires on-premise or air-gapped deployment.

**Why it matters:** This is the single most important compliance question. The answer determines deployment model, LLM provider choice, encryption requirements, and compliance certifications needed before the product can be sold to regulated industries.

### 8.2 Geographic Data Residency [BLOCKING for EU customers]
**Question:** Are any clients in the European Union or subject to EU data protection law?
- If yes: Data must remain within EU boundaries; EU-region deployments and LLM endpoints are mandatory.
- If yes: A Data Processing Agreement (DPA) must be signed before client data is ingested.
- Data residency requirements by region must be confirmed for each client engagement.

**Why it matters:** GDPR fines for cross-border data transfer violations can reach 4% of global annual revenue. This cannot be discovered after client data has been processed.

### 8.3 Compliance Certifications Required for Sales [SPRINT 2+]
**Question:** Which compliance certifications are required before enterprise customers can sign contracts?
- SOC 2 Type II (typically required by US enterprises; takes 6–12 months)
- ISO 27001 (European enterprise standard)
- HIPAA BAA (healthcare clients; must be in place before any PHI is processed)
- PCI-DSS (fintech; only if the system processes card data — unlikely for spec generation)
- FedRAMP (US government; typically 12–18 months)

**Why it matters:** SOC 2 Type II is the baseline requirement for most enterprise SaaS sales. Starting the audit process requires audit logging and access controls to be in place from the beginning — retroactively adding them is significantly more expensive.

### 8.4 PII & Sensitive Data Handling Policy [BLOCKING]
**Question:** What is the organization's policy on PII appearing in requirements documents?
- Requirements documents frequently contain PII (client names, contact info, project financials) — how should the system handle this?
- Should PII be automatically redacted before embedding, or flagged for human review?
- Should the system refuse to ingest documents that contain certain sensitive data types (e.g., SSNs, credit card numbers)?

**Why it matters:** This determines the PII detection module's configuration and the user workflow when PII is found. Automatic redaction changes the source document before embedding — the user must be notified.

---

## 9. Integration Ecosystem Questions

### 9.1 Jira Integration Scope [BLOCKING]
**Question:** For the Jira integration, what is the required scope in Phase 1?
- **Read only:** Import existing epics and issues as requirements sources (ingestion only).
- **Read + Write:** Import existing epics, and push generated requirements back as new Jira stories/epics.
- **Bidirectional sync:** Changes to Jira epics after ingestion are reflected back in the BRA spec; changes to the spec push back to Jira.

**Why it matters:** Read-only is a 1-week integration. Read + Write requires mapping the spec schema to Jira's Epic/Story schema (non-trivial). Bidirectional sync is 4+ weeks and requires webhook infrastructure.

### 9.2 Single Sign-On (SSO) [SPRINT 2+]
**Question:** Is SSO required for enterprise customers, and which protocols must be supported?
- SAML 2.0 (enterprise standard; required by most large organizations)
- OpenID Connect (OIDC; modern; used by Google, Microsoft, Okta)
- Both (common requirement; SAML for legacy, OIDC for modern)

**Why it matters:** SSO is typically a hard blocker for enterprise sales. It affects the auth library choice and the user provisioning model (SCIM for automatic user creation/deprovisioning).

### 9.3 Webhook vs. Polling for Source Updates [SPRINT 2+]
**Question:** For connected integrations (Jira, Confluence, Notion), which update detection method is acceptable?
- **Webhooks (preferred):** Source system pushes a notification when content changes; low latency, low API usage.
- **Polling:** Chitragupt polls the source system on a schedule (e.g., every 15 minutes); higher API usage, potential rate limit issues.
- **Manual trigger only:** BA explicitly triggers a re-ingest when they know the source has changed.

**Why it matters:** Webhooks require the Chitragupt API to be publicly accessible with a stable endpoint. Polling adds recurring API call costs and may hit rate limits on connected systems.

### 9.4 API Rate Limits on Connected Systems [BLOCKING]
**Question:** For Jira and Confluence integrations, what are the API rate limits on the organization's instance?
- Jira Cloud: Default 10,000 API calls/hour per OAuth app
- Confluence Cloud: Default 60 requests/minute per user
- Are there additional enterprise-tier rate limits available?

**Why it matters:** If a project has 50 Jira epics, each with 10 sub-issues, and each with 5 comments, that is 500 API calls just to ingest one project. This can hit rate limits quickly and must be designed for with batching and backoff.

---

## 10. UX, Adoption & Training Questions

### 10.1 Target User's Technical Comfort Level [BLOCKING]
**Question:** What is the AI/technical literacy of the primary users (Business Analysts)?
- **Low:** No prior experience with AI tools; expect significant hand-holding and guided UI.
- **Medium:** Familiar with AI tools (ChatGPT, Copilot); comfortable with natural language interaction; needs clear explanations of confidence scores and citations.
- **High:** Power users who want API access, configurable prompts, and direct model tier selection.

**Why it matters:** This determines the default UI mode (Guided vs. Express vs. Expert) and the vocabulary used in the interface. Showing raw confidence scores (0.87) to a low-literacy user is confusing; showing a simple "High / Medium / Low" indicator is actionable.

### 10.2 Change Management & Adoption Risk [SPRINT 2+]
**Question:** What is the primary adoption risk?
- "BA resistance" — fear that the tool will replace BA jobs
- "Trust gap" — stakeholders don't believe the AI output is accurate enough to use
- "Workflow disruption" — the tool requires changing existing processes
- "Learning curve" — the tool is too complex to learn quickly

**Why it matters:** Different adoption risks require different mitigation strategies in the product. Fear of replacement → position as "BA copilot," keep human in control prominently. Trust gap → invest in confidence visualization and citation transparency. Workflow disruption → integrate into existing tools (Jira, Confluence) rather than requiring users to come to a new system.

### 10.3 Training & Onboarding Support [SPRINT 2+]
**Question:** What level of onboarding support is expected for each customer tier?
- **Self-serve:** Video documentation, in-app tooltips, and an interactive sample project.
- **Guided onboarding:** A 1-hour live session with a Customer Success Manager for Professional tier.
- **Hands-on implementation:** 2–4 day onsite or remote implementation engagement for Enterprise tier.

**Why it matters:** The onboarding scope determines Customer Success team sizing and the documentation investment required before launch.

### 10.4 Feedback Mechanism for AI Output Quality [SPRINT 2+]
**Question:** How should users provide feedback when the AI makes a mistake that they want to report (beyond just editing it)?
- Thumbs up / thumbs down on individual requirements (lightweight, anonymized)
- Detailed feedback form: what was wrong, what was expected
- No in-product feedback channel; collect feedback via CS team

**Why it matters:** User feedback on AI quality is the primary signal for model improvement and calibration recalibration. Without a structured feedback channel, quality regressions are only discovered via churn, not proactively.

---

> End of Document • Chitragupt Unknowns & Stakeholder Queries • v2.0 • May 2026
