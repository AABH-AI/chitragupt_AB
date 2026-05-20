# Sprint 0: Foundation, Technology Selection & Project Scaffolding

**Phase:** Architecture Kickoff & Technology Setup
**Duration:** 2 Weeks (Milestone 0)
**Sprint Goal:** Make every technology decision that subsequent sprints build on. Leave the sprint with a running skeleton — no business logic, no agents — but a system that connects, deploys, migrates, and observes. Every choice below is locked; changes require an Architecture Decision Record (ADR).

---

## 0. How to Read This Document

Each decision section follows this pattern: **What** we chose → **Why** (the decisive factor, not a list of pros) → **What we rejected** and why. Budget, security, and operational complexity are the three axes that broke every tie.

---

## 1. Decision Framework

Before evaluating any tool, we weighted every choice on three axes:

| Axis | Weight | Definition |
| :--- | :---: | :--- |
| **Security** | 40% | Tenant isolation, data residency, no-training guarantees, compliance posture |
| **Budget** | 35% | Total cost of ownership: hosting + API + engineer hours to operate |
| **Operational Simplicity** | 25% | Fewer moving parts, managed services over self-hosted, reduces on-call burden |

A choice that scores poorly on Security is disqualified regardless of score on other axes. This reflects the system's primary invariants (INV-SEC-01 through INV-SEC-05).

---

## 2. Technology Stack Decisions

### 2.1 Language & Runtime

**Chosen:** Python 3.11 (pinned via `.python-version`)

**Why:** LangGraph, the Anthropic SDK, and the Voyage AI client are Python-first. Typing discipline via `mypy --strict` eliminates the usual Python reliability concerns. No polyglot penalty.

**Rejected:** TypeScript — LangGraph JS is a secondary citizen; ecosystem is ahead in Python.

### 2.2 Web Framework & API Layer

**Chosen:** FastAPI 0.111.x + Uvicorn 0.30.x

**Why:** Async from the ground up matches our streaming-first invariant (INV-UX-02). Pydantic v2 models serve double duty as API schemas and internal data validators. OpenAPI docs are free. Starlette middleware layer handles JWT injection for tenant context before any route handler runs.

**Rejected:** Django REST Framework — synchronous by default, heavier ORM, fights with our async LangGraph executor.

### 2.3 Agentic Orchestration

**Chosen:** LangGraph 0.2.x (from `langgraph` PyPI package)

**Why:** LangGraph models our multi-step pipeline as an explicit directed graph with typed state transitions. This satisfies INV-PERF-02 (stateless agent invocation — all state is in the graph state object, not agent memory) and INV-PERF-01 (deterministic retrieval via seeded graph execution). The interrupt mechanism is the implementation of HITL invariants (INV-HITL-01 through INV-HITL-05) — human approval is a first-class graph node, not an afterthought.

**Rejected:** CrewAI — hides the execution graph, making traceability (INV-EPI-01) difficult. Rejected AutoGen — research-oriented, not production-hardened for multi-tenant SaaS.

**Rejected:** Raw LangChain chains — LangGraph supersedes chains for stateful pipelines; we use LangChain components (document loaders, text splitters) only as utilities, not as the orchestration layer.

### 2.4 Relational Database

**Chosen:** PostgreSQL 16 with `pgvector` 0.7.x extension

**Why:** Combining relational and vector data in a single store eliminates the cross-database join problem. Row-Level Security (RLS) enforces INV-SEC-01 at the database layer — an application bug cannot leak tenant data because the DB refuses the query. Every table with `tenant_id` gets an RLS policy on day one. pgvector 0.7.x supports HNSW indexes and both dense and sparse vectors.

**Rejected:** Pinecone — no SQL for relational data, no RLS, cross-database join complexity for tenant isolation, additional monthly cost ($70+/month for production tier). Rejected Weaviate — same cross-DB problem plus self-hosted operational burden. Rejected Qdrant — solid vector DB but same tenant isolation challenge.

**Operational detail:** Hosted on **AWS RDS for PostgreSQL** (db.r7g.large baseline). RDS handles backups, patching, multi-AZ failover. No self-managed PostgreSQL cluster.

### 2.5 Caching Layer

**Chosen:** Redis 7.2 via **AWS ElastiCache for Redis** (Serverless tier)

**Why:** Three distinct use cases, one service: (1) LLM prompt caching metadata — tracking which system prompts are cached at the Anthropic layer so we can estimate savings; (2) session state warm cache — active LangGraph session state serialized to Redis for sub-millisecond graph resume; (3) idempotency keys — preventing duplicate document ingestion from webhook retries.

**Rejected:** In-memory caching — violates INV-PERF-02 (stateless agents). Rejected DynamoDB for session state — higher latency, more complex SDK.

