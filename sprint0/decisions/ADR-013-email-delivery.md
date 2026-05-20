# ADR-013: Notification & Email Delivery

**Status:** OPEN
**Deciders:** DevOps
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-COST-01 (budget cap — system must email owner when 80% and 100% thresholds are reached), INV-COST-02 (workspace monthly cap — same notification requirement)

---

## Context

The system sends transactional email for the following events:

| Event | Recipient | Urgency |
| :--- | :--- | :--- |
| Budget cap at 80% | Project owner + workspace admin | High |
| Budget cap at 100% (agent suspended) | Project owner + workspace admin | Critical |
| Conflict raised (human review needed) | Assigned reviewer | Medium |
| Approval request sent | Reviewer | Medium |
| Export complete | Requester | Low |
| Ingestion failure (after retries exhausted) | Project owner | High |
| Workspace monthly cap reached | Workspace admin | Critical |

Email is the only reliable out-of-band notification channel — in-app notifications require the user to have the browser open. Budget cap notifications in particular must reach the recipient even when no session is active.

This ADR covers transactional email only. In-app real-time notifications (WebSocket/SSE) and optional Slack/Teams integrations are handled at the application layer and do not require a separate vendor decision at Sprint 0.

## Decision Drivers

- Reliable delivery (transactional email, not marketing — must not land in spam)
- HTML template support (formatted emails with event detail, links, CTAs)
- Deliverability reputation and monitoring (bounce rate, spam score)
- REST API or SMTP integration (REST preferred for application integration)
- Cost at expected volume (estimate: 5–20 emails per project per week)
- Data residency — email content may reference project names; EU residency matters for GDPR workspaces
- Domain verification and DKIM/SPF/DMARC support

## Considered Options

| Option | REST API | Templates | Deliverability | Free Tier | Cost / 1K emails | EU Region |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **SendGrid** | ✅ | ✅ | High | 100/day | ~$0.001 | ✅ |
| **AWS SES** | ✅ | ✅ (via SES templates) | High | 62K/month (if via EC2) | ~$0.10 / 1K | ✅ |
| **Postmark** | ✅ | ✅ | Very High | 100/month | ~$1.50 / 1K | ❌ (US only) |
| **Resend** | ✅ | ✅ (React Email) | High | 3K/month | ~$0.80 / 1K | ❌ |
| **Mailgun** | ✅ | ✅ | High | 1K/month trial | ~$0.80 / 1K | ✅ EU |

## Evaluation Matrix

| Criterion | Weight | SendGrid | AWS SES | Postmark | Resend |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Reliable transactional deliverability | 35% | | | | |
| REST API ease of integration | 20% | | | | |
| Cost at expected volume | 20% | | | | |
| EU data residency option | 15% | | | | |
| HTML template management | 10% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix, then record the decision below.

**Chosen provider:**

**From address / sender domain:**

**Template management approach:**

**Rationale:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**
