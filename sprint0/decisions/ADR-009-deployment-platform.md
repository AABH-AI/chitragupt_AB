# ADR-009: Deployment Platform

**Status:** OPEN
**Deciders:** DevOps
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-UX-01 (response within 2 seconds — no cold starts on critical paths), INV-PERF-03 (graceful degradation — platform must support auto-restart and health checks), INV-COMP-01 (data residency — compute must run in configured region)

---

## Context

The application consists of two distinct workload types with different scaling profiles:

1. **API server** — handles HTTP requests, WebSocket connections for streaming, and serves the UI. Latency-sensitive. Must not cold-start on user-facing paths (INV-UX-01).
2. **Ingestion worker** — processes uploaded documents asynchronously (chunking, embedding, writing to DB). CPU and memory intensive, bursty, can tolerate cold starts.

The deployment platform must handle both workload types, ideally without maintaining two separate infrastructure stacks. Secrets management (API keys for LLM providers, DB credentials) must be handled by the platform or an adjacent managed service — never stored in environment variables in the container image.

## Decision Drivers

- Cold start latency for the API server path (streaming LLM responses require fast container readiness — INV-UX-01)
- Auto-scaling under variable load (ingestion jobs are bursty and CPU-intensive)
- Managed vs. self-hosted operational model (affects on-call burden)
- Secrets management integration (LLM API keys, DB credentials)
- Cost at baseline and peak load — baseline should be minimal (no idle cluster cost)
- Data residency compliance (INV-COMP-01) — must be deployable to specific cloud regions
- Integration with chosen CI/CD pipeline (ADR-011)

## Considered Options

| Option | Cold Start | Auto-scaling | Managed | Secrets Integration | Baseline Cost |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **AWS ECS Fargate** | ~10–30s (pre-warmed tasks avoid this) | ✅ Task count | ✅ | ✅ Secrets Manager | Pay per vCPU-second |
| **AWS Lambda + API GW** | 1–5s (warm) / longer (cold) | ✅ Instant | ✅ | ✅ Secrets Manager | Pay per invocation |
| **AWS EKS (Kubernetes)** | ~5–15s (pod schedule) | ✅ HPA | Partial | ✅ | EC2 node cost (always-on) |
| **Google Cloud Run** | ~1–3s | ✅ | ✅ | ✅ Secret Manager | Pay per request |
| **Azure Container Apps** | ~5–15s | ✅ | ✅ | ✅ Key Vault | Pay per vCPU-second |
| **Railway / Render** | ~10–30s | Limited | ✅ | Basic env vars | Fixed monthly |

## Evaluation Matrix

| Criterion | Weight | ECS Fargate | Lambda | EKS | Cloud Run |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Cold start for API server | 25% | | | | |
| Auto-scaling for ingestion workers | 20% | | | | |
| Operational simplicity | 20% | | | | |
| Secrets management integration | 20% | | | | |
| Cost at expected load | 15% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix, then record the decision below.

**Chosen platform:**

**API server configuration (min/max tasks or instances):**

**Ingestion worker configuration (scaling policy):**

**Cloud provider (determines ADR-007 and ADR-008 service options):**

**Cloud region(s) for launch:**

**Rationale:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**
