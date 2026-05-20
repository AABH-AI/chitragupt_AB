# ADR-003: LLM Model Selection per Agent Role

**Status:** OPEN
**Deciders:** Tech Lead, Solutions Architect
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-MODEL-01 (fallback chain), INV-MODEL-02 (tier ceiling per agent), INV-MODEL-03 (pinned versions), INV-MODEL-04 (schema validation), INV-PERF-03 (graceful degradation)

---

## Context

Every agent in the pipeline must have a pinned model ID assigned before Sprint 1 begins. Floating aliases are prohibited in production (INV-MODEL-03). The model assignment also determines the fallback chain (INV-MODEL-01) and per-agent tier ceilings (INV-MODEL-02). This ADR covers all LLM roles: primary reasoning, fast classification, premium (if used), and fallback.

A zero-data-retention endpoint is mandatory for all providers — model training on client requirement documents would be a critical security and contractual breach.

## Agent Roles Requiring Assignment

| Role | Purpose | Tier Constraint |
| :--- | :--- | :--- |
| Classification / routing | Document type detection, intent classification, PII pre-scan | Fast — low cost, high throughput |
| Primary reasoning | Synthesis, conflict detection, gap analysis, context assembly | Quality — best cost/quality balance |
| Premium reasoning | Final specification lock review (if used at all) | Premium — gated by workspace plan tier |
| Vision / multimodal | Diagram and image content extraction | Must support image input |
| Fallback | Activated when primary provider unavailable | Must be a different vendor from primary |

## Decision Drivers

- Structured output reliability — agents produce JSON; the model must consistently return schema-valid output (INV-MODEL-04)
- Long-context reasoning quality — requirement corpora can be large; 128K+ context preferred
- Cost per token at expected volume (see budget axis)
- Zero data retention guarantee — enterprise-tier endpoint required
- Provider resilience and rate limit posture — primary and fallback must be different vendors (INV-MODEL-01)
- Prompt caching support — reduces cost significantly for repeated system prompts

## Considered Options

### Primary / Fast / Premium Tier

| Provider | Model Family | Context Window | Zero Retention | Prompt Caching | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Anthropic** | Claude Opus / Sonnet / Haiku | 200K | ✅ Enterprise | ✅ | Strong structured output; good long-context |
| **OpenAI** | GPT-4o / GPT-4o-mini / o1 | 128K | ✅ Enterprise | ✅ | Strong ecosystem; structured output mode |
| **Google** | Gemini 2.0 Pro / Flash | 1M+ | ✅ Vertex AI | Partial | Largest context window; strong for large document batches |
| **Meta / Self-hosted** | Llama 3.x | Variable | ✅ (self-hosted) | Manual | Full control; significant infra cost and ops burden |
| **Cohere** | Command R+ | 128K | ✅ Enterprise | ✅ | RAG-optimized grounding; smaller ecosystem |

### Fallback Provider

Must be a different vendor from whichever is chosen as primary. At minimum one primary + one fallback vendor required (INV-MODEL-01).

## Model Assignment Worksheet

Fill in the chosen model ID for each role. IDs must be pinned (no `-latest` suffixes).

| Role | Chosen Model ID | Provider | Tier | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| Classification / routing | | | Fast | |
| Primary reasoning | | | Quality | |
| Premium reasoning | | | Premium | |
| Vision / multimodal | | | Quality | |
| Fallback (different vendor) | | | Quality | |

## Evaluation Matrix — Primary Reasoning Model

| Criterion | Weight | Anthropic Claude | OpenAI GPT-4o | Google Gemini |
| :--- | :---: | :---: | :---: | :---: |
| Structured JSON output reliability | 30% | | | |
| Long-context reasoning quality | 25% | | | |
| Cost per 1M tokens (input/output) | 20% | | | |
| Zero retention + security posture | 15% | | | |
| Prompt caching support | 10% | | | |
| **Weighted Total** | | | | |

## Decision

> **OPEN** — Complete the worksheets above, then record the decision below.

**Fallback chain:**

```
[Primary model] → [Fallback model (different vendor)] → dead-letter queue (human retry)
```

**Rationale:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**

**Cost estimate at expected volume:**