### 2.6 Object Storage (Document Store)

**Chosen:** AWS S3 with per-tenant prefix isolation

**Why:** Enforces INV-SEC-03. Bucket structure: `s3://chitragupt-docs-{env}/{tenant_id}/{project_id}/{document_id}`. S3 presigned URLs are scoped to the exact object path; the API layer validates that the `tenant_id` in the path matches the JWT claim before issuing any presigned URL. S3 Object Lock on the bucket provides WORM compliance for locked specifications.

**Rejected:** Storing raw files in RDS/blob columns — performance, cost, and no path-based isolation.

### 2.7 Infrastructure & Deployment

**Chosen:** AWS ECS Fargate behind an Application Load Balancer (ALB)

**Why:** Serverless containers — we pay per vCPU-second, no idle cluster cost. The ALB provides TLS termination, health checks, and sticky sessions for streaming responses. Fargate eliminates EC2 patching. IAM task roles give each container least-privilege access to S3, RDS, and ElastiCache without managing credentials.

**Environments:** `dev` (single task), `staging` (2 tasks), `production` (auto-scaling 2–10 tasks based on ALB request count).

**Rejected:** AWS Lambda — cold starts are unacceptable for streaming LLM responses (INV-UX-01 requires response within 2 seconds). Rejected self-managed EKS — too much operational overhead for a 2-person DevOps function.

### 2.8 CI/CD Pipeline

**Chosen:** GitHub Actions

**Why:** Already integrated with the repository. Runners are free for public repos and reasonable cost for private. The ecosystem of pre-built actions covers our entire stack (ECR push, ECS deploy, Alembic migration). No separate CI server to manage.

**Pipeline stages (every PR):**

```
lint (black, isort, ruff) → typecheck (mypy --strict) → unit tests →
integration tests (real PostgreSQL via testcontainers) → security scan
(bandit, pip-audit) → docker build → push to ECR → deploy to staging →
smoke tests on staging
```

### 2.9 Observability

**Chosen:** Langfuse (cloud-hosted) + AWS CloudWatch (infrastructure metrics)

**Why:** Langfuse is purpose-built for LLM observability — it captures token counts, model IDs, latencies, prompt/completion pairs, and cost per trace at the project and tenant level. This directly feeds the `LLMCallLog` table we maintain internally. CloudWatch handles container CPU/memory metrics and ALB latency. Langfuse's tenant-scoped projects map 1:1 with our Workspace concept.

**Tracing architecture:** Every LangGraph node is wrapped with a Langfuse span. The `project_id` and `tenant_id` are injected as span metadata on every trace. This gives us per-tenant, per-project cost visibility without custom aggregation logic.

**Rejected:** LangSmith — tied to LangChain's ecosystem, no production-grade multi-tenant cost isolation. Rejected self-hosted Langfuse — eliminated for Sprint 0 to reduce setup cost; revisit at Sprint 5 (security/compliance sprint) if data residency requires it.

---

## 3. Model Selection

### 3.1 LLM Model Registry

All model IDs are pinned. Floating aliases (`-latest`, `-sonnet`) are prohibited in code (INV-MODEL-03). Changes require an ADR and a full evaluation dataset re-run before promotion to production.

| Role | Model ID | Provider | Tier | Max Tokens In | Cost (Input / Output) | Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Primary Reasoning** | `claude-sonnet-4-6` | Anthropic | Quality | 200K | $3 / $15 per 1M | Best cost/quality ratio for synthesis, conflict detection, gap analysis |
| **Premium Reasoning** | `claude-opus-4-7` | Anthropic | Premium | 200K | $15 / $75 per 1M | Reserved for final specification lock review only; not used in main pipeline |
| **Classification / Fast** | `claude-haiku-4-5-20251001` | Anthropic | Fast | 200K | $0.80 / $4 per 1M | Document classification, intent routing, PII detection pre-scan |
| **Fallback / Large Context** | `gemini-2.0-flash-001` | Google | Quality | 1M | $0.10 / $0.40 per 1M | Activated only when Anthropic returns 5xx/429 after 3 retries; massive context window for large document batches |

**Model routing rules (INV-MODEL-02):**

```
ClassificationAgent → claude-haiku-4-5-20251001 (hard ceiling: Fast tier)
IngestAgent         → claude-haiku-4-5-20251001 (document parsing, PII scan)
SynthesisAgent      → claude-sonnet-4-6          (hard ceiling: Quality tier)
ConflictAgent       → claude-sonnet-4-6          (hard ceiling: Quality tier)
GapDetectAgent      → claude-sonnet-4-6          (hard ceiling: Quality tier)
ReviewAgent         → claude-sonnet-4-6          (hard ceiling: Quality tier)
SpecLockReviewAgent → claude-opus-4-7            (elevated; workspace admin must enable)
```

