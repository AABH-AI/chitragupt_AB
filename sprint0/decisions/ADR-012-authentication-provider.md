# ADR-012: Authentication & Identity Provider

**Status:** OPEN
**Deciders:** Solutions Architect, Tech Lead
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-SEC-01 (tenant isolation — JWT must carry `tenant_id` claim, verified on every request), INV-COST-04 (free-tier protection — `plan_tier` claim checked at agent invocation time)

---

## Context

The system requires a production-grade authentication layer that covers four distinct scenarios:

1. **Email/password login** — baseline for all plan tiers
2. **Enterprise SSO (SAML 2.0)** — required for business and enterprise workspace plans (Okta, Azure AD, Google Workspace)
3. **Social login (OIDC/OAuth 2.0)** — convenience for non-enterprise users (Google, Microsoft, GitHub)
4. **API key authentication** — for programmatic ingestion, webhooks, and service-to-service calls

Every authenticated session must produce a JWT that carries: `user_id`, `tenant_id` (= `workspace_id`), `role`, and `plan_tier`. The API middleware verifies this JWT on every request and injects the tenant context into the database session (RLS enforcement, INV-SEC-01).

The decision is whether to build this authentication layer or buy it from a managed identity service.

## Decision Drivers

- SAML 2.0 support (enterprise plan requirement — cannot be deferred)
- OIDC / OAuth 2.0 support for social providers
- API key management (issuance, rotation, revocation, hashing at rest)
- JWT issued with custom claims (`tenant_id`, `role`, `plan_tier`) — not just a standard OIDC token
- Time to implement vs. build cost — auth is security-critical; bugs have severe consequences
- Data residency for auth data (user accounts, session tokens)
- Cost at expected user count
- Operational simplicity (password reset, email verification, MFA all managed externally)

## Considered Options

| Option | SAML | OIDC | API Keys | Custom JWT Claims | Managed | Cost |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Auth0** | ✅ | ✅ | Via Actions | ✅ Custom claims | ✅ | Free to 7,500 MAU; $23+/month |
| **AWS Cognito** | ✅ | ✅ | Via Lambda triggers | ✅ Custom attributes | ✅ | Free to 50K MAU; $0.0055/MAU after |
| **Clerk** | ✅ Enterprise | ✅ | ✅ | ✅ | ✅ | Free to 10K MAU; $25+/month |
| **Supabase Auth** | ❌ | ✅ | ✅ | Limited | ✅ | Free tier; $25+/month |
| **Firebase Auth** | ❌ | ✅ | ❌ | Limited | ✅ | Free to 10K/month |
| **Self-built (FastAPI + JWT)** | Must build | Must build | Must build | ✅ Full control | ❌ | Engineering cost only |

## Evaluation Matrix

| Criterion | Weight | Auth0 | AWS Cognito | Clerk | Self-built |
| :--- | :---: | :---: | :---: | :---: | :---: |
| SAML 2.0 support | 30% | | | | |
| Custom JWT claims (`tenant_id`, `plan_tier`) | 25% | | | | |
| API key management built-in | 15% | | | | |
| Operational simplicity (MFA, reset, verification) | 15% | | | | |
| Cost at expected MAU | 15% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix, then record the decision below.

**Chosen provider:**

**JWT claims required (must be present on every token):**
- `user_id`
- `tenant_id`
- `role`
- `plan_tier`
- `exp` (expiry)

**Token lifetime (access token):**

**Refresh token strategy:**

**API key storage (hashed with algorithm):**

**Rationale:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**
