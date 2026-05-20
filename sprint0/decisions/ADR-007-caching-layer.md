# ADR-007: Caching Layer

**Status:** OPEN
**Deciders:** Solutions Architect, DevOps
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-PERF-02 (stateless agent invocation — session state must be stored externally, not in agent memory), INV-UX-03 (lossless recovery on disconnection — requires server-side session persistence)

**Depends on:** ADR-009 (deployment platform determines which managed cache services are available)

---

## Context

The caching layer serves three distinct roles that have different latency and consistency requirements:

1. **Session state cache** — active LangGraph graph state, serialized between agent node executions. Must be accessible within milliseconds so graph resumption is fast. TTL: idle session timeout (configurable, default 30 minutes).
2. **Idempotency keys** — prevent duplicate document ingestion when webhooks or API clients retry. TTL: 24 hours.
3. **Rate-limit counters** — per-tenant, per-project LLM call rate limiting. TTL: rolling 1-minute windows.

Without an external cache, agents cannot be stateless (INV-PERF-02) and browser disconnections will lose in-progress work (INV-UX-03).

## Decision Drivers

- Sub-millisecond read latency for session state (agent node resume must be fast)
- TTL-based automatic expiry (session state should expire after inactivity; idempotency keys after 24h)
- Atomic increment operations (required for rate-limit counters)
- Managed service availability on the chosen cloud provider (reduces ops burden)
- Data persistence option (session state should survive a cache restart, not be lost)
- Cost at expected concurrent session count

## Considered Options

| Option | Latency | TTL | Atomic Ops | Managed | Persistence | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Redis (managed)** | Sub-ms | ✅ | ✅ | ✅ (ElastiCache, Redis Cloud, Upstash) | ✅ AOF/RDB | Industry standard; rich data structures |
| **Redis (self-hosted)** | Sub-ms | ✅ | ✅ | ❌ | ✅ | More control; ops burden |
| **Memcached (managed)** | Sub-ms | ✅ | Limited | ✅ | ❌ | No persistence; no atomic complex ops |
| **DynamoDB** | ~1–5ms | ✅ TTL | Limited | ✅ | ✅ | Latency higher than Redis; overkill for simple cache |
| **In-memory (application)** | Sub-ms | Manual | ✅ | N/A | ❌ | Violates INV-PERF-02; no horizontal scale |

## Evaluation Matrix

| Criterion | Weight | Redis (managed) | Redis (self-hosted) | Memcached | DynamoDB |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Read latency (sub-ms) | 30% | | | | |
| TTL + persistence support | 25% | | | | |
| Managed service availability | 20% | | | | |
| Atomic operation support | 15% | | | | |
| Cost at expected scale | 10% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix, then record the decision below.

**Chosen option:**

**Managed service / provider:**

**Rationale:**

**Session state TTL (idle timeout):**

**Idempotency key TTL:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**
