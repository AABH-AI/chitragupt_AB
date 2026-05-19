# Sprint 5 Plan: Security, Compliance & Multi-Tenancy Hardening

**Phase:** Enterprise Security Hardening & Regulatory Compliance
**Duration:** 2 Weeks (Milestone 5)
**Objective:** Harden the system for multi-tenant SaaS production security. Enable strict PostgreSQL Row-Level Security, integrate automated PII scrubbing prior to vector embeddings, construct immutable audit logs, set up OIDC Single Sign-On, and build geographic data residency routing pathways.

---

## 1. Technical Goals & Scope

Sprint 5 focuses on meeting the compliance demands of our enterprise banking and European clients. We harden our data isolation, build audit logging evidence trails, and integrate automated data redaction.

### 1.1 Compliance Bounds

- **Data Classification:** Confidential / Internal (Restricted) targeting SOC 2 Type II readiness.
- **Tenancy:** Physically isolated databases or strict row-level schema logical walls (**INV-SEC-01**).
- **Data Residency:** Automatic routing of EU-based workspace workloads to EU AWS infrastructure (`eu-west-1`) (**INV-COMP-01**).
- **Privacy Rules:** Automated preprocessing scrubbing of sensitive identifiers (SSNs, cards, phones, personal emails) (**INV-SEC-02**).

---

## 2. Key Deliverables & Action Items

### 2.1 Task: PostgreSQL RLS Verification (DB/Security Focus)

- **Goal:** Activate and enforce RLS policies on all workspace tables.
- **Verification:** Implement automated test suites simulating active cross-tenant query injections, asserting that Tenant B queries never retrieve Tenant A database rows.

### 2.2 Task: Automated PII Preprocessing Scans (Security Focus)

- **Goal:** Build the pre-embedding PII redaction pipeline.
- **Implementation:**
  - Create a PII detector using Named Entity Recognition (NER) and regex templates.
  - Prior to chunking and embedding, identify emails, phone numbers, SSNs, and credit card patterns, replacing them with `[PII_REDACTED]` (**INV-SEC-02**).
  - Store the raw source files in S3 buckets isolated strictly under subfolders partitioned by `tenant_id` (**INV-SEC-03**).

### 2.3 Task: Geographic Data Residency Routing (DevOps Focus)

- **Goal:** Set up regional API and data routing.
- **Implementation:**
  - Read the incoming workspace's region flag.
  - If the workspace is flagged as European (EU), route all transaction databases, S3 uploads, embeddings, and LLM API calls strictly to EU infrastructure endpoints (**INV-COMP-01**).

### 2.4 Task: Immutable Audit Logs & OIDC (Backend Focus)

- **Goal:** Build audit trails for SOC 2 Type II verification and establish enterprise SSO.
- **Deliverables:**
  - Create an append-only, immutable `audit_logs` database table tracking all human modifications, approvals, exports, and login events (**INV-SEC-04**).
  - Integrate OpenID Connect (OIDC) SSO support for Google Workspace, Okta, and Microsoft Azure AD.

---

## 3. Invariants to Enforce & Verify

- **PII Scrubbing Invariant (INV-SEC-02):** Write unit tests asserting that raw data inputs containing test SSNs and email coordinates generate vector chunks with those identifiers strictly replaced by `[PII_REDACTED]`.
- **Audit Log Immutability (INV-SEC-04):** Ensure that the database user role assigned to the application layer lacks permissions to update or delete rows within the `audit_logs` table.

---

## 4. Definition of Done & Quality Gate

- [x] PostgreSQL Row-Level Security policies active across all tables.
- [x] Automated PII scrubbing redaction scans run on all uploads prior to embedding.
- [x] S3 bucket storage paths are partitioned and verified as tenant-isolated.
- [x] OIDC Single Sign-On is fully operational for Google, Okta, and Azure AD.
- [x] Geographic data residency routing redirects EU tenant processing to EU endpoints.
- [x] Immutable audit logs capture all administrative and review actions.
- [x] **Quality Gate:** Cross-tenant RLS regression tests pass at $100\%$ accuracy, with zero database co-mingling under simulated concurrent user lookups.

---

> End of Sprint 5 Plan • Chitragupt • v2.0 • May 2026
