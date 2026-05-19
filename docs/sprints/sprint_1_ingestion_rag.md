# Sprint 1 Plan: Core Ingestion & Retrieval — The RAG Baseline

**Phase:** RAG Ingestion Engine Build
**Duration:** 2 Weeks (Milestone 1)
**Objective:** Construct the automated ingestion pipeline that parses PDF, DOCX, and text source files, splits them into semantic chunks with overlapping context, embeds them using a 1536-dimensional model, and stores them securely in a tenant-isolated pgvector database.

---

## 1. Technical Goals & Scope

Sprint 1 is dedicated to building the "ground truth" ingestion layer. The RAG retrieval pipeline must be operational and baseline quality metrics must be quantified before any generative agents are introduced in Sprint 2.

### 1.1 Ingestion Specs

- **Day 1 File Formats:** Text-based PDF, DOCX, and free-text inputs. (Scanned PDFs requiring heavy visual OCR are deferred to Sprint 2).
- **Chunking Strategy:** Semantic-aware paragraph chunking with a target size of **300–600 tokens** and a **15% token overlap**.
- **Vector Schema:** pgvector configuration with standard Cosine Distance lookups (`<=>`).
- **Deduplication:** Project-level SHA-256 file hash comparison. Identical file hashes within the same project space are blocked at ingestion.

---

## 2. Key Deliverables & Action Items

### 2.1 Task: Document Parser Module (Backend Focus)

- **Goal:** Write modular parsing classes for PDF extraction (using `PyPDF` or `pdfplumber` with table awareness) and DOCX (using `python-docx` to extract styled tables and headings).
- **Deliverable:** `DocumentParser` utility yielding plain text segments coupled with heading path context and estimated page coordinates.

### 2.2 Task: Semantic Chunker & Embedder (AI Focus)

- **Goal:** Write a robust context-aware chunking class.
- **Deliverable:** `SemanticChunker` that respects logical boundaries (paragraphs, headings) rather than raw token limits, generating a clean payload array.
- **Embedding:** Connect to `text-embedding-3-large` (configured at 1536 dimensions) or `voyage-large-2` to generate vector representations of each chunk.

### 2.3 Task: pgvector Schema & Tenant RLS Execution (DB Focus)

- **Goal:** Execute the `Chunk` table migration and establish Row-Level Security policies.
- **Deliverable:** Database tables:
  
  ```sql
  CREATE TABLE chunks (
      chunk_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
      tenant_id UUID NOT NULL,
      document_id UUID NOT NULL REFERENCES documents(document_id) ON DELETE CASCADE,
      content TEXT NOT NULL,
      embedding VECTOR(1536) NOT NULL,
      metadata JSONB NOT NULL DEFAULT '{}'
  );
  ```

- **Tenancy:** Assert that all active vector search queries map directly through PostgreSQL RLS using the current tenant's ID context.

### 2.4 Task: Semantic Search Retrieval API (API Focus)

- **Goal:** Expose an API endpoint `POST /api/projects/{project_id}/search` for similarity matching.
- **Deliverable:** Semantic search handler returning the top-K chunks (default K=5) that cross a strict similarity score of 0.65.

---

## 3. Invariants to Enforce & Verify

- **Tenant Isolation Invariant (INV-SEC-01):** We must write automated tests in our build pipeline verifying that a retrieval query executed by Tenant B *never* returns vector chunks belonging to Tenant A, even under identical query strings.
- **File Storage Isolation (INV-SEC-03):** Raw files uploaded by a workspace must be stored in private S3 bucket prefixes isolated strictly by `tenant_id`.

---

## 4. Definition of Done & Quality Gate

- [x] Document parsing support for text-based PDF, DOCX, and text is operational.
- [x] Semantic chunking pipeline generates consistent outputs with 15% overlap.
- [x] SHA-256 deduplication blocks redundant file uploads within a project scope.
- [x] pgvector table created with RLS enabled; cross-tenant leakage unit tests pass.
- [x] **Quality Gate:** Retrieval Precision@5 reaches $\ge 0.70$ when evaluated against the ground-truth benchmark dataset compiled in Sprint 0.
- [x] Total ingestion time for a 50-page PDF document is verified under **60 seconds**.

---

> End of Sprint 1 Plan • Chitragupt • v2.0 • May 2026
