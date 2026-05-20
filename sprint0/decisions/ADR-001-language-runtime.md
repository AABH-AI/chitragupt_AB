# ADR-001: Language & Runtime

**Status:** OPEN
**Deciders:** Tech Lead
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-PERF-02 (stateless agent invocation requires good async support)

---

## Context

The primary application language governs the entire engineering toolchain: which frameworks are available, what type safety is achievable, and how quickly the team can move. The agentic orchestration ecosystem (orchestration frameworks, LLM SDKs, vector store clients) has uneven support across languages — this is the dominant factor in the decision, not general-purpose language merit.

## Decision Drivers

- Maturity and feature-completeness of the LLM and agent orchestration SDK ecosystem
- Native async support (required for concurrent agent execution and streaming — INV-UX-02)
- Static type checking toolchain (reduces runtime errors in a system with complex data contracts)
- Team proficiency and ramp-up time
- Availability of document parsing libraries (PDF, DOCX, XLSX, audio transcription)

## Considered Options

| Option | Notes |
| :--- | :--- |
| **Python 3.11+** | Largest LLM/agent ecosystem; `asyncio` native; `mypy` for static typing; strong document parsing libraries |
| **TypeScript / Node.js** | Good ecosystem but LangGraph JS is secondary; fewer document parsing options |
| **Go** | Excellent performance and concurrency; minimal LLM SDK support; no viable agent orchestration framework |

## Evaluation Matrix

Score each option 1–5 per criterion. Multiply by weight. Sum for weighted total.

| Criterion | Weight | Python 3.11+ | TypeScript | Go |
| :--- | :---: | :---: | :---: | :---: |
| LLM/agent ecosystem maturity | 40% | | | |
| Async & concurrency model | 20% | | | |
| Static type safety | 20% | | | |
| Team proficiency | 10% | | | |
| Document parsing library depth | 10% | | | |
| **Weighted Total** | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix above, then record the decision below.

**Chosen option:**

**Rationale:**

**Pinned version:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**
