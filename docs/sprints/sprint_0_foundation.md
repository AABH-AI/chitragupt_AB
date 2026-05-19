# Sprint 0 Plan: Foundation, Ontology & Technology Selection

**Phase:** Architecture Kickoff & Technology Setup
**Duration:** 2 Weeks (Milestone 0)
**Objective:** Finalize all technology selections, relational schemas, vector schemas, and deployment scaffolding. Create a type-safe database migration and establish our core evaluation benchmark dataset.

---

## 1. Technical Goals & Scope

Sprint 0 is dedicated to setting up the project's foundation. No functional RAG code is written yet. Instead, we establish the structural boundaries, database definitions, and test configurations.

### 1.1 Technology Decisions (Client Locked)

We align our stack strictly to the client's commercial and architectural constraints:

- **Primary Reasoning Model:** `claude-3-5-sonnet-20241022`
- **Fast / Classification Model:** `claude-3-5-haiku-20241022`
- **Fallback / Large Document Model:** `gemini-1.5-pro-002`
- **Orchestration Layer:** LangGraph (Python 3.11+)
- **Transactional Relational Database:** PostgreSQL 16 (with `pgvector` extension)
- **Embedding Model:** `text-embedding-3-large` or `voyage-large-2` (pinned to 1536 dimensions)
- **Deployment Platform:** AWS ECS Fargate behind an Application Load Balancer
- **CI/CD Pipeline:** GitHub Actions
- **Observability Suite:** Langfuse

### 1.2 Ontology Database Mapping

Using the unified ontology defined in `ontology.md`, we will draft and run initial database migrations.

- **Primary Entities:** `Workspace`, `User`, `Project`, `Document`, `Chunk`, `Requirement`, `Conflict`, `Gap`, `Specification`.
- **Cardinals and Keys:** Every table must carry a `tenant_id: UUID` column as the primary key suffix or filter key.
- **Relational Integrity:**
  - Chunks carry a `document_id` foreign key with `ON DELETE CASCADE`.
  - Requirements carry an array of `source_chunk_ids: UUID[]` or a join table `requirement_chunks`.

---

## 2. Key Deliverables & Action Items

### 2.1 Task: Database Migration Setup (SA Focus)

- **Goal:** Draft a clean, repeatable migrations directory using `Alembic` (Python).
- **Deliverable:** Database schema SQL migrations for PostgreSQL.
- **Implementation:** Enable Row-Level Security (RLS) on all transaction tables by default, with custom session variables (`app.current_tenant_id`) enforced on the pool.

### 2.2 Task: LangGraph Pipeline Scaffolding (Tech Lead Focus)

- **Goal:** Initialize the base workspace directory, configure `pyproject.toml` with poetry dependencies, and build a dummy LangGraph routing chart.
- **Deliverable:** LangGraph architecture setup with dummy nodes (`IngestNode`, `SynthesisNode`, `GapDetectNode`, `ReviewNode`) returning static JSON payloads.
- **Verification:** Ensure that states are passed cleanly and the graph executes without deadlocks.

### 2.3 Task: Evaluation Dataset Compilation (BA Focus)

- **Goal:** Gather and pre-seed a high-fidelity ground truth requirements benchmark.
- **Deliverable:** A static JSON dataset containing **5–10 historical requirements packages** (RFPs, manuals, chats) coupled with their corresponding high-quality, human-curated specifications.
- **Value:** This serves as our automated semantic quality gate for all model and prompt iterations in later sprints.

### 2.4 Task: Observability Integration (DevOps Focus)

- **Goal:** Deploy a secure, staging-hosted instance of `Langfuse` in our AWS environment.
- **Deliverable:** Piped tracing connection from our LangGraph executor setup to the Langfuse API.

---

## 3. Invariants to Enforce & Verify

During Sprint 0, we must write automated unit tests to verify the structural scaffolding of our invariants:

- **Model Version Pinning Invariant (INV-MODEL-03):** Assert in client configuration tests that no floating aliases (`-latest`) exist in the settings file.
- **Tenant Isolation Scaffolding (INV-SEC-01):** Run an initial DB test asserting that queries run without setting `app.current_tenant_id` throw a permission exception or return exactly 0 rows.

---

## 4. Definition of Done & Quality Gate

- [x] All 44 unknowns resolved in `unknowns_and_stakeholder_queries.md`.
- [x] Database migrations written, tested, and pushed to remote main.
- [x] LangGraph dummy pipeline runs cleanly under concurrent local simulation.
- [x] Ground truth evaluation dataset structured as static JSON and checked into source control.
- [x] Langfuse observability is actively catching client traces on staging.
- [x] CI/CD pipeline is initialized in GitHub Actions, running linting and mypy tests on every PR.

---

> End of Sprint 0 Plan • Chitragupt • v2.0 • May 2026