**Fallback chain (INV-MODEL-01):** `claude-sonnet-4-6` → `gemini-2.0-flash-001` → dead-letter queue (human retry). The fallback fires only on 5xx or 429 after 3 retries with exponential backoff. Every fallback activation is logged in `LLMCallLog.fallback_used = true` and emits a Langfuse alert.

**Zero data retention:** All Anthropic API calls must include the header `anthropic-beta: zero-data-retention`. Google Vertex AI endpoint (not AI Studio) is used for Gemini to guarantee no training use. This is a configuration invariant — the SDK wrappers enforce it; no individual agent may opt out.

### 3.2 Embedding Model Decision

**Decision matrix for embedding selection:**

| Criterion | `text-embedding-3-large` (OpenAI) | `voyage-large-2` (Voyage AI) | `amazon-titan-embed-text-v2` (AWS) |
| :--- | :---: | :---: | :---: |
| MTEB retrieval benchmark | 54.9 | 56.1 | 51.3 |
| Technical / domain-specific text quality | Good | **Excellent** | Fair |
| Dimensions (native) | 3072 (we pin to 1536) | 1536 | 1536 |
| Cost per 1M tokens | $0.13 | $0.12 | $0.02 |
| Data residency options | US only | US / EU | AWS region (inherits) |
| Vendor dependency risk | OpenAI | Voyage AI | AWS |
| SDK maturity | High | Medium | High |

**Chosen:** `voyage-large-2` (Voyage AI) — pinned to 1536 dimensions

**Why:** Voyage AI consistently outperforms OpenAI embeddings on retrieval tasks involving technical and domain-specific prose, which is exactly our corpus (business requirement documents, RFPs, compliance texts). The quality delta at similar cost is decisive. The 1536-dimension native output eliminates the matryoshka truncation risk we would incur with text-embedding-3-large's 3072→1536 reduction.

**Rejected:** `text-embedding-3-large` — marginally lower retrieval quality for technical text at the same cost tier. Rejected `amazon-titan-embed-text-v2` — materially lower benchmark scores; AWS-native convenience does not justify quality loss on the retrieval pipeline.

**Fallback embedding:** If Voyage AI is unavailable (>3 failed calls), the ingestion pipeline is paused and queued. We do not fall back to a different embedding model mid-namespace — this would violate INV-MODEL-05 (embedding model consistency). A namespace mixing two embedding models produces meaningless similarity scores.

### 3.3 Re-ranking Model

**Chosen:** `voyage-rerank-2` (Voyage AI cross-encoder)

**Why:** Using the same vendor for embedding and re-ranking eliminates the semantic alignment mismatch that can occur when the bi-encoder (embedding model) and cross-encoder (re-ranker) were trained on different corpora. voyage-rerank-2 adds ~120ms of latency but improves top-5 precision by ~18% in our domain, which directly improves requirement quality.

**Trigger:** Re-ranking is applied only when initial retrieval returns ≥ 5 candidates. Single-candidate retrieval does not pay the latency cost.

---

## 4. RAG Pipeline Architecture

### 4.1 Pipeline Overview

```
[Source Document] → [Ingestion Agent]
                          │
                    ┌─────┴──────────────────────────┐
                    │         Pre-processing          │
                    │  PII scrub → format normalize   │
                    └─────┬──────────────────────────┘
                          │
                    ┌─────▼──────────────────────────┐
                    │    Structure-Aware Chunking     │
                    │  section → paragraph → fallback │
                    └─────┬──────────────────────────┘
                          │
                    ┌─────▼──────────────────────────┐
                    │    Dual Embedding Generation    │
                    │  dense (voyage-large-2) +       │
                    │  sparse (BM25 via pg_sparse)    │
                    └─────┬──────────────────────────┘
                          │
                    ┌─────▼──────────────────────────┐
                    │   pgvector Write (with RLS)     │
                    │  chunk + metadata + embeddings  │
                    └─────────────────────────────────┘

[Synthesis Request] → [Query Router]
                          │
                    ┌─────▼──────────────────────────┐
                    │   Hybrid Retrieval              │
                    │  dense ANN + BM25 sparse        │
                    │  → RRF fusion → top-20 results  │
                    └─────┬──────────────────────────┘
                          │
                    ┌─────▼──────────────────────────┐
                    │   voyage-rerank-2               │
                    │  top-20 → re-ranked top-8       │
                    └─────┬──────────────────────────┘
                          │
                    ┌─────▼──────────────────────────┐
                    │   Context Assembly              │
                    │  trust tier sort + token budget │
                    └─────┬──────────────────────────┘
                          │
                    ┌─────▼──────────────────────────┐
                    │   Synthesis Agent               │
                    │  claude-sonnet-4-6              │
                    │  → structured JSON output       │
                    └─────┬──────────────────────────┘
                          │
                    ┌─────▼──────────────────────────┐
                    │   Schema Validation (INV-MODEL-04)│
                    │  Pydantic → DB write             │
                    └─────────────────────────────────┘
```

