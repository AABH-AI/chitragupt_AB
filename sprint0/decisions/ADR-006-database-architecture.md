# ADR-006: Database Architecture

**Status:** OPEN
**Deciders:** Solutions Architect
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-SEC-01 (tenant isolation enforced at DB layer via RLS), INV-SEC-04 (audit log immutability), INV-MODEL-05 (embedding consistency — one vector index per namespace), INV-VER-01 through INV-VER-04 (versioning and immutability)

**Depends on:** ADR-004 (embedding dimensions determine vector column width), ADR-005 (retrieval strategy determines whether sparse vectors are needed alongside dense)

---

## Context

The system requires two distinct data storage concerns:

1. **Relational data** — entities from `ontology.md`: Workspaces, Projects, Users, Documents, Requirements, Conflicts, Gaps, Specifications, Audit Logs, LLM Call Logs, and their relationships.
2. **Vector data** — dense float embeddings per chunk, with filterable metadata, for semantic similarity search.

These can be served by the same database (if the relational DB supports a vector extension) or by separate systems. The key tension is between operational simplicity (fewer systems to manage) and specialization (dedicated vector DBs offer richer ANN indexing options).

The non-negotiable constraint is that **Row-Level Security must be enforceable at the database layer** — tenant isolation that depends solely on application-layer filtering is insufficient (INV-SEC-01). This requirement strongly favors a relational database with RLS support as the source of truth.

## Decision Drivers

- Row-Level Security enforceable at the DB engine level (INV-SEC-01 — application bug must not be able to leak tenant data)
- Filtered vector similarity search with mandatory filters: `tenant_id`, `project_id`, `is_active`, `valid_until`
- Ability to run ACID transactions across relational and vector writes (chunk insert + document status update must be atomic)
- Managed service availability (reduces ops burden)
- Cost at expected data volume (chunks × embedding dimensions)
- HNSW index support for sub-second ANN search at scale (>50K vectors)
- Sparse vector support (if hybrid retrieval is chosen in ADR-005)
- Data residency options

## Considered Options

### Combined (relational + vector in one system)

| Option | RLS Support | Vector Extension | HNSW | Sparse Vector | Managed Service | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **PostgreSQL + pgvector** | ✅ Native | ✅ pgvector | ✅ v0.7+ | Partial (jsonb) | ✅ RDS, Supabase, Neon | Single system; transactional consistency; RLS on same tables as vectors |
| **PostgreSQL + pg_embedding** | ✅ Native | ✅ HNSW-native | ✅ | ❌ | Limited | Less mature than pgvector |

### Split (relational + dedicated vector DB)

| Option | Vector DB | RLS | Tenant Isolation Approach | Cross-DB Join | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| PostgreSQL + Pinecone | Pinecone | ✅ (PG only) | Pinecone namespace per tenant | Application-layer | $70+/month; no relational joins |
| PostgreSQL + Qdrant | Qdrant | ✅ (PG only) | Qdrant collection per tenant | Application-layer | Self-hosted or managed; strong ANN |
| PostgreSQL + Weaviate | Weaviate | ✅ (PG only) | Weaviate tenant classes | Application-layer | Managed option; higher cost |

## Evaluation Matrix

| Criterion | Weight | PG + pgvector | PG + Pinecone | PG + Qdrant |
| :--- | :---: | :---: | :---: | :---: |
| RLS enforceable across all data | 30% | | | |
| Transactional consistency (relational + vector writes) | 20% | | | |
| Filtered ANN performance at scale | 20% | | | |
| Operational simplicity (number of systems) | 15% | | | |
| Cost at expected volume | 15% | | | |
| **Weighted Total** | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix, then record the decision below.

**Chosen architecture:**

**Relational database (product + version):**

**Vector storage (same system or separate product + version):**

**Managed service / hosting:**

**Rationale:**

## Schema Implications

Once the DB is chosen, the following schema constraints apply regardless:

- Every tenant-scoped table must have a `tenant_id UUID NOT NULL` column
- RLS policy must be created in the same migration as the table
- Chunk embeddings must be stored as a fixed-dimension vector column (dimension decided in ADR-004)
- HNSW index must be provisioned when the vector table exceeds 50,000 active rows
- The `audit_log` table must use an append-only role — no UPDATE or DELETE permissions

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**

**Migration strategy if we later need to change:**
