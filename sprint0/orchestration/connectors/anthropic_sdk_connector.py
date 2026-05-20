"""
Anthropic SDK direct connector.

This connector wraps the Anthropic Python SDK for direct model calls
with zero framework overhead. It is NOT a full orchestration backend —
all graph structure and state management must be hand-built around it.

Intended use: as the LLM client inside a LangGraph node, not as the
orchestrator itself. Exposed here as a standalone connector for cases
where the simplest possible integration is needed (e.g., a single-step
classification call in a test harness).

Provides prompt caching, zero data retention enforcement, and streaming
out of the box.

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

# Zero data retention header — must be sent on every API call
_ZDR_HEADERS: dict[str, str] = {"anthropic-beta": "zero-data-retention"}


class AnthropicSDKConnector(OrchestrationConnector):
    """
    Direct Anthropic SDK connector.

    Key properties:
    - Prompt caching enabled automatically for system prompts > 1024 tokens
    - Zero data retention enforced via request header on every call
    - Regional deployment available via AWS Bedrock or GCP Vertex
    - No orchestration framework overhead

    Limitations:
    - No HITL — resume() raises HITLNotSupportedError
    - No explicit graph — blocked by rule_explicit_graph_production in staging/prod
    - Recommended as LLM client within a LangGraph node, not as top-level orchestrator
    """

    CAPABILITIES = ConnectorCapabilities(
        hitl_interrupts=False,
        streaming=True,
        state_persistence=False,
        parallel_execution=True,
        explicit_graph=False,
        self_hostable=False,      # API-only; regional via Bedrock/Vertex
        multi_agent=False,
        zero_data_retention=True,
    )

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config

    @property
    def connector_id(self) -> str:
        return "anthropic_sdk"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return self.CAPABILITIES

    async def execute(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> ExecutionResult:
        # Single-node graphs only; multi-node requires LangGraph
        raise NotImplementedError("AnthropicSDKConnector.execute — implement if selected")

    async def resume(
        self,
        session_id: str,
        human_input: HumanInput,
        graph: GraphDefinition,
    ) -> ExecutionResult:
        raise HITLNotSupportedError(
            "Anthropic SDK connector does not support HITL. "
            "Wrap it inside a LangGraph node and use the LangGraph connector for interrupts."
        )

    async def stream(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> AsyncIterator[StreamChunk]:
        """
        Sprint implementation note:
            async with client.messages.stream(
                model=model_id,
                messages=messages,
                extra_headers=_ZDR_HEADERS,
            ) as stream:
                async for text in stream.text_stream:
                    yield StreamChunk(chunk_type="token", content=text, ...)
        """
        self.assert_capability(ConnectorCapability.STREAMING)
        raise NotImplementedError("AnthropicSDKConnector.stream — implement if selected")
        yield

    def serialize_state(self, state: AgentState) -> dict[str, Any]:
        return dict(state)

    def deserialize_state(self, data: dict[str, Any]) -> AgentState:
        return AgentState(**data)  # type: ignore[arg-type]

    async def health_check(self) -> bool:
        try:
            import anthropic  # noqa: F401
            return True
        except ImportError:
            logger.warning("anthropic package not installed")
            return False
