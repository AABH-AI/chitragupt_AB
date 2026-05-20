# ADR-002: Agentic Orchestration Framework

**Status:** OPEN
**Deciders:** Tech Lead
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-PERF-01 (deterministic retrieval), INV-PERF-02 (stateless agents), INV-HITL-01 through INV-HITL-04 (human-in-the-loop interrupts)

**Depends on:** ADR-001 (language choice constrains available frameworks)

---

## Context

The orchestration framework is the runtime that coordinates all agents in the pipeline — ingestion, classification, synthesis, conflict detection, gap analysis, and human review. It must model the pipeline as an explicit, inspectable graph where each node is a discrete step with defined inputs and outputs. This is a structural requirement, not a preference: without an explicit graph, traceability (INV-EPI-01) and human interrupt points (INV-HITL-01) cannot be implemented reliably.

## Decision Drivers

- Explicit, inspectable state machine with typed state transitions (required by INV-PERF-01 and INV-PERF-02)
- First-class support for human-in-the-loop interrupt points — agent execution must be pausable and resumable (INV-HITL-01 through INV-HITL-04)
- Stateless agent invocation — all context loaded from external state, not agent memory (INV-PERF-02)
- Observability integration — each node execution must be traceable
- Horizontal scalability — multiple concurrent graph executions for different projects/sessions
- Vendor lock-in risk and open-source sustainability

## Considered Options

| Option | Notes |
| :--- | :--- |
| **LangGraph** | Explicit directed graph; native interrupt support; typed `TypedDict` state; strong Anthropic/OpenAI SDK integration |
| **CrewAI** | Role-based agent abstraction; less explicit graph; limited interrupt support |
| **AutoGen** | Research-oriented; good for multi-agent conversations; not production-hardened for SaaS multi-tenancy |
| **Custom state machine** | Full control; high build cost; no community support |
| **Prefect / Temporal** | Workflow orchestrators with durable execution; not LLM-native; no built-in HITL for AI outputs |

## Evaluation Matrix

| Criterion | Weight | LangGraph | CrewAI | AutoGen | Custom |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Explicit inspectable graph | 25% | | | | |
| HITL interrupt support | 25% | | | | |
| Stateless invocation model | 20% | | | | |
| Observability integration | 15% | | | | |
| Production maturity & community | 15% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix above, then record the decision below.

**Chosen option:**

**Rationale:**

**Pinned version:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**
