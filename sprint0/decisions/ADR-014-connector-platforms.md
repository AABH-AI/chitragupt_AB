# ADR-014: External Connector Platforms (MVP Set)

**Status:** OPEN
**Deciders:** Product Manager, Tech Lead
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** INV-HITL-02 (manual trigger — export connectors must fire only after explicit human approval), INV-SEC-03 (file isolation — connector auth must be scoped to workspace, not shared credentials)

---

## Context

Chitragupt integrates with external platforms in two directions:

- **Inbound connectors** (Sprint 1) — pull or receive source documents from external systems (Jira epics, Confluence pages, Google Drive files, etc.)
- **Outbound connectors** (Sprint 4) — push approved requirements to external systems (create Jira stories, Confluence pages, etc.)

This ADR answers one specific question: **which platforms are in the MVP set?** Building every possible connector is not feasible in the first release. The team must select a prioritized subset based on where client requirement documents actually live and where clients expect to see output.

Every connector — inbound and outbound — requires:
- OAuth 2.0 app registration with the platform
- Token storage (encrypted, per workspace)
- Token refresh logic
- Rate limit handling

This is non-trivial per connector. The MVP selection directly determines Sprint 1 and Sprint 4 scope.

## Decision Drivers

- Where do target clients actually store their existing requirement documents? (inbound priority)
- Where do target clients expect to receive approved requirements? (outbound priority)
- Platform API maturity and rate limits
- OAuth app registration complexity per platform
- Breadth vs. depth: fewer connectors done well vs. more connectors done partially
- Vendor ecosystem: some platforms share an API model (Atlassian covers Jira + Confluence with one OAuth app)

## Platform Inventory

### Inbound Connector Candidates

| Platform | Common use as requirements source | API Quality | OAuth Complexity | Atlassian umbrella |
| :--- | :--- | :--- | :--- | :--- |
| **Jira** | Epics, stories, custom fields | ✅ Mature | One-time OAuth app | ✅ |
| **Confluence** | Specification pages, meeting notes | ✅ Mature | Shared with Jira | ✅ |
| **Notion** | Product docs, requirement databases | ✅ Good | Separate OAuth app | ❌ |
| **Google Docs / Drive** | Documents, spreadsheets | ✅ Mature | Google OAuth | ❌ |
| **SharePoint / OneDrive** | Documents, wikis | ✅ Mature | Azure AD app | ❌ |
| **GitHub (repo files)** | Markdown specs in repos | ✅ Mature | GitHub OAuth | ❌ |
| **Linear** | Issue descriptions, project docs | ✅ Good | Separate OAuth app | ❌ |
| **Slack exports** | Channel threads, DM exports | ⚠️ Complex | Slack app + user auth | ❌ |

### Outbound Connector Candidates

| Platform | Common as requirements destination | API Write Support | Same OAuth as inbound |
| :--- | :--- | :--- | :--- |
| **Jira** | Stories, epics with AC | ✅ | ✅ |
| **Confluence** | Published specification pages | ✅ | ✅ |
| **Notion** | Requirement databases | ✅ | ✅ if inbound selected |
| **GitHub Issues** | Issues with labels | ✅ | ✅ if inbound selected |
| **Linear** | Issues | ✅ | ✅ if inbound selected |
| **Azure DevOps** | Work items | ✅ | Separate app |

## MVP Selection Worksheet

The PM must confirm the MVP connector set before Sprint 1 planning. Each selected connector adds ~3–5 days of engineering work.

### Inbound MVP (Sprint 1) — select platforms:

| Platform | In MVP? | Priority | Notes |
| :--- | :--- | :--- | :--- |
| Jira | ☐ Yes ☐ No | | |
| Confluence | ☐ Yes ☐ No | | |
| Notion | ☐ Yes ☐ No | | |
| Google Docs / Drive | ☐ Yes ☐ No | | |
| SharePoint | ☐ Yes ☐ No | | |
| GitHub repo files | ☐ Yes ☐ No | | |
| Linear | ☐ Yes ☐ No | | |

### Outbound MVP (Sprint 4) — select platforms:

| Platform | In MVP? | Priority | Notes |
| :--- | :--- | :--- | :--- |
| Jira | ☐ Yes ☐ No | | |
| Confluence | ☐ Yes ☐ No | | |
| Notion | ☐ Yes ☐ No | | |
| GitHub Issues | ☐ Yes ☐ No | | |
| Linear | ☐ Yes ☐ No | | |

## Decision

> **OPEN** — Complete the worksheets above with PM sign-off, then record the decision below.

**Inbound MVP connector set:**

**Outbound MVP connector set:**

**OAuth app registrations needed before Sprint 1 starts:**

**Rationale:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Deferred connectors (post-MVP roadmap):**