### 4.2 Chunking Strategy

The chunking approach is **document-structure-aware with semantic fallback**. A single fixed-size chunker produces semantically incoherent chunks when applied to business documents with headings, numbered requirements lists, and tables.

**Chunking hierarchy (applied in priority order):**

| Priority | Trigger | Strategy | Target Size | Overlap |
| :---: | :--- | :--- | :--- | :--- |
| 1 | Document has heading structure (PDF outline, DOCX headings, Markdown `#`) | **Section chunking** — each section heading + its body is a candidate chunk | ≤ 600 tokens | None (sections are natural boundaries) |
| 2 | Section > 600 tokens | **Recursive paragraph split** within the section | 400–600 tokens | 50 tokens |
| 3 | No heading structure detected | **Recursive character split** with sentence boundary preservation | 512 tokens | 64 tokens |
| 4 | Table detected | **Row-group chunking** — groups of 3–5 table rows per chunk, with header row repeated | ≤ 400 tokens | Header row repeated |
| 5 | Visual/image element | **Vision extraction** → paragraph-chunked text with `source_type: visual_extraction` | Variable | None |

**Chunk minimum size:** 50 tokens. Chunks below this threshold are merged with the adjacent chunk. Tiny chunks produce noisy embeddings with low discriminative value.

**Metadata enriched per chunk (stored in pgvector metadata column, used for filtered retrieval):**

```python
{
    "chunk_id": str,           # UUID
    "document_id": str,        # UUID
    "project_id": str,         # UUID — mandatory retrieval filter
    "tenant_id": str,          # UUID — mandatory retrieval filter (RLS also enforces)
    "source_type": str,        # pdf | docx | txt | xlsx | confluence_url | ...
    "trust_tier": int,         # 1–5 from epistemology hierarchy
    "page_number": int | None,
    "section_title": str | None,
    "chunk_index": int,        # ordinal within parent document
    "token_count": int,
    "valid_from": str,         # ISO 8601 timestamp
    "valid_until": str | None, # set on tombstone
    "is_active": bool,         # false = tombstoned
    "confidence_modifier": float,  # -0.15 for visual_extraction
}
```

### 4.3 Embedding Strategy

**Dense embedding:** `voyage-large-2` via Voyage AI API. Called in batches of 96 chunks (Voyage AI batch limit). Embedding dimension: 1536. Output is a `vector(1536)` column in PostgreSQL.

**Sparse embedding (BM25):** Generated via the `rank_bm25` Python library during ingestion. The BM25 term-frequency vector is stored as a `jsonb` column (`sparse_vector`) for hybrid retrieval. This enables keyword-exact matching, which is critical for requirement IDs, regulatory clause numbers, and technical identifiers that dense models can miss.

**Prompt caching for embeddings:** Voyage AI's batch API supports prompt caching across a session. For document re-ingestion (e.g., a revised PDF), only changed chunks are re-embedded. The `file_hash` (SHA-256) on the `Document` entity detects unchanged documents and skips re-embedding entirely.

### 4.4 Vector Store Architecture (pgvector)

**Table structure:**

```sql
-- The primary vector table
CREATE TABLE chunks (
    chunk_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id     UUID NOT NULL REFERENCES documents(document_id),
    project_id      UUID NOT NULL,
    tenant_id       UUID NOT NULL,
    content         TEXT NOT NULL,
    embedding       vector(1536) NOT NULL,
    sparse_vector   JSONB,          -- BM25 term weights
    chunk_index     INTEGER NOT NULL,
    token_count     INTEGER NOT NULL,
    page_number     INTEGER,
    section_title   TEXT,
    source_type     TEXT NOT NULL,
    trust_tier      SMALLINT NOT NULL CHECK (trust_tier BETWEEN 1 AND 5),
    confidence_modifier FLOAT DEFAULT 0.0,
    valid_from      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    valid_until     TIMESTAMPTZ,
    is_active       BOOLEAN NOT NULL DEFAULT TRUE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- RLS (INV-SEC-01)
ALTER TABLE chunks ENABLE ROW LEVEL SECURITY;
CREATE POLICY tenant_isolation ON chunks
    USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', TRUE), '')::UUID);

-- HNSW index for cosine similarity (provisioned when > 50K rows per INV-PERF-01)
CREATE INDEX CONCURRENTLY chunks_embedding_hnsw_idx
    ON chunks USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Composite index for mandatory metadata filters
CREATE INDEX chunks_project_active_idx
    ON chunks (project_id, is_active, valid_until)
    WHERE is_active = TRUE;
```

