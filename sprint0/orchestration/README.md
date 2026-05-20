# Orchestration Connector Middleware

This directory defines the orchestration connector abstraction layer for Chitragupt. It allows the agentic pipeline to switch between orchestration backends — LangGraph, LangChain, CrewAI, Together AI, Anthropic SDK, or HuggingFace Transformers — by changing configuration rather than application code.

---

## Why this exists

Different clients have different constraints:

- An enterprise client in the EU cannot use Together AI (US-hosted API, no data residency).
- A HIPAA-scoped workspace must run on self-hostable infrastructure.
- A starter-plan client may want cost-optimised open-source model access.
- A client's internal engineering team may mandate a specific framework.

Without this middleware, each of these scenarios would require code changes. With it, the change is a configuration entry in `orchestration.yaml` or a workspace setting.

---

## Directory structure

```
orchestration/
├── config/
│   ├── orchestration.yaml          ← master config: connector registry + routing rules
│   └── profiles/
│       ├── enterprise.yaml         ← constraint profile for enterprise workspaces
│       ├── budget.yaml             ← constraint profile for starter/budget workspaces
│       └── development.yaml        ← relaxed profile for local dev and CI
├── core/
│   ├── base.py                     ← abstract OrchestrationConnector interface + shared types
│   ├── registry.py                 ← ConnectorRegistry: loads and caches connector instances
│   └── selector.py                 ← ConstraintBasedSelector: evaluates rules, picks connector
└── connectors/
    ├── langgraph_connector.py      ← recommended production connector
    ├── langchain_connector.py      ← utility layer; not for production orchestration
    ├── crewai_connector.py         ← role-based alternative; development/evaluation
    ├── together_ai_connector.py    ← open-source model access; US/starter only
    ├── anthropic_sdk_connector.py  ← direct SDK; use inside LangGraph nodes, not as orchestrator
    └── transformers_connector.py   ← self-hosted; disabled by default; requires GPU infra
```

---

## How connector selection works

### Compile-time mode

Set the `ORCHESTRATION_BACKEND` environment variable before starting the application:

```bash
ORCHESTRATION_BACKEND=langgraph python -m chitragupt.api.app
```

The connector is resolved once at startup and is immutable for the process lifetime. No per-request evaluation. Use in environments where all workspaces use the same backend.

### Runtime mode (default)

The connector is selected per workspace based on the workspace's constraint profile. The `ConstraintBasedSelector` evaluates the routing rules in `orchestration.yaml` against the workspace constraints and returns the best matching connector.

```python
from sprint0.orchestration.core import ConstraintBasedSelector, OrchestrationConstraints, ConnectorCapability

selector = ConstraintBasedSelector.from_config()

constraints = OrchestrationConstraints(
    data_residency="eu",
    plan_tier="enterprise",
    compliance_flags=["GDPR"],
    required_capabilities=[ConnectorCapability.HITL_INTERRUPTS],
    environment="production",
)

connector = selector.select(constraints)
# → LangGraphConnector (only self-hostable connector with HITL + explicit graph)
```

---

## Routing rule evaluation order

Rules in `orchestration.yaml` are evaluated in ascending `priority` order. Lower number = higher priority. First matching rule narrows the candidate set.

| Priority | Rule | Type | Effect |
| :---: | :--- | :--- | :--- |
| 1 | `rule_on_premise` | Hard filter | Eliminates non-self-hostable connectors |
| 2 | `rule_strict_data_residency` | Hard filter | EU/APAC: eliminates non-self-hostable |
| 3 | `rule_hipaa` | Hard filter | HIPAA flag: eliminates non-self-hostable |
| 4 | `rule_hitl_required` | Hard filter | Eliminates connectors without HITL |
| 5 | `rule_explicit_graph_production` | Hard filter | Staging/prod: eliminates non-graph connectors |
| 6 | `rule_client_mandate` | Override | Forces a specific connector |
| 7 | `rule_enterprise_plan` | Soft preference | Prefers LangGraph |
| 8 | `rule_starter_budget_us` | Soft preference | Allows Together AI as secondary |
| 99 | `rule_development_permissive` | Soft preference | All connectors allowed |

Hard filters eliminate connectors from consideration entirely. If all connectors are eliminated, `OrchestrationConfigurationError` is raised and the system refuses to start for that workspace.

---

## Adding a new connector

1. Create `connectors/my_connector.py` implementing `OrchestrationConnector` from `core/base.py`.
2. Add an entry to `orchestration.yaml` under `connectors:` with `enabled: true` and accurate `capabilities:`.
3. Add a routing rule under `routing_rules:` if the connector requires specific conditions.
4. Add the module path to `_CONNECTOR_MODULE_MAP` in `core/registry.py`.
5. Export the class from `connectors/__init__.py`.
6. Write a unit test asserting the connector's declared capabilities match its actual behaviour.

---

## Status

All connectors are **STUBS** at Sprint 0. The interface is defined and type-safe. Real implementation begins in Sprint 1 for the chosen connector (ADR-002). Other connectors are implemented on demand.
