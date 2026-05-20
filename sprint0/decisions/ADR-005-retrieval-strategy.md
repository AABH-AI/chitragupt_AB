# ADR-005: Retrieval Strategy

**Status:** OPEN
**Deciders:** Tech Lead
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-PERF-01 (deterministic retrieval — same query must return same ranked results), INV-EPI-01 (traceability — retrieval is the source of chunk citations)

**Depends on:** ADR-004 (embedding model choice determines dense retrieval quality), ADR-006 (database choice determines what retrieval modes are available)

---

## Context

The retrieval strategy determines how relevant chunks are selected from the vector store for each synthesis query. The choice has a direct, measurable impact on requirement quality — missed chunks become missing requirements; irrelevant chunks become noise in the synthesis context.

Two fundamental retrieval modes exist and can be combined:

- **Dense (ANN):** Embedding similarity — good for semantic and conceptual matches, poor at exact string matches
- **Sparse (BM25/keyword):** Term frequency — good for exact strings (requirement IDs, regulatory clause numbers, named entities), poor at paraphrase

Business requirement documents contain both: prose describing intent (semantic) and specific identifiers, code references, and clause numbers (keyword). This is the primary question this ADR must answer.

A re-ranking step (cross-encoder) can be added after initial retrieval to improve precision, at the cost of additional latency (~100–200ms).

## Decision Drivers

- Precision on exact-match queries (requirement IDs, regulation references, technical identifiers) — dense-only retrieval typically misses these
- Precision on semantic queries (conceptual similarity, paraphrase) — sparse-only retrieval misses these
- Determinism — the retrieval result must be reproducible given the same database state (INV-PERF-01)
- Latency budget — retrieval must complete within the overall response time target
- Complexity of maintaining dual indexes in production
- Whether a re-ranking step meaningfully improves top-K precision in this domain

## Considered Options

| Option | Precision (Semantic) | Precision (Keyword) | Latency | Complexity |
| :--- | :--- | :--- | :--- | :--- |
| **Dense-only (ANN)** | High | Low | Low | Low |
| **Sparse-only (BM25)** | Low | High | Low | Low |
| **Hybrid (dense + BM25 + RRF)** | High | High | Medium | Medium |
| **Hybrid + cross-encoder re-ranking** | Very High | Very High | Medium-High | Medium-High |

**Reciprocal Rank Fusion (RRF)** is the standard fusion algorithm: `score = 1/(k + rank_dense) + 1/(k + rank_sparse)` where `k=60`. It is parameter-free and deterministic given the same inputs.

## Key Parameters to Decide

Regardless of which strategy is chosen, the following parameters must be locked:

| Parameter | Description | Options |
| :--- | :--- | :--- |
| `similarity_threshold` | Minimum cosine similarity; chunks below this are dropped as noise | 0.55 / 0.60 / 0.65 / 0.70 |
| `top_k_retrieval` | Number of candidates retrieved before re-ranking (if used) | 10 / 15 / 20 / 25 |
| `top_k_final` | Number of chunks entering the synthesis context after re-ranking | 5 / 8 / 10 / 12 |
| `trust_tier_boost` | Score multiplier per trust tier level | 0.03 / 0.05 / 0.08 per tier |

## Evaluation Matrix

| Criterion | Weight | Dense-only | Sparse-only | Hybrid | Hybrid + Rerank |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Semantic recall | 30% | | | | |
| Keyword/exact-match precision | 25% | | | | |
| Retrieval determinism | 20% | | | | |
| Latency budget fit | 15% | | | | |
| Operational complexity | 10% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix, agree on the key parameters, then record the decision below.

**Chosen strategy:**

**Key parameters (locked):**

| Parameter | Value |
| :--- | :--- |
| `similarity_threshold` | |
| `top_k_retrieval` | |
| `top_k_final` | |
| `trust_tier_boost` | |
| Re-ranking model (if used) | |

**Rationale:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**
