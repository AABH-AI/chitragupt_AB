# ADR-004: Embedding Model

**Status:** OPEN
**Deciders:** Tech Lead, Solutions Architect
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-MODEL-05 (embedding model consistency — once chosen, cannot be mixed within a namespace)

**Depends on:** ADR-003 (vendor preference may influence embedding provider choice)

---

## Context

The embedding model converts document chunks into dense float vectors stored in the vector database. This is the most consequential single technical decision in the RAG pipeline because **it cannot be changed after data is written without a full re-embedding of every chunk in every namespace**. Mixing two embedding models within the same vector index produces invalid similarity scores and is prohibited (INV-MODEL-05).

The model must be pinned at a specific version and dimension count on day one.

## Decision Drivers

- Retrieval quality on technical, domain-specific business prose (requirement documents, RFPs, compliance texts) — benchmark against MTEB retrieval tasks
- Native output dimensions — prefer models that do not require truncation; truncation introduces approximation error
- Cost per token at expected ingestion volume
- Data retention and privacy posture of the embedding API provider (same zero-retention requirement as LLM)
- Availability of a cross-encoder re-ranking model from the same vendor — matching training distribution improves re-ranking accuracy
- Failure posture: if the provider is unavailable, ingestion must queue and wait — it must not fall back to a different embedding model

## Considered Options

| Option | Provider | Dimensions | MTEB Retrieval | Cost / 1M tokens | Same-vendor Re-ranker | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **voyage-large-2** | Voyage AI | 1536 | High | ~$0.12 | ✅ voyage-rerank-2 | Purpose-built for retrieval; strong on technical text |
| **voyage-3** | Voyage AI | 1024 | Very High | ~$0.06 | ✅ voyage-rerank-2 | Newer; smaller dims; benchmark TBD |
| **text-embedding-3-large** | OpenAI | 3072 (pin to 1536) | High | ~$0.13 | ❌ (use Cohere) | Requires matryoshka truncation to 1536 |
| **text-embedding-3-small** | OpenAI | 1536 | Medium | ~$0.02 | ❌ | Lower quality; not suitable for production RAG |
| **embed-english-v3.0** | Cohere | 1024 | High | ~$0.10 | ✅ rerank-english-v3.0 | Strong on RAG tasks; shorter dims |
| **amazon-titan-embed-text-v2** | AWS | 1536 | Medium | ~$0.02 | ❌ | AWS-native; lower benchmark scores |

## Evaluation Matrix

| Criterion | Weight | voyage-large-2 | text-embedding-3-large | embed-english-v3.0 | amazon-titan-v2 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Retrieval quality (MTEB) | 35% | | | | |
| Native dimension (no truncation) | 15% | | | | |
| Same-vendor re-ranker available | 20% | | | | |
| Cost per 1M tokens | 15% | | | | |
| Privacy / zero-retention posture | 15% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix, then record the decision below.

**Chosen model:**

**Pinned model ID:**

**Dimension count (locked for all time):**

**Rationale:**

**Re-ranking model (paired):**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**

**Re-embedding cost if we ever need to change models:**
(estimate: number of expected chunks × dimension count × cost per token)
