# ADR-011: CI/CD Pipeline

**Status:** OPEN
**Deciders:** DevOps
**Sprint:** 0
**Date Decided:** —
**Invariants Affected:** None directly — but the CI pipeline is the enforcement mechanism for invariant tests (D-07) and the model version pinning check (INV-MODEL-03)

**Depends on:** ADR-009 (deployment platform determines the deploy step tooling)

---

## Context

The CI/CD pipeline runs automatically on every pull request and on every merge to `main`. It is the gating mechanism that prevents broken code, missing type annotations, security vulnerabilities, and invariant violations from reaching staging or production.

The pipeline has two distinct phases:

1. **CI (Continuous Integration)** — runs on every PR: lint, type check, unit tests, integration tests (real DB via containers), security scan, Docker build
2. **CD (Continuous Deployment)** — runs on merge to `main`: push image to registry, deploy to staging, run smoke tests

The integration test stage is the most expensive step — it requires a real PostgreSQL instance with pgvector. This must be containerized (not mocked) to preserve the validity of the tenant isolation test (INV-SEC-01).

## Decision Drivers

- Native integration with the source code repository (no external webhook setup)
- Support for containerized test environments — integration tests require a real PostgreSQL database (testcontainers or service containers)
- Security scanning: dependency vulnerability audit and static analysis
- Parallelism — lint/type/unit/integration stages should run in parallel where possible
- Cost at expected PR frequency (assume 20–40 PRs/week)
- Secret management for CI environment (LLM API keys, DB credentials for test)
- Deployment step integration with chosen platform (ADR-009)

## Required Pipeline Stages (Non-Negotiable)

Every PR must pass all of these before it can merge:

```
[parallel]
  ├── Lint (formatter + import sorter)
  ├── Type check (strict mode)
  └── Security scan (dependency audit + static analysis)

[sequential]
  └── Unit tests
      └── Integration tests (real PostgreSQL + pgvector via service container)
          └── Docker build (verify image builds successfully)
              └── [on merge to main only] Deploy to staging
                  └── Smoke tests on staging
```

## Considered Options

| Option | Repo Integration | Container Services | Cost | Secret Management | Notes |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **GitHub Actions** | ✅ Native (GitHub) | ✅ Service containers | Free for public; ~$0.008/min private | ✅ GitHub Secrets | Largest action ecosystem |
| **GitLab CI** | ✅ Native (GitLab) | ✅ Service containers | Free tier; $29+/month | ✅ GitLab CI vars | Strong if repo is on GitLab |
| **CircleCI** | Webhook | ✅ | Free tier; pay-per-compute | ✅ | Good parallelism; external service |
| **AWS CodePipeline** | Webhook | ✅ CodeBuild | Pay-per-build-minute | ✅ Secrets Manager | AWS-native; less ecosystem |
| **Buildkite** | Webhook | ✅ (self-hosted agents) | $35+/month + agent infra | ✅ | Enterprise-grade; higher ops cost |

## Evaluation Matrix

| Criterion | Weight | GitHub Actions | GitLab CI | CircleCI | CodePipeline |
| :--- | :---: | :---: | :---: | :---: | :---: |
| Native repo integration | 30% | | | | |
| Container service support for integration tests | 25% | | | | |
| Cost at expected PR volume | 20% | | | | |
| Ecosystem and pre-built actions | 15% | | | | |
| Secret management | 10% | | | | |
| **Weighted Total** | | | | | |

## Decision

> **OPEN** — Fill in the evaluation matrix, then record the decision below.

**Chosen CI/CD tool:**

**Branch protection rules (PRs must pass):**

**Deployment target on merge to `main`:**

**Rationale:**

## Consequences

**Positive:**

**Negative / Trade-offs:**

**Risks:**
