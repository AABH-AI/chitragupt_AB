"""
Constraint-based connector selector.

Evaluates routing rules from orchestration.yaml against a set of
OrchestrationConstraints and returns the highest-priority matching connector.

Selection modes
---------------
compile_time : Called once at startup. Uses ORCHESTRATION_BACKEND env var
               to bypass rule evaluation entirely. Connector is pinned for
               the process lifetime.

runtime      : Called per workspace/project. Rules are evaluated against
               the workspace's constraint profile to select the connector
               most appropriate for that client.
"""

from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .base import (
    ConnectorCapability,
    OrchestrationConfigurationError,
    OrchestrationConnector,
    OrchestrationConstraints,
)
from .registry import ConnectorRegistry

logger = logging.getLogger(__name__)


class ConstraintBasedSelector:
    """
    Selects the appropriate OrchestrationConnector given a set of constraints.

    Usage
    -----
    selector = ConstraintBasedSelector.from_config()

    # Compile-time (startup) selection:
    connector = selector.select_compile_time()

    # Runtime (per-workspace) selection:
    constraints = OrchestrationConstraints(
        data_residency="eu",
        plan_tier="enterprise",
        compliance_flags=["GDPR", "HIPAA"],
        required_capabilities=[ConnectorCapability.HITL_INTERRUPTS],
        environment="production",
    )
    connector = selector.select(constraints)
    """

    def __init__(
        self,
        config: dict[str, Any],
        registry: ConnectorRegistry,
    ) -> None:
        self._config = config["orchestration"]
        self._registry = registry

    @classmethod
    def from_config(cls, config_path: Path | None = None) -> ConstraintBasedSelector:
        if config_path is None:
            config_path = Path(__file__).parent.parent / "config" / "orchestration.yaml"
        with config_path.open("r", encoding="utf-8") as fh:
            config = yaml.safe_load(fh)
        registry = ConnectorRegistry.get_instance(config_path)
        return cls(config, registry)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_compile_time(self) -> OrchestrationConnector:
        """
        Resolve the connector at startup.

        Reads ORCHESTRATION_BACKEND env var. Falls back to the
        `fallback_connector` in config if the env var is not set.
        Raises OrchestrationConfigurationError if the chosen connector
        is disabled or fails the minimum capability check for production.
        """
        backend = os.environ.get("ORCHESTRATION_BACKEND")
        if backend:
            logger.info("Compile-time connector override: ORCHESTRATION_BACKEND=%s", backend)
            return self._registry.get(backend)

        fallback = self._config.get("fallback_connector", "langgraph")
        logger.info("No ORCHESTRATION_BACKEND set; using fallback: %s", fallback)
        return self._registry.get(fallback)

    def select(self, constraints: OrchestrationConstraints) -> OrchestrationConnector:
        """
        Evaluate routing rules and return the best connector for the given constraints.

        Steps:
        1. Start with all enabled connectors.
        2. Apply routing rules in priority order.
           - hard_filter rules: eliminate non-compliant candidates.
           - soft_preference rules: reorder candidates.
           - override rules: bypass evaluation and return a specific connector.
        3. Filter by required_capabilities (always a hard filter).
        4. Return the first surviving candidate.
        5. If no candidates survive, raise OrchestrationConfigurationError.
        """
        if self._config.get("selection_mode") == "compile_time":
            return self.select_compile_time()

        candidates = self._registry.all_enabled()

        rules = sorted(
            self._config.get("routing_rules", []),
            key=lambda r: r.get("priority", 99),
        )

        preferred_order: list[str] = []

        for rule in rules:
            if not self._rule_matches(rule, constraints):
                continue

            action = rule.get("action", {})
            action_type = action.get("type", "soft_preference")

            if action_type == "override":
                connector_id = self._resolve_override(action, constraints)
                if connector_id:
                    logger.info("Rule '%s' overrides connector to: %s", rule["id"], connector_id)
                    return self._registry.get(connector_id)

            elif action_type == "hard_filter":
                required_cap = action.get("require_capability")
                if required_cap:
                    cap = ConnectorCapability(required_cap)
                    before = len(candidates)
                    candidates = [c for c in candidates if c.capabilities.has(cap)]
                    logger.debug(
                        "Rule '%s' hard-filtered on capability '%s': %d → %d candidates",
                        rule["id"], required_cap, before, len(candidates),
                    )
                preferred_ids = action.get("preferred_connectors", [])
                if preferred_ids:
                    preferred_order = preferred_ids

            elif action_type == "soft_preference":
                preferred_order = action.get("preferred_connectors", preferred_order)

        # Always hard-filter by explicitly required capabilities
        for cap in constraints.required_capabilities:
            candidates = [c for c in candidates if c.capabilities.has(cap)]

        if not candidates:
            raise OrchestrationConfigurationError(
                f"No orchestration connector satisfies the given constraints: "
                f"data_residency={constraints.data_residency}, "
                f"compliance={constraints.compliance_flags}, "
                f"required_capabilities={constraints.required_capabilities}, "
                f"environment={constraints.environment}. "
                f"Review orchestration.yaml routing_rules or enable additional connectors."
            )

        # Sort surviving candidates by preferred_order
        candidates = self._sort_by_preference(candidates, preferred_order)

        selected = candidates[0]
        logger.info(
            "Selected orchestration connector: %s (from %d candidates)",
            selected.connector_id, len(candidates),
        )
        return selected

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _rule_matches(
        self,
        rule: dict[str, Any],
        constraints: OrchestrationConstraints,
    ) -> bool:
        condition = rule.get("condition", {})

        for key, expected in condition.items():
            actual = getattr(constraints, key, None)

            if expected == "!null":
                if actual is None:
                    return False
                continue

            if isinstance(expected, list):
                if actual not in expected:
                    return False
            elif key == "compliance_flags_contains":
                if expected not in (constraints.compliance_flags or []):
                    return False
            elif key == "feature_required":
                cap = ConnectorCapability(expected)
                if not constraints.requires(cap):
                    return False
            else:
                if actual != expected:
                    return False

        return True

    @staticmethod
    def _resolve_override(
        action: dict[str, Any],
        constraints: OrchestrationConstraints,
    ) -> str | None:
        connector_id = action.get("use_connector", "")
        if connector_id.startswith("${workspace."):
            # Template variable: resolve from constraints
            attr = connector_id.removeprefix("${workspace.").removesuffix("}")
            return getattr(constraints, attr, None)
        return connector_id or None

    @staticmethod
    def _sort_by_preference(
        candidates: list[OrchestrationConnector],
        preferred_order: list[str],
    ) -> list[OrchestrationConnector]:
        if not preferred_order:
            return candidates

        def rank(connector: OrchestrationConnector) -> int:
            try:
                return preferred_order.index(connector.connector_id)
            except ValueError:
                return len(preferred_order)  # unranked connectors go last

        return sorted(candidates, key=rank)
