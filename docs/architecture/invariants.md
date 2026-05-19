# System Invariants

**Phase:** Product Discovery
**Version:** 2.0 — Expanded
**Purpose:** To establish the absolute, unbreakable rules of the Chitragupt system. These invariants serve as architectural constraints that must not be violated by any feature, sprint, agent behavior, or LLM output. Violations of invariants are system bugs, not product decisions.

---

## How to Use This Document

Each invariant is stated as a rule that must hold true under **all conditions** — including edge cases, failure states, high load, and partial system failures. If an invariant cannot be guaranteed, the system must fail safely (surface error, halt generation, alert operator) rather than silently violate it.

Before any feature ships, the engineering team should explicitly verify it does not violate any invariant below.

---

## 1. Data Security & Tenant Isolation

**INV-SEC-01 — Tenant Isolation Invariant**
Under no circumstances can vector embeddings, chunks, metadata, requirements, documents, or any derived data from Tenant A be queried, retrieved, synthesized, or displayed during a session belonging to Tenant B. This invariant applies even if two tenants share the same underlying infrastructure. Enforcement mechanisms are: separate vector namespaces, row-level security in the relational database, JWT-bound API middleware, and mandatory `tenant_id` filter on every vector query. Any system component that issues a vector query without a `tenant_id` filter is a critical security defect and must be fixed before deployment.

**INV-SEC-02 — Chat Ephemeral PII Scrubbing Invariant**
Chat session logs and conversational elicitation content must be scanned for PII (personally identifiable information: names, email addresses, phone numbers, government IDs, financial account numbers) before any part of the chat content is embedded into the vector store. PII-flagged content must be either redacted (replaced with `[PII_REDACTED]`) or excluded from embedding entirely. The scrubbing step is mandatory and must execute before the embedding call, never after.

**INV-SEC-03 — File Storage Isolation Invariant**
Raw uploaded documents must be stored in a path or bucket prefix that is strictly scoped to the owning tenant (e.g., `s3://chitragupt-docs/{tenant_id}/{project_id}/`). A user from Tenant A must never receive a presigned URL that points to a file belonging to Tenant B, regardless of whether they somehow know the file path.

**INV-SEC-04 — Audit Log Immutability Invariant**
The audit log is append-only. No entry in the audit log may be updated or deleted by any user, agent, or system process — including administrators. If data deletion is required for compliance (GDPR right-to-erasure), the audit log entry for the erasure event is preserved but the referenced entity content is scrubbed. The audit log records the fact that erasure occurred.

**INV-SEC-05 — Prompt Injection Containment Invariant**
Retrieved chunks from the vector store must never be able to override, modify, or supplant the agent's system prompt instructions. The system prompt must be placed in a protected position in the model's context that precedes all user and retrieved content. Any retrieved content that appears to contain prompt injection attempts (e.g., "Ignore previous instructions and...") must be logged, flagged, and excluded from the synthesis context.

---

## 2. Epistemological & Agentic Rules

**INV-EPI-01 — Traceability Invariant**
Every generated requirement, constraint, and assumption in the final specification **must** contain a verifiable pointer (`source_chunks` array) to at least one active, non-tombstoned chunk in the vector store. The pointer must resolve to a real chunk record. Ungrounded, zero-shot generation of business requirements is strictly prohibited. A requirement with an empty `source_chunks` array must not be writable to the database except as a human-authored override (which is itself a valid source of truth).

**INV-EPI-02 — Conflict Non-Resolution Invariant**
If the retrieval stage surfaces two sources that directly contradict each other on the same topic, the Agentic layer must **not** unilaterally decide which is correct. It must halt synthesis for that specific topic, create a `Conflict` object, and raise it for human review. The only exception is when the hierarchy of truth is unambiguous (e.g., a Human Override — Rank 1 — contradicts a document — Rank 3; in this case the override wins without creating a conflict flag). The Conflict Non-Resolution invariant applies to sources of equal or adjacent trust tier.

**INV-EPI-03 — Confidence Tagging Invariant**
Any synthesized output with a calibrated confidence score below 0.85 **must** be tagged with the appropriate confidence label (`[SYNTHESIZED]`, `[INFERRED — VERIFY]`, or `[SPECULATIVE — REVIEW]`) both in the database record and in the rendered output to the user. Under no circumstances may a low-confidence claim be presented to the user without its confidence tag. Stripping tags is a product defect.