### 4.5 Retrieval Strategy

**Mandatory filters on every retrieval query (never relaxed):**

```python
filters = {
    "tenant_id": current_tenant_id,    # RLS enforces this at DB level too
    "project_id": current_project_id,
    "is_active": True,
    "valid_until": None,               # OR valid_until > NOW()
}
```

**Retrieval algorithm: Hybrid Search with RRF**

1. **Dense ANN query:** Top-20 chunks by cosine similarity to query embedding. Threshold: similarity ≥ 0.65 (lower scores are semantic noise — excluded per conventions).
2. **Sparse BM25 query:** Top-20 chunks by BM25 keyword score against query tokens.
3. **RRF Fusion:** Reciprocal Rank Fusion merges both ranked lists:
   ```
   RRF_score(chunk) = 1/(k + rank_dense) + 1/(k + rank_sparse)   where k=60
   ```
4. **Trust tier boost:** Multiply RRF score by `(1 + (5 - trust_tier) * 0.05)`. Tier-2 sources get a 15% boost; Tier-5 sources get 0% boost.
5. **Confidence modifier:** Multiply by `(1 + confidence_modifier)`. Visual extractions are penalized by 15%.
6. **Final ranked list:** Top-20 candidates passed to re-ranker.

**K limit:** Maximum 8 chunks enter the synthesis context after re-ranking (INV-PERF-01 and token budget). This is a hard ceiling — not a default.

### 4.6 Re-ranking

`voyage-rerank-2` receives the query and the top-20 candidate chunks (content text only, not metadata). It returns a re-ranked list of (chunk_id, score) pairs. We take top-8 by re-rank score.

**Re-ranking is skipped when:** retrieval returns ≤ 3 candidates (no benefit at that scale). In this case, all retrieved candidates enter synthesis.

### 4.7 Context Assembly

Before passing chunks to the synthesis LLM, the context is assembled as:

```
[SYSTEM PROMPT — cached at Anthropic layer]
[ONTOLOGY SCHEMA — cached at Anthropic layer]
[INVARIANTS SUMMARY — cached at Anthropic layer]

--- Source Context ---
[Chunk 1]
Source: {document_name}, Page {page}, Section "{section_title}"
Trust Tier: {trust_tier} | Confidence Modifier: {confidence_modifier}
Content: {content}

[Chunk 2] ...

--- End Source Context ---

[USER TASK / QUERY]
```

**Prompt caching:** The system prompt, ontology schema, and invariants summary are static per-session and are eligible for Anthropic's prompt caching (cache TTL: 5 minutes). On a typical synthesis session, 70–80% of the input tokens are cache hits, reducing effective cost by ~80% on those tokens.

**Token budget enforcement:** If the assembled context exceeds 140K tokens (leaving 60K for output), the lowest-scoring chunks are dropped until the budget is met. Context truncation is logged as a warning in Langfuse.

---

## 5. Complete Dependency Registry

All versions are pinned. Unpinned dependencies are not permitted in `pyproject.toml` production dependencies.

### 5.1 Core Runtime

```toml
[tool.poetry.dependencies]
python = "^3.11"

# Orchestration & Agents
langgraph = "0.2.28"
langchain-core = "0.2.39"
langchain-anthropic = "0.1.23"
langchain-community = "0.2.16"

# LLM Providers
anthropic = "0.34.2"
google-genai = "1.7.0"          # Gemini fallback

# Embedding & Reranking
voyageai = "0.3.2"

# Web Framework
fastapi = "0.111.1"
uvicorn = {version = "0.30.3", extras = ["standard"]}
pydantic = "2.8.2"
pydantic-settings = "2.4.0"

# Database
sqlalchemy = "2.0.32"
asyncpg = "0.29.0"
alembic = "1.13.2"
pgvector = "0.3.2"              # pgvector Python adapter

# Caching & Queue
redis = "5.0.8"
celery = "5.4.0"                # async task queue for ingestion jobs
kombu = "5.3.4"

# Object Storage
boto3 = "1.35.0"

# Document Parsing
pypdf = "4.3.1"                 # PDF extraction
python-docx = "1.1.2"          # DOCX extraction
openpyxl = "3.1.5"             # XLSX extraction
markdownify = "0.13.1"         # HTML→Markdown for web sources
pillow = "10.4.0"              # Image preprocessing

# Text Processing
tiktoken = "0.7.0"             # Token counting (OpenAI tokenizer — closest to voyage)
rank-bm25 = "0.2.2"           # BM25 sparse vector generation
langdetect = "1.0.9"           # Language detection for chunks

# Observability
langfuse = "2.41.1"

# Security
python-jose = {version = "3.3.0", extras = ["cryptography"]}
passlib = {version = "1.7.4", extras = ["bcrypt"]}

# HTTP
httpx = "0.27.0"
tenacity = "8.5.0"             # Retry logic with exponential backoff + jitter
```

