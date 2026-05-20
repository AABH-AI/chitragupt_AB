# ADR-010: Observability Stack

**Status:** OPEN
**Deciders:** Tech Lead, DevOps
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-COST-01 (project budget cap — requires real-time cost tracking), INV-COST-02 (workspace monthly budget cap), INV-COST-03 (cost attribution — every LLM call attributed before issued)

---

## Context

The observability stack must serve two distinct purposes that generic APM tools do not handle well together:

1. **LLM-specific telemetry** — token counts, model IDs, prompt/completion content (truncated for cost), latency per call, cost attribution, cache hit/miss, fallback activations. This is the primary signal for the budget cap invariants.
2. **Infrastructure telemetry** — container CPU/memory, API latency percentiles, error rates, DB query latency.

The LLM telemetry requirement is the harder one. It must capture per-trace metadata (`tenant_id`, `project_id`, `agent_name`, `model_id`) and aggregate it in real time so the budget cap circuit breaker can query it. Off-the-shelf APM tools (Datadog, New Relic) do not natively model LLM cost per project.

## Decision Drivers

- Native LLM observability: token counts, model IDs, prompt/completion capture per trace
- Per-tenant and per-project cost attribution at query time (required by INV-COST-03)
- Real-time alerting when budget thresholds are approached (80%) and reached (100%) (INV-COST-01, INV-COST-02)
- Data retention and privacy posture — LLM prompt content may contain client requirement data; must be handled appropriately
- Self-hosted vs. managed tradeoff (self-hosted increases ops burden but gives full data control)
- Integration with the chosen orchestration framework (ADR-002)
- Cost of the observability service itself

## Considered Options

### LLM Tracing (primary concern)

| Option | LLM-native | Per-project cost | Self-hosted option | Managed option | Privacy posture |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Langfuse** | ✅ | ✅ | ✅ | ✅ Cloud | Configurable; prompts stored; review data residency |
| **LangSmith** | ✅ | Partial | ❌ | ✅ Cloud | LangChain-coupled; US-hosted |
| **Helicone** | ✅ | ✅ | ✅ | ✅ Cloud | Proxy-based; good cost tracking |
| **Custom (OpenTelemetry + Grafana)** | ❌ (manual) | Manual | ✅ | ✅ Grafana Cloud | Full control; high build cost |
| **Arize Phoenix** | ✅ | Partial | ✅ | ✅ | Good for eval; lighter on ops metrics |

### Infrastructure Metrics (secondary concern)

| Option | Container metrics | Alerting | Managed | Notes |
| :--- | :--- | :--- | :--- | :--- |
| **Cloud provider native** (CloudWatch, GCP Monitoring, Azure Monitor) | ✅ | ✅ | ✅ | Free with compute; limited LLM support |
| **Datadog** | ✅ | ✅ | ✅ | Expensive; LLM observability add-on |
| **Grafana Cloud** | ✅ | ✅ | ✅ | Open; can pair with Langfuse |

## Evaluation Matrix — LLM Tracing

| Criterion | Weight | Langfuse | LangSmith | Helicone | Custom OTel |
| :--- | :---: | :---: | :---: | :---: | :---: |
| LLM-native telemetry (tokens, cost, model) | 30% | | | | |
| Per-project cost attribution at query time | 25% | | | | |
| Self-hosted option for data residency | 20% | | | | |
| Alerting on budget thresholds | 15% | | | | |
| Build/integration cost | 10% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix, then record the decision below.

**LLM tracing tool:**

**Infrastructure metrics tool:**

**Self-hosted or managed:**

**Data residency posture for prompt content:**

**Rationale:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**