**INV-EPI-04 — Orphan Knowledge Prohibition Invariant**
Any LLM-generated claim that cannot be matched to at least one chunk in the vector store (i.e., an "Orphan" — has no retrievable source) must not appear in the final specification as a confirmed requirement. It must either be: raised as an Open Question (Gap), flagged as `[SPECULATIVE — REVIEW]` if included, or discarded entirely. The agent must never present Orphan Knowledge as an established fact.

**INV-EPI-05 — Temporal Validity Invariant**
Chunks with a non-null `valid_until` timestamp that has passed must be excluded from all retrieval queries. Requirements derived solely from tombstoned or expired chunks must be flagged for re-validation. A system upgrade, database migration, or performance optimization must never remove the `is_active` and `valid_until` filters from retrieval queries.

**INV-EPI-06 — Visual Extraction Confidence Cap Invariant**
Any requirement or claim derived from a visual extraction (diagram, screenshot, image, video frame) must have its final confidence score capped at 0.80, regardless of the LLM's reported confidence. All visual-derived claims must carry the `[VISUAL EXTRACTION — VERIFY]` tag in the output. This cap cannot be waived by configuration.

---

## 3. Human-in-the-Loop (HITL) Authority

**INV-HITL-01 — Human Override Invariant**
A human reviewer's explicit edit, approval, or rejection of an LLM-generated output becomes the absolute ground truth for that output and supersedes all previous AI-generated versions. The system **cannot** overwrite a human edit during subsequent re-generation cycles for the same requirement. The `human_override_text` field preserves the original AI text permanently; the `description` field reflects the human-edited version. Re-generation of an approved requirement is only permitted if the human explicitly requests it and confirms the override is intentional.

**INV-HITL-02 — Manual Trigger Invariant**
The system will not automatically push any generated specification, requirement, or artifact to downstream execution tools (Jira, GitHub, Confluence, CI/CD pipelines) without an explicit, deliberate human approval action on that specific export. Automation hooks (webhooks) are permitted to fire *after* human approval, not in lieu of it. A specification in `draft` or `in_review` status must never trigger an external system write.

**INV-HITL-03 — Re-generation Scope Invariant**
When a human reviewer requests re-generation of a specific requirement or section, the re-generation must be scoped only to that requirement or section. The agent must not re-generate, overwrite, or modify any requirement that has already been human-approved in the same specification version. Approved requirements are immutable until the human explicitly requests a new version cycle.

**INV-HITL-04 — Conflict Escalation Invariant**
A Conflict object may only be moved to `resolved` status by an explicit human action (choosing Source A, Source B, or providing a manual resolution). An agent may not programmatically resolve a conflict. An agent may provide a recommendation (e.g., "Source B appears more authoritative based on document date") but the resolution action itself is reserved for humans.

**INV-HITL-05 — Spec Lock Invariant**
Once a Specification reaches `locked` status, no further automated changes may be made to its Requirements, Constraints, or Assumptions. The locked specification is a final, immutable artifact. If errors are discovered after locking, a new Specification version must be created — the locked version must not be modified.

---

## 4. Performance & Execution

**INV-PERF-01 — Deterministic Retrieval Invariant**
Given the exact same vector database state, the same query, and the same retrieval parameters (top-K, similarity threshold, metadata filters), the retrieval phase must return the exact same chunks in the exact same ranked order. Non-determinism in retrieval undermines traceability and reproducibility of specifications. Random re-ranking or stochastic retrieval algorithms that cannot be seeded must not be used in the retrieval layer.

**INV-PERF-02 — Stateless Agent Invocation Invariant**
The core reasoning agents must not maintain internal in-memory state between separate invocations. All context, retrieved chunks, and session history must be loaded explicitly from the vector store, the relational database, or the active session state object at the start of each invocation. An agent that relies on implicit in-memory state between calls is not horizontally scalable and violates this invariant.

**INV-PERF-03 — Graceful Degradation Invariant**
If an LLM provider (primary or fallback) is unavailable or returns a non-recoverable error, the system must degrade gracefully: queue the failed request for async retry, preserve all previously generated output, notify the user of the delay, and never corrupt the project state. The system must not retry indefinitely (maximum 3 attempts with exponential backoff); after exhausting retries, the task must move to a dead-letter queue for human-initiated retry.

---

## 5. Cost & Budget Invariants