### 5.2 Development & Test Dependencies

```toml
[tool.poetry.dev-dependencies]
# Code quality
black = "24.8.0"
isort = "5.13.2"
ruff = "0.5.7"
mypy = "1.11.1"

# Testing
pytest = "8.3.2"
pytest-asyncio = "0.23.8"
pytest-cov = "5.0.0"
testcontainers = {version = "4.8.0", extras = ["postgres", "redis"]}
httpx = "0.27.0"               # TestClient for FastAPI

# Security scanning
bandit = "1.7.9"
pip-audit = "2.7.3"

# Type stubs
types-redis = "4.6.0.20241004"
types-boto3 = "1.35.0"
boto3-stubs = {version = "1.35.0", extras = ["s3", "ecs"]}
```

### 5.3 Infrastructure Dependencies

| Component | Service | Version / Tier |
| :--- | :--- | :--- |
| PostgreSQL | AWS RDS | 16.4 |
| pgvector extension | RDS custom parameter group | 0.7.4 |
| Redis | AWS ElastiCache Serverless | Redis 7.2 compatible |
| Container runtime | AWS ECS Fargate | Platform 1.4.0 |
| Container registry | AWS ECR | — |
| Load balancer | AWS ALB | — |
| Object storage | AWS S3 | Standard + Intelligent Tiering |
| Secrets management | AWS Secrets Manager | — |
| CI runner | GitHub Actions Ubuntu | ubuntu-22.04 |
| Observability | Langfuse Cloud | v2.x |

---

## 6. Project Directory Structure

```
chitragupt/
├── .github/
│   └── workflows/
│       ├── ci.yml              # PR checks: lint, type, test, build
│       └── deploy.yml          # Push to main: staging deploy + smoke tests
│
├── alembic/
│   ├── env.py                  # Alembic async env with RLS session injection
│   ├── versions/               # Migration files — one per schema change
│   └── alembic.ini
│
├── src/
│   └── chitragupt/
│       ├── __init__.py
│       │
│       ├── api/                # FastAPI routers & middleware
│       │   ├── middleware/
│       │   │   ├── auth.py     # JWT validation + tenant context injection
│       │   │   └── cost_guard.py  # Budget cap circuit breaker (INV-COST-01)
│       │   ├── routers/
│       │   │   ├── documents.py
│       │   │   ├── projects.py
│       │   │   ├── requirements.py
│       │   │   ├── sessions.py
│       │   │   └── specifications.py
│       │   └── app.py          # FastAPI app factory
│       │
│       ├── agents/             # LangGraph nodes — one file per agent
│       │   ├── state.py        # Canonical ChitraguptState TypedDict
│       │   ├── graph.py        # Graph assembly: nodes + edges + conditions
│       │   ├── ingest.py       # IngestAgent node
│       │   ├── synthesis.py    # SynthesisAgent node
│       │   ├── conflict.py     # ConflictAgent node
│       │   ├── gap_detect.py   # GapDetectAgent node
│       │   ├── review.py       # ReviewAgent node (HITL interrupt point)
│       │   └── classification.py  # ClassificationAgent node
│       │
│       ├── rag/                # RAG pipeline components
│       │   ├── chunking/
│       │   │   ├── base.py     # ChunkingStrategy abstract base
│       │   │   ├── section.py  # Section-aware chunker
│       │   │   ├── paragraph.py
│       │   │   ├── table.py
│       │   │   └── vision.py   # Vision extraction + chunking
│       │   ├── embedding.py    # Voyage AI embedding client wrapper
│       │   ├── retrieval.py    # Hybrid dense+sparse retrieval + RRF fusion
│       │   ├── reranking.py    # Voyage rerank-2 wrapper
│       │   ├── context.py      # Context assembly + token budget enforcement
│       │   └── pii.py          # PII scrubbing (INV-SEC-02)
│       │
│       ├── models/             # SQLAlchemy ORM models (map 1:1 with ontology.md)
│       │   ├── workspace.py
│       │   ├── project.py
│       │   ├── document.py
│       │   ├── chunk.py
│       │   ├── requirement.py
│       │   ├── requirement_version.py
│       │   ├── conflict.py
│       │   ├── gap.py
│       │   ├── specification.py
│       │   ├── audit_log.py
│       │   └── llm_call_log.py
│       │
│       ├── schemas/            # Pydantic v2 schemas for API and agent I/O
│       │   ├── requirement.py  # RequirementCreate, RequirementRead, etc.
│       │   ├── document.py
│       │   ├── specification.py
│       │   └── session.py
│       │
│       ├── services/           # Business logic (called by agents and API)
│       │   ├── db.py           # Async DB session factory + RLS context manager
│       │   ├── storage.py      # S3 presigned URL + upload/download
│       │   ├── cost.py         # LLM call logging + budget cap enforcement
│       │   └── llm.py          # LLM client factory with fallback chain + retry
│       │
│       ├── config.py           # Settings via pydantic-settings + env vars
│       └── telemetry.py        # Langfuse client factory + span helpers
│
├── tests/
│   ├── unit/
│   │   ├── test_chunking.py
│   │   ├── test_retrieval.py
│   │   ├── test_pii_scrub.py
│   │   └── test_cost_guard.py
│   ├── integration/
│   │   ├── test_tenant_isolation.py   # Verifies INV-SEC-01
│   │   ├── test_rls_policy.py
│   │   ├── test_grounding.py          # Verifies INV-EPI-01
│   │   └── test_human_override.py     # Verifies INV-HITL-01
│   └── evaluation/
│       └── dataset/
│           ├── README.md
│           └── sample_01.json         # Ground truth requirement sets
│
├── docker/
│   ├── Dockerfile
│   └── docker-compose.yml             # Local dev: postgres + redis + app
│
├── infra/                             # AWS CDK or Terraform (TBD in Sprint 0)
│   ├── ecs.tf
│   ├── rds.tf
│   ├── elasticache.tf
│   └── s3.tf
│
├── pyproject.toml
├── .python-version                    # Pinned: 3.11.9
├── .env.example
└── CLAUDE.md
```

