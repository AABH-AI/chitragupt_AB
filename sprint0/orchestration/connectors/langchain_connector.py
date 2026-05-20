"""
LangChain orchestration connector.

LangChain is supported as a utility layer (document loaders, text splitters,
embedding wrappers) but NOT as the primary orchestrator for production pipelines.
It lacks native HITL and explicit graph support required by invariants.

Use cases where this connector IS appropriate:
- Development / prototyping
- Utility chains (document loading, format conversion) called within a LangGraph node
- Evaluating LangChain-specific integrations before wrapping them in LangGraph

STATUS: STUB — interface defined; production use not recommended.
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


class LangChainConnector(OrchestrationConnector):
    """
    Wraps LangChain LCEL chains as the orchestration backend.

    Constraints:
    - No HITL support: resume() always raises HITLNotSupportedError
    - No explicit graph: routing rules will block this in production/staging
      (rule_explicit_graph_production in orchestration.yaml)
    - Recommended only in development environment or as utility within LangGraph nodes
    """

    CAPABILITIES = ConnectorCapabilities(
        hitl_interrupts=False,
        streaming=True,
        state_persistence=False,
        parallel_execution=False,
        explicit_graph=False,
        self_hostable=True,
        multi_agent=False,
        zero_data_retention=True,
    )

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    @property
    def connector_id(self) -> str:
        return "langchain"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return self.CAPABILITIES

    async def execute(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> ExecutionResult:
        raise NotImplementedError("LangChainConnector.execute — implement if/when needed")

    async def resume(
        self,
        session_id: str,
        human_input: HumanInput,
        graph: GraphDefinition,
    ) -> ExecutionResult:
        raise HITLNotSupportedError(
            "LangChain connector does not support HITL interrupts. "
            "Use LangGraph connector for workflows requiring human approval."
        )

    async def stream(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> AsyncIterator[StreamChunk]:
        self.assert_capability(ConnectorCapability.STREAMING)
        raise NotImplementedError("LangChainConnector.stream — implement if/when needed")
        yield

    def serialize_state(self, state: AgentState) -> dict[str, Any]:
        return dict(state)

    def deserialize_state(self, data: dict[str, Any]) -> AgentState:
        return AgentState(**data)  # type: ignore[arg-type]

    async def health_check(self) -> bool:
        try:
            import langchain_core  # noqa: F401
            return True
        except ImportError:
            logger.warning("langchain-core package not installed")
            return False