**INV-COST-01 — Project Budget Cap Invariant**
If a project has a `budget_cap_usd` configured, the system must not initiate new LLM inference calls that would push the project's `cost_incurred_usd` above the cap. When the budget is exhausted: (a) stop all active agent tasks for that project, (b) preserve all output generated up to that point, (c) surface a clear budget alert to the project owner and workspace admin, and (d) require an explicit human action to raise the cap before processing continues. The system must never silently exceed a configured budget.

**INV-COST-02 — Workspace Monthly Budget Cap Invariant**
If a workspace has a `monthly_budget_cap_usd` configured, the system must enforce it at the workspace level across all projects. When the workspace monthly cap is reached, all agent tasks across all projects in that workspace are paused. The workspace admin is notified immediately. This invariant takes precedence over individual project-level caps.

**INV-COST-03 — Cost Attribution Invariant**
Every LLM API call must be attributed to a specific project, agent, and model tier before it is issued. Unattributed calls (where project_id or agent_name is null) are prohibited. The `LLMCallLog` record must be written atomically with the API call — if logging fails, the call must not be issued (the system must not incur costs it cannot account for).

**INV-COST-04 — Free-Tier Protection Invariant**
For users on the free or starter plan, the system must enforce hard rate limits per project (e.g., maximum 3 LLM agent invocations per session). Premium agent tiers (Opus / o1) must be disabled for non-qualifying plans. Plan entitlements are checked at the start of each agent invocation, not just at account creation.

---

## 6. UX & Responsiveness Invariants

**INV-UX-01 — User Feedback Immediacy Invariant**
Every user action — file upload, message send, approval click, export request — must produce a visible system response within 2 seconds. This may be a progress indicator, a confirmation toast, or the start of a streaming response. Silent processing (user clicks, nothing happens) is never acceptable. If the full action takes longer than 2 seconds, a progress state must be communicated.

**INV-UX-02 — Streaming First Invariant**
All LLM-generated content displayed to users in the chat or spec preview interfaces must use streaming (token-by-token or chunk-by-chunk delivery). Blocking the UI while waiting for a complete LLM response to be assembled server-side before display is prohibited. If streaming cannot be supported for a particular output format (e.g., DOCX export), the system must show a deterministic progress indicator with a time estimate.

**INV-UX-03 — Lossless Recovery Invariant**
If a user's browser or session disconnects mid-generation, the system must be able to restore the last known state of the project and any partially generated specification upon reconnection. No in-progress work is lost due to a client disconnection. State recovery is implemented via server-side session persistence, not client-side caching.

**INV-UX-04 — Confidence Always Visible Invariant**
The confidence tier of every requirement displayed in the review UI must always be visible. Confidence information must not be hidden behind a toggle, collapsed by default, or removed from any export format. The confidence tag (`[INFERRED — VERIFY]`, etc.) must appear in exported DOCX, PDF, and Markdown outputs alongside the requirement text — until a human approves the requirement, at which point the tag may be removed from the final locked output.

**INV-UX-05 — Non-Destructive Edit Invariant**
No user interface action may result in permanent, unrecoverable data loss without a confirmation dialog that explicitly describes what will be deleted and provides a "Cancel" option. This applies to: deleting a project, removing a source document, rejecting a requirement, and clearing a chat session. Version history is always preserved — the user may be able to delete a project, but the audit log entry of the deletion is permanent.

---

## 7. Data Versioning & Immutability Invariants

**INV-VER-01 — Requirement Version Append-Only Invariant**
Every change to a Requirement's `description`, `status`, `confidence_score`, or `acceptance_criteria` must create a new entry in the `RequirementVersion` table. No update to a Requirement may overwrite version history. The `RequirementVersion` table is append-only; rows may never be deleted except via a compliance-triggered erasure that also records the erasure in the audit log.

**INV-VER-02 — Approved Spec Immutability Invariant**
A Specification in `approved` or `locked` status is immutable. Its `requirements`, `constraints`, and `assumptions` arrays must not be modified, added to, or removed from after the status is set. To make changes, a new Specification version must be created from the locked version as a baseline.

**INV-VER-03 — Source Chunk Tombstone Invariant**
When a source document is updated or superseded, its old chunks must be tombstoned (`is_active = false`, `valid_until = NOW()`) rather than hard-deleted. Hard deletion of chunks that are referenced by any existing Requirement is prohibited. The traceability chain from Requirement to source must remain queryable indefinitely for compliance and audit purposes.

