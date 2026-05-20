# ADR-008: Object Storage

**Status:** OPEN
**Deciders:** Solutions Architect, DevOps
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-SEC-03 (file storage isolation — `/{tenant_id}/{project_id}/` prefix enforced), INV-VER-03 (source chunk tombstone — raw files must be retained even after chunks are tombstoned), INV-COMP-01 (data residency — storage must comply with workspace's configured region)

**Depends on:** ADR-009 (deployment platform constrains available storage services)

---

## Context

Every raw document uploaded to the system must be stored durably before ingestion begins. The storage system is responsible for:

- Receiving uploaded files (PDF, DOCX, XLSX, audio, video, images)
- Enforcing path-based tenant isolation: `/{tenant_id}/{project_id}/{document_id}`
- Generating presigned URLs scoped to a single object (download, not directory listing)
- Retaining files for the workspace's configured retention period
- Supporting WORM (Write Once Read Many) for locked specification exports

A user from Tenant A must never receive a URL that resolves to Tenant B's file, regardless of whether they know the path (INV-SEC-03). This must be enforced by the storage service — not just the application layer.

## Decision Drivers

- Path-based tenant isolation enforceable at the storage service layer
- Presigned URL generation scoped to exact object (not prefix or bucket)
- Managed service — no self-hosted storage infrastructure
- Multi-region / data residency options (INV-COMP-01)
- WORM / Object Lock support (for locked specification archives)
- Cost at expected storage volume and transfer rate
- Integration with the chosen cloud provider (ADR-009)

## Considered Options

| Option | Provider | Path Isolation | Presigned URLs | Object Lock | Multi-region | Egress Cost |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **AWS S3** | AWS | ✅ IAM prefix policies | ✅ | ✅ S3 Object Lock | ✅ | $0.09/GB |
| **Google Cloud Storage** | GCP | ✅ IAM conditions | ✅ | ✅ Retention policies | ✅ | $0.12/GB |
| **Azure Blob Storage** | Azure | ✅ SAS tokens | ✅ | ✅ Immutability policies | ✅ | $0.08/GB |
| **Cloudflare R2** | Cloudflare | ✅ Custom domain + tokens | ✅ | ❌ | Limited | $0.00 (no egress) |
| **Backblaze B2** | Backblaze | ✅ | ✅ | ❌ | Limited | $0.01/GB |

## Evaluation Matrix

| Criterion | Weight | AWS S3 | GCP Cloud Storage | Azure Blob | Cloudflare R2 |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Path isolation enforceability | 25% | | | | |
| Object Lock / WORM support | 20% | | | | |
| Integration with deployment platform | 20% | | | | |
| Multi-region / data residency | 20% | | | | |
| Cost (storage + egress) | 15% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix, then record the decision below.

**Chosen service:**

**Bucket / container naming convention:**
`{service}://{bucket-name}/{tenant_id}/{project_id}/{document_id}`

**Retention policy (default):**

**Object Lock for locked specifications:** Yes / No

**Rationale:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**