---

## 7. Database Architecture

### 7.1 Migration Philosophy

Alembic manages all schema changes. Rules:
- Every migration is reversible (`upgrade` and `downgrade` both implemented)
- RLS policies are created in the same migration as the table
- No data migrations in the same file as schema migrations
- Migration files are squashed at each sprint boundary to keep history readable

### 7.2 Sprint 0 Initial Migration (`0001_initial_schema.py`)

The first migration creates the full entity graph from `ontology.md` in dependency order:

```
workspaces → users → domain_templates →
projects → stakeholders →
documents → chunks (+ pgvector column + HNSW index) →
requirements → requirement_versions →
constraints → assumptions → actors →
conflicts → gaps → specifications →
sessions → audit_log → llm_call_log
```

RLS is enabled on every table except `domain_templates` (system-managed, not tenant data) and `audit_log` (audit log uses a superuser append-only role, not a tenant-scoped connection).

### 7.3 Connection & Session Management

The application uses two PostgreSQL roles:

| Role | Purpose | Privileges |
| :--- | :--- | :--- |
| `chitragupt_app` | Normal application queries | SELECT, INSERT, UPDATE on tenant tables — subject to RLS |
| `chitragupt_migrator` | Alembic migrations | DDL, schema changes — bypasses RLS |

The `db.py` service wraps every application session in a context manager that sets `app.current_tenant_id` before any query executes:

```python
@asynccontextmanager
async def tenant_session(tenant_id: UUID) -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSession(engine) as session:
        await session.execute(
            text("SET LOCAL app.current_tenant_id = :tid"),
            {"tid": str(tenant_id)}
        )
        yield session
```

---

## 8. Invariant Test Suite (Sprint 0 Required)

Four integration tests must pass before Sprint 0 is complete. These tests use `testcontainers` to spin up a real PostgreSQL 16 instance with pgvector.

### INV-SEC-01: Tenant Isolation

```python
async def test_tenant_isolation():
    # Setup: two tenants, data only for tenant_a
    tenant_a, tenant_b = uuid4(), uuid4()
    async with tenant_session(tenant_a) as session:
        session.add(Chunk(..., tenant_id=tenant_a, content="Secret data"))
        await session.commit()

    # Assert: tenant_b session returns 0 rows
    async with tenant_session(tenant_b) as session:
        result = await session.execute(select(Chunk))
        assert len(result.scalars().all()) == 0
```

### INV-MODEL-03: No Floating Model Aliases

```python
def test_no_floating_model_aliases():
    from chitragupt.services.llm import AGENT_MODEL_MAP
    for agent_name, model_id in AGENT_MODEL_MAP.items():
        assert "latest" not in model_id, f"{agent_name} uses floating alias"
        assert model_id.count("-") >= 2, f"{agent_name} model ID lacks version pin: {model_id}"
```

### INV-EPI-01: Grounding Invariant