**INV-VER-04 — No Retroactive Spec Modification Invariant**
The system must not retroactively modify a Specification that has already been exported or delivered to a client. If an error is discovered in an exported specification, the correct response is: create a new Specification version, correct the error, export the new version, and notify all recipients. The original export is preserved in its original form.

---

## 8. Compliance & Regulatory Invariants

**INV-COMP-01 — Data Residency Invariant**
If a workspace has a configured `data_residency` setting (e.g., `eu`), all data storage, vector embedding, and LLM processing for that workspace must occur within the specified geographic boundary. LLM API calls must route to the appropriate regional endpoint (e.g., Azure OpenAI EU deployment). No data from an EU-residency workspace may transit through or be stored in US-based infrastructure.

**INV-COMP-02 — Right-to-Erasure Invariant**
Upon a verified GDPR right-to-erasure request, all personal data attributable to the requesting individual must be scrubbed from: document content, chunk text, requirement descriptions, session messages, and user records. Scrubbing replaces content with `[ERASED — GDPR Art. 17 — {date}]`. The erasure is recorded in the audit log. Vector embeddings derived from erased content must be deleted from the vector store. The erased data is not recoverable.

**INV-COMP-03 — HIPAA PHI Non-Embedding Invariant**
If a workspace is flagged as `compliance_flags: ["HIPAA"]`, the PII scrubbing module must be extended to detect Protected Health Information (PHI) categories: patient names, dates of birth, medical record numbers, diagnoses, treatment plans. Detected PHI must be redacted before any embedding operation. Under no circumstances may PHI from a HIPAA-scoped workspace be embedded in plain text into the vector store.

**INV-COMP-04 — Audit Trail Completeness Invariant**
For any specification that has been exported, delivered, or locked, the system must be able to produce a complete, unbroken audit trail showing: (a) every source document ingested, (b) every agent call made, (c) every requirement generated and by which agent, (d) every human edit with the before/after diff, (e) every approval and by whom, and (f) the final export event. This audit trail must be queryable and exportable on demand for regulatory review.

---

## 9. Model Selection & Fallback Invariants

**INV-MODEL-01 — Fallback Chain Completeness Invariant**
The LLM model router must have a complete, configured fallback chain before any project processing begins. A configuration state where the primary provider is configured but no fallback is defined is an invalid system configuration that must be rejected at startup. The fallback chain must include at minimum: one primary provider, one secondary provider (different vendor), and a policy for handling exhaustion of all fallbacks (queue for manual retry).

**INV-MODEL-02 — Model Tier Ceiling Invariant**
An agent may not call a model tier higher than its configured maximum without explicit elevated authorization. The Classification Agent is bounded to the `fast` tier; calling a `premium` model from the Classification Agent is a configuration violation. Model tier assignments are set per agent in the system configuration and may not be overridden by a prompt or user preference at runtime (only by a workspace admin changing the configuration).

**INV-MODEL-03 — Model Version Pinning Invariant**
All LLM calls must specify a pinned model version (e.g., `claude-sonnet-4-6`, not `claude-sonnet-latest`). Floating model aliases that resolve to different models over time are prohibited in production. Model version upgrades must be treated as a deployment event: tested against the evaluation dataset, confirmed to meet quality thresholds, and explicitly promoted to production. A model version that degrades specification quality below baseline thresholds must be rolled back.

**INV-MODEL-04 — Response Schema Validation Invariant**
Any agent that expects structured output from an LLM (e.g., a JSON array of requirements) must validate the response against the expected schema before writing it to the database. Invalid or malformed responses must be rejected and retried (up to 3 times) before escalating to a fallback behavior (human review). The system must never write structurally invalid data to the requirements store, even if the LLM produces it.

**INV-MODEL-05 — Embedding Model Consistency Invariant**
All chunks within a single vector namespace must be embedded using the same embedding model and the same embedding dimensions. Mixing embedding models within a single vector index (e.g., half the chunks embedded with `text-embedding-3-large` and half with `voyage-large-2`) produces invalid similarity comparisons and is strictly prohibited. If the embedding model is upgraded, a full re-embedding of all active chunks must be performed and the old vectors replaced before queries are issued against the new model.

---

> End of Document • Chitragupt Invariants • v2.0 • May 2026
