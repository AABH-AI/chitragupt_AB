# Sprint 2 Plan: Synthesis & Elicitation — The Agentic Layer

**Phase:** Multi-Agent Orchestration & Core AI Reasoning
**Duration:** 2 Weeks (Milestone 2)
**Objective:** Implement the multi-agent reasoning graph using LangGraph. Introduce the Synthesis Agent to generate requirement drafts from vectors, the Elicitation Agent to discover gap checklist questions, and the Conflict/Gap Detection agents to flag inconsistencies.

---

## 1. Technical Goals & Scope

Sprint 2 transitions our raw vectors into a dynamic, stateful AI reasoning ecosystem. We implement the core agent nodes and link them into a deterministic graph.

### 1.1 Multi-Agent Flow

- **Orchestrator:** LangGraph state engine managing session data.
- **Synthesis Node:** Retrieves relevant chunks and generates Agile User Stories with explicit confidence scores.
- **Classification Node:** Segregates generated items into Functional, NFR, Constraint, and Assumption.
- **Gap Detection Node:** Audits the current requirements draft against our pre-seeded domain completeness checklists.
- **Conflict Detection Node:** Checks for contradicting source chunks and flags inconsistencies.
- **Elicitation Node:** Batches all discovered gaps into an "Open Questions Checklist" at the end of the analysis.

---

## 2. Key Deliverables & Action Items

### 2.1 Task: LangGraph Node Implementations (Tech Lead Focus)

- **Goal:** Replace dummy Sprint 0 nodes with active, functional LLM clients.
- **Deliverables:**
  - `SynthesisAgentNode`: Calls Claude 3.5 Sonnet to draft Agile User Stories (`"As an [Actor]..."`).
  - `ClassificationAgentNode`: Uses Claude 3.5 Haiku to quickly classify categories.
- **Prompt Caching:** Enable static prompt header caching on all nodes to keep API context costs optimized.

### 2.2 Task: Gap & Conflict Detection Agents (AI Focus)

- **Goal:** Build the logical verification agents.
- **Gap Detection:** Compiles incomplete taxonomy items (missing Gherkin BDD, missing citations, or missing actors) into the `Gap` entity table.
- **Conflict Detection:** Compares chunk semantic coordinates. If two retrieved chunks with different properties contradict (e.g., conflicting API SLAs), flag the requirement with `[CONFLICT DETECTED — PENDING]` status.

### 2.3 Task: Budget Cap & Circuit Breakers (Backend Focus)

- **Goal:** Implement strict token and financial tracking (**INV-COST-01**).
- **Implementation:**
  - Log every LLM call into `llm_call_logs`.
  - Prior to executing any LangGraph node, calculate the accumulated project cost.
  - If project cost exceeds the **$20.00 project cap**, suspend execution instantly, raise a webhook event, and alert the user.

### 2.4 Task: Core Chat UI (Frontend Focus)

- **Goal:** Build the elicitation chat panel.
- **Deliverable:** Streamed message window displaying progress indicator logs ("Ingesting...", "Analyzing...") alongside the batched "Open Questions Checklist" once generation runs complete.

---

## 3. Invariants to Enforce & Verify

- **Traceability Invariant (INV-EPI-01):** Every generated requirement in the database must possess at least one active vector coordinate mapping inside the `requirement_chunks` join table. Grounded synthesis is strictly enforced.
- **Cost Cap Circuit Breaker (INV-COST-01):** Write integration unit tests simulating a rogue loop; verify that the executor suspends nodes immediately when the project cost reaches 100% of the cap.

---

## 4. Definition of Done & Quality Gate

- [x] LangGraph orchestration graph executes fully, successfully passing states across nodes.
- [x] Synthesis, Classification, Gap, and Conflict agents are operational.
- [x] Inline prompt caching is active and verified via Langfuse headers.
- [x] Financial circuit breaker (INV-COST-01) suspended-state triggers work flawlessly.
- [x] Chat interface displays elicitation streams and batched question blocks.
- [x] **Quality Gate:** End-to-end regression tests on the evaluation dataset demonstrate:
  - $\ge 80\%$ recall of ground-truth human requirements.
  - $\le 15\%$ false positive generation rate.

---

> End of Sprint 2 Plan • Chitragupt • v2.0 • May 2026
