"""
CrewAI orchestration connector.

CrewAI provides a role-based multi-agent model with lower onboarding cost
than LangGraph. It is suitable for development and for clients who prefer
the "crew of agents" mental model. However, its hidden graph abstraction
is a weaker compliance posture for INV-PERF-01, and its HITL support is
less robust than LangGraph's native interrupt mechanism.

STATUS: STUB — interface defined; Sprint 1 or later for real implementation.
"""

from __future__ import annotations

import logging
from typing import Any, AsyncIterator

from ..core.base import (
    AgentState,
    ConnectorCapabilities,
    ConnectorCapability,
    ExecutionResult,
    GraphDefinition,
    HumanInput,
    OrchestrationConnector,
    StreamChunk,
)

logger = logging.getLogger(__name__)


class CrewAIConnector(OrchestrationConnector):
    """
    Wraps CrewAI as the orchestration backend.

    Constraints:
    - HITL is possible via human_input=True agent, but less controlled than LangGraph
    - Graph is implicit: traceability requires custom logging around task execution
    - Not recommended for production multi-tenant SaaS without additional hardening
    """

    CAPABILITIES = ConnectorCapabilities(
        hitl_interrupts=True,
        streaming=False,
        state_persistence=False,
        parallel_execution=True,
        explicit_graph=False,
        self_hostable=True,
        multi_agent=True,
        zero_data_retention=True,
    )

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    @property
    def connector_id(self) -> str:
        return "crewai"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return self.CAPABILITIES

    async def execute(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> ExecutionResult:
        raise NotImplementedError("CrewAIConnector.execute — implement if chosen in ADR-002")

    async def resume(
        self,
        session_id: str,
        human_input: HumanInput,
        graph: GraphDefinition,
    ) -> ExecutionResult:
        self.assert_capability(ConnectorCapability.HITL_INTERRUPTS)
        raise NotImplementedError("CrewAIConnector.resume — implement if chosen in ADR-002")

    async def stream(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> AsyncIterator[StreamChunk]:
        raise NotImplementedError(
            "CrewAI connector does not support token streaming. "
            "Use LangGraph connector for streaming workflows."
        )
        yield

    def serialize_state(self, state: AgentState) -> dict[str, Any]:
        return dict(state)

    def deserialize_state(self, data: dict[str, Any]) -> AgentState:
        return AgentState(**data)  # type: ignore[arg-type]

    async def health_check(self) -> bool:
        try:
            import crewai  # noqa: F401
            return True
        except ImportError:
            logger.warning("crewai package not installed")
            return False
