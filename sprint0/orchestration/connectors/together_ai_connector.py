"""
Together AI SDK connector.

Together AI provides cost-competitive access to open-source models
(Llama, Mistral, Qwen, etc.) via a simple API. It is NOT an orchestration
framework — it is an LLM API client. This connector wraps it as an
orchestration backend for environments where:
  - Data residency is not required (US-hosted API)
  - HITL approval workflows are not in scope
  - Budget optimisation on starter plans is the priority
  - Open-source model access is explicitly required

For all production multi-tenant environments, use the LangGraph connector
with an Anthropic or Google LLM client inside the nodes.

STATUS: STUB — interface defined.
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
    HITLNotSupportedError,
    HumanInput,
    OrchestrationConnector,
    StreamChunk,
)

logger = logging.getLogger(__name__)


class TogetherAIConnector(OrchestrationConnector):
    """
    Wraps the Together AI SDK for direct LLM calls without an orchestration graph.

    Limitations that disqualify this connector for production pipelines:
    - No HITL support → violates INV-HITL-01
    - No explicit graph → violates INV-PERF-01 in staging/production
    - Not self-hostable → violates EU/on-premise data residency rules
    - Zero data retention not guaranteed by Together AI terms

    Appropriate for: development, cost benchmarking, open-source model evaluation.
    """

    CAPABILITIES = ConnectorCapabilities(
        hitl_interrupts=False,
        streaming=True,
        state_persistence=False,
        parallel_execution=True,
        explicit_graph=False,
        self_hostable=False,
        multi_agent=False,
        zero_data_retention=False,
    )

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._api_key: str | None = None

    @property
    def connector_id(self) -> str:
        return "together_ai"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return self.CAPABILITIES

    async def execute(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> ExecutionResult:
        # Together AI has no graph abstraction. GraphDefinition.nodes are
        # executed sequentially as individual LLM calls.
        raise NotImplementedError("TogetherAIConnector.execute — implement if selected")

    async def resume(
        self,
        session_id: str,
        human_input: HumanInput,
        graph: GraphDefinition,
    ) -> ExecutionResult:
        raise HITLNotSupportedError(
            "Together AI connector does not support HITL interrupts. "
            "Use LangGraph connector for approval workflows."
        )

    async def stream(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> AsyncIterator[StreamChunk]:
        self.assert_capability(ConnectorCapability.STREAMING)
        raise NotImplementedError("TogetherAIConnector.stream — implement if selected")
        yield

    def serialize_state(self, state: AgentState) -> dict[str, Any]:
        return dict(state)

    def deserialize_state(self, data: dict[str, Any]) -> AgentState:
        return AgentState(**data)  # type: ignore[arg-type]

    async def health_check(self) -> bool:
        try:
            import together  # noqa: F401
            return True
        except ImportError:
            logger.warning("together package not installed")
            return False
