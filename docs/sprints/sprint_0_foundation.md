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

## 2. RAG Pipeline Architecture Decisions

Beyond individual tool selection, the team must define and document the RAG pipeline shape before any ingestion code is written. The following sub-decisions feed into the overall retrieval architecture ADR (ADR-005) and also inform the database schema (ADR-006).

### 2.1 Chunking Strategy

**Questions to answer:**
- How are documents segmented into chunks? (fixed size, recursive character split, structure-aware, semantic boundary detection)
- What is the target token size and overlap per chunk type?
- How are structured elements handled differently? (tables, numbered lists, headers, images)
- What is the minimum viable chunk size below which chunks are discarded or merged?

**Constraint:** The chunking strategy determines the granularity of traceability. INV-EPI-01 requires that every requirement links to at least one chunk — overly large chunks reduce citation precision.

### 2.2 Metadata Schema per Chunk

**Questions to answer:**
- What metadata fields are stored alongside each embedding for filtered retrieval?
- Which fields are mandatory filters on every query (never relaxed)?
- How is the trust tier (from `epistemology.md`) encoded and applied at retrieval time?

### 2.3 Context Assembly

**Questions to answer:**
- How are retrieved chunks ordered before being passed to the synthesis LLM?
- How is the token budget managed when retrieved context is large?
- How is the prompt structured to separate system instructions, schema definitions, source context, and the user query?
- Which parts of the prompt are candidates for LLM-provider-level prompt caching?

---

## 3. Project Scaffolding

The team must agree on and implement the following structural elements before Sprint 1 begins. The specific directory layout is a Sprint 0 deliverable, not a Sprint 0 pre-decision.

### 3.1 Required Top-Level Structure

The scaffold must include, at minimum:

- Application source directory with clear separation between: API layer, agent/orchestration layer, RAG pipeline components, ORM models, Pydantic schemas, and shared services
- Database migrations directory (managed by the chosen migration tool)
- Test directory with separate folders for unit, integration, and evaluation tests
- Infrastructure-as-code directory
- CI/CD workflow configuration
- Local development environment configuration (e.g., Docker Compose)

### 3.2 Required Configuration Patterns

- All secrets and environment-specific values in environment variables, never hardcoded
- A settings file (backed by environment variables) that exposes all configurable values with type validation
- A `.env.example` file documenting every required environment variable with a description and example value

---

## 4. Invariant Verification Tests

Sprint 0 must produce automated tests that verify the structural scaffolding of four critical invariants. These tests use a real database (not mocks) and must pass in CI.

| Test | Invariant Verified | What it proves |
| :--- | :--- | :--- |
| Tenant isolation test | INV-SEC-01 | A query executed in Tenant B's session returns 0 rows from Tenant A's data |
| No floating model alias test | INV-MODEL-03 | No model ID in the codebase contains a floating alias (e.g., `-latest`) |
| Grounding invariant test | INV-EPI-01 | Every requirement produced by a synthesis agent has a non-empty `source_chunks` array pointing to active DB records |
| Human override immutability test | INV-HITL-01 | A human-approved requirement description is unchanged after re-running synthesis on the same source documents |

---

## 5. Sprint 0 Deliverables

| # | Deliverable | Acceptance Criteria |
| :--- | :--- | :--- |
| D-01 | ADRs 001–011, one per decision area in Section 1 | Each ADR has Status, Context, Decision, and Consequences sections; all are merged to `main` |
| D-02 | Dependency manifest with all production and dev dependencies pinned to exact versions | No unpinned dependencies; `install` reproduces a deterministic environment |
| D-03 | Database migration covering all entities in `ontology.md` | Migration runs `upgrade` and `downgrade` cleanly on a fresh database; RLS enabled on all tenant tables |
| D-04 | LangGraph graph skeleton with typed state and stub nodes for each agent role | Graph executes end-to-end with static mock payloads; state transitions are observable in traces |
| D-05 | API skeleton with authentication middleware and tenant context injection | JWT middleware rejects requests missing required claims; a `GET /health` endpoint returns 200 |
| D-06 | 4 invariant integration tests | All 4 pass in CI against a real database |
| D-07 | CI/CD pipeline running on every PR | Lint → type check → unit tests → integration tests → build; failing pipeline blocks merge |
| D-08 | Observability connected to staging environment | At least one test trace visible with `tenant_id` and `project_id` span metadata |
| D-09 | Staging environment deployed and reachable | Application health check returns 200 from the staging load balancer |
| D-10 | Evaluation dataset: 3–5 historical requirement packages in structured JSON | Each file has `source_documents`, `ground_truth_requirements`, and `human_notes` fields |
| D-11 | `CLAUDE.md` onboarding guide at repo root | A new engineer can run local dev environment from scratch using only this guide |

---

## 6. Definition of Done

Sprint 0 is complete when **all** of the following are true:

- [ ] All 11 ADRs (ADR-001 through ADR-011) are written, reviewed, and merged to `main`
- [ ] All 11 deliverables (D-01 through D-11) are merged to `main`
- [ ] CI pipeline is green on `main`
- [ ] All 4 invariant tests pass in CI
- [ ] Staging environment is reachable and returning healthy responses
- [ ] At least one test trace is visible in the observability tool with correct tenant and project metadata
- [ ] No floating model alias exists anywhere in the codebase
- [ ] Strict type checking passes with 0 errors
- [ ] All team members can run the local development environment from scratch

---

> End of Sprint 0 Plan • Chitragupt • v4.0 • May 2026
