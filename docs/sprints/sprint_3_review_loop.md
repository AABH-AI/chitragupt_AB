# Sprint 3 Plan: Output & Review Loop

**Phase:** Human-in-the-Loop & Export Engines
**Duration:** 2 Weeks (Milestone 3)
**Objective:** Construct the Specification Writer Agent to assemble requirements into formatted templates. Build the review dashboard with inline edit capabilities, conflict resolution panels, requirement version tracking, and Markdown file generation.

---

## 1. Technical Goals & Scope

Sprint 3 shifts the product experience to the Business Analyst. We construct the tools that let humans audit, modify, and lock down AI-synthesized specifications.

### 1.1 The Human-in-the-Loop Paradigm

- **Specification Writer:** Consolidates active database entries into a cohesive document using general or domain-specific templates.
- **Approve/Reject Cycle:** Single-item review triggers. approved requirements are marked `BA Approved` and locked.
- **Human Override Invariant (INV-HITL-01):** Human edits serve as absolute ground truth and must never be overwritten during subsequent agentic re-runs.
- **Scoped Re-generation:** Re-runs can only target draft or modified sections, preserving human progress across rest of document (**INV-HITL-03**).

---

## 2. Key Deliverables & Action Items

### 2.1 Task: Specification Writer Agent (AI Focus)

- **Goal:** Write the assembly agent that formats stories, priority tags, actors, source citations, and Gherkin BDD criteria into professional Markdown document layouts.
- **Deliverable:** `SpecWriterAgentNode` compiling clean output schemas.

### 2.2 Task: Review UI Dashboard (Frontend Focus)

- **Goal:** Build the interactive requirement inspection board.
- **Deliverables:**
  - Collapsible functional sections with color-coded status badges: `[HIGH CONFIDENCE]` (green), `[INFERRED - REVIEW]` (amber), `[CONFLICT]` (red).
  - Hover tooltips showing natural language citations mapping directly to source PDF excerpts.
  - Quick action toolbar: **Approve**, **Reject**, and **Edit Inline** buttons next to every story block.

### 2.3 Task: Conflict Resolution Comparison Panel (Frontend/Backend Focus)

- **Goal:** Operationalize our conflict resolution interface.
- **Deliverable:** Side-by-side view panel showing conflicting source text (Source A vs. Source B) with metadata, prompting BAs with `Accept A`, `Accept B`, or `Manual Override` actions. Executing an action clears the conflict flag instantly.

### 2.4 Task: Versioning & Document Lock (Backend Focus)

- **Goal:** Implement audit trails and version entities.
- **Deliverables:**
  - Create the `RequirementVersion` database table to track a full audit trail of changes.
  - Implement a `Lock Specification` endpoint that freezes a project, sets its status to `locked`, and exports it.

---

## 3. Invariants to Enforce & Verify

- **Human Override Invariant (INV-HITL-01):** Run integration tests that modify a requirement, mark it approved, and then trigger a complete synthesis re-run. Assert that the human modification remains preserved.
- **Scoped Re-generation (INV-HITL-03):** Verify that re-runs only consume context tokens and regenerate requirement entities for unchecked/draft items, keeping database transactions isolated.

---

## 4. Definition of Done & Quality Gate

- [x] Specification Writer Agent generates clean Markdown specifications.
- [x] Collapsible review dashboard with hover tooltips and action toolbar is fully functional.
- [x] Conflict resolution side-by-side comparison screen is fully integrated and tested.
- [x] Audit trails track all modifications in the `RequirementVersion` entity.
- [x] Markdown export download works seamlessly on locked project specifications.
- [x] **Quality Gate:** A panel of domain BAs accepts $\ge 75\%$ of generated specifications without requiring critical structural revisions.

---

> End of Sprint 3 Plan • Chitragupt • v2.0 • May 2026