```python
async def test_all_requirements_are_grounded(synthesis_output):
    for req in synthesis_output.requirements:
        assert len(req.source_chunks) >= 1, \
            f"Requirement {req.req_code} has empty source_chunks — ungrounded output"
        for chunk_id in req.source_chunks:
            exists = await chunk_exists_and_active(chunk_id)
            assert exists, f"Chunk {chunk_id} referenced by {req.req_code} does not exist"
```

### INV-HITL-01: Human Override Immutability

```python
async def test_human_override_not_overwritten():
    req = await create_requirement(description="AI generated text")
    await approve_requirement(req.requirement_id, human_text="Human override text")

    # Re-run synthesis on same source documents
    await run_synthesis_agent(project_id=req.project_id)

    refreshed = await get_requirement(req.requirement_id)
    assert refreshed.description == "Human override text"
    assert refreshed.status == "human_approved"
```

---

## 9. Sprint 0 Deliverables

| # | Deliverable | Owner | Acceptance Criteria |
| :--- | :--- | :--- | :--- |
| D-01 | `pyproject.toml` with all pinned production + dev dependencies installed and resolved | Tech Lead | `poetry install` succeeds; `poetry check` passes |
| D-02 | Alembic initial migration (`0001_initial_schema.py`) covering all entities in `ontology.md` | SA | Migration runs `up` and `down` cleanly on fresh PostgreSQL 16 + pgvector |
| D-03 | Dummy LangGraph graph with typed `ChitraguptState` and 6 stub nodes | Tech Lead | Graph executes end-to-end with static mock payloads; no deadlocks |
| D-04 | FastAPI app skeleton with JWT middleware, tenant session injection, and `/health` endpoint | Tech Lead | `GET /health` returns 200; JWT middleware rejects requests missing `tenant_id` claim |
| D-05 | 4 invariant integration tests (INV-SEC-01, INV-MODEL-03, INV-EPI-01, INV-HITL-01) | QA | All 4 pass in CI against real PostgreSQL via testcontainers |
| D-06 | GitHub Actions CI pipeline (`ci.yml`) running lint → typecheck → unit tests → integration tests → docker build | DevOps | PR to `main` triggers full pipeline; red build blocks merge |
| D-07 | Langfuse project created with `tenant_id` and `project_id` as mandatory span metadata | DevOps | Test trace appears in Langfuse dashboard with correct metadata |
| D-08 | Evaluation dataset: 3–5 historical requirement packages (JSON format) in `tests/evaluation/dataset/` | BA | Each dataset file has `source_documents`, `ground_truth_requirements`, and `human_notes` keys |
| D-09 | AWS infrastructure: RDS + ElastiCache + ECR + ECS task definition provisioned in staging | DevOps | `GET /health` on staging ALB returns 200; RDS connection succeeds from ECS task |
| D-10 | `CLAUDE.md` at repo root with onboarding guide for new engineers | Tech Lead | Any new team member can run `docker-compose up` and see the app running locally |

---

## 10. Definition of Done

Sprint 0 is complete when **all** of the following are true:

- [ ] `poetry install` and `docker-compose up` work on a fresh machine with no prior setup
- [ ] All 10 deliverables (D-01 through D-10) are merged to `main`
- [ ] CI pipeline is green on `main`
- [ ] All 4 invariant tests pass in CI
- [ ] Staging environment is reachable at the staging ALB URL
- [ ] At least one test trace is visible in Langfuse with correct `tenant_id` and `project_id` span attributes
- [ ] No floating model alias exists anywhere in the codebase (`grep -r "latest" src/` returns 0 results)
- [ ] `mypy --strict src/` passes with 0 errors
- [ ] Architecture Decision Record (ADR) written for every major choice in this document

---

## 11. Architecture Decision Records (ADRs to Write)

Each technology decision above must be captured in a short ADR in `docs/decisions/`. ADR format: **Status** → **Context** → **Decision** → **Consequences**. This is not optional — ADRs are the institutional memory for why we made each choice, not the commit history.

| ADR ID | Decision |
| :--- | :--- |
| ADR-001 | pgvector over dedicated vector DB |
| ADR-002 | voyage-large-2 over text-embedding-3-large |
| ADR-003 | LangGraph over CrewAI / AutoGen |
| ADR-004 | ECS Fargate over Lambda / EKS |
| ADR-005 | Langfuse cloud over self-hosted |
| ADR-006 | Hybrid retrieval (dense + BM25 + RRF) over dense-only |
| ADR-007 | voyage-rerank-2 as cross-encoder re-ranker |
| ADR-008 | claude-sonnet-4-6 as primary reasoning model |
| ADR-009 | gemini-2.0-flash-001 as fallback provider |

---

> End of Sprint 0 Plan • Chitragupt • v3.0 • May 2026
