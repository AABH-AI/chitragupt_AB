# Sprint 4 Plan: Integrations & Export

**Phase:** Enterprise Ecosystem Connectivity
**Duration:** 2 Weeks (Milestone 4)
**Objective:** Build enterprise integrations connecting the system to external requirement sources (Jira, Confluence, Linear). Develop high-fidelity Microsoft Word (DOCX) and PDF export formatting engines, and set up outbound system webhooks.

---

## 1. Technical Goals & Scope

Sprint 4 transitions Chitragupt from a standalone web tool into an integrated platform. We connect to external data silos where product backlogs and company document wikis are managed.

### 1.1 Integration Scope

- **Jira Cloud:** OAuth 2.0 connection.
  - **Read:** Ingest existing high-level Epics and requirements.
  - **Write:** Push approved User Stories and Gherkin criteria directly to Jira backlogs.
- **Confluence Cloud:** OAuth 2.0 connection.
  - **Read:** Parse wiki documentation URLs with advanced HTML-to-text extraction.
- **Export Formats:** MS Word (DOCX) template matching company style-guides, and standard vector PDF.
- **Rate Limit Handling:** Automated sliding window rate-limiter with token bucket algorithms for Jira and Confluence client APIs.

---

## 2. Key Deliverables & Action Items

### 2.1 Task: Jira Read/Write Client (Integration Focus)

- **Goal:** Develop the Jira integration connector.
- **Read Workflow:** Import Epics, fetch description text and child tickets, and pipe them into the ingestion queue.
- **Write Workflow:** Expose a button `Push to Jira` on the dashboard. Upon click, format and push approved requirements as separate User Stories linked under their parent epic.
- **Invariant Enforcement (INV-HITL-02):** Under no circumstances can the system auto-create or auto-push tickets without explicit human approval.

### 2.2 Task: Confluence Ingestion & Staleness Check (Integration Focus)

- **Goal:** Build the Confluence page parser.
- **Staleness Tracking:** Expose background polling logic (runs every 30 minutes) that checks Confluence page modification timestamps. If a change is found, trigger a **Staleness Alert** in the UI prompting BAs to manually confirm re-ingestion.

### 2.3 Task: DOCX & PDF Formatting Engines (Backend Focus)

- **Goal:** Build export modules that construct beautiful, structured Microsoft Word files from Markdown specifications using professional styles, headers, and footer components.
- **Deliverables:** `DocxExportService` and `PdfExportService`.
- **Traceability Matrix:** Include a structured summary table appended to the end of exported specs mapping requirement codes to source document properties.

### 2.4 Task: Outbound Webhooks & Events (Backend Focus)

- **Goal:** Build transactional event hooks.
- **Deliverable:** Expose subscription management for outbound POST hooks: `spec.completed`, `conflict.raised`, `gap.raised`, `requirement.approved`.

---

## 3. Invariants to Enforce & Verify

- **Human-Approved Pushes (INV-HITL-02):** Write unit tests validating that the Jira write integration module throws an assertion exception if triggered in a headless execution context without active session user credentials.
- **Rate Limit Backoff:** Verify via mock integration tests that when a third-party API returns a HTTP 429 status, the client catches the code and executes an exponential backoff with random jitter.

---

## 4. Definition of Done & Quality Gate

- [x] Jira OAuth 2.0 integration successfully imports Epics and pushes generated stories.
- [x] Confluence page HTML parser extracts structured text and detects document staleness.
- [x] Slid-window token bucket rate-limiters protect client credentials from blacklisting.
- [x] Word Document (DOCX) and PDF exports match Markdown specifications 1:1.
- [x] Outbound system webhooks successfully fire on spec locked states.
- [x] **Quality Gate:** Bulk requirement integration import on a 20-epic mock project finishes in under **5 minutes** without rate-limiting failures.

---

> End of Sprint 4 Plan • Chitragupt • v2.0 • May 2026
