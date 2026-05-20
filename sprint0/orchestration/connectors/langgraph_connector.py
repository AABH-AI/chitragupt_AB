"""
LangGraph orchestration connector.

This is the recommended production connector. LangGraph's explicit directed
graph satisfies INV-PERF-01 (deterministic retrieval), its stateless node model
satisfies INV-PERF-02, and its native interrupt mechanism satisfies
INV-HITL-01 through INV-HITL-04.

STATUS: STUB — interface defined; LangGraph wiring implemented in Sprint 1.
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


class LangGraphConnector(OrchestrationConnector):
    """
    Wraps LangGraph as the orchestration backend.

    Implementation notes (Sprint 1):
    - StateGraph compiled from GraphDefinition.nodes and .edges
    - MemorySaver or AsyncPostgresSaver as checkpointer (decided in ADR-006)
    - interrupt_before / interrupt_after map directly to GraphDefinition fields
    - Langfuse tracing injected via LangChainTracer callback
    """

    CAPABILITIES = ConnectorCapabilities(
        hitl_interrupts=True,
        streaming=True,
        state_persistence=True,
        parallel_execution=True,
        explicit_graph=True,
        self_hostable=True,
        multi_agent=True,
        zero_data_retention=True,
    )

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._graphs: dict[str, Any] = {}   # compiled graph cache keyed by graph_id

    @property
    def connector_id(self) -> str:
        return "langgraph"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return self.CAPABILITIES

    async def execute(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> ExecutionResult:
        """
        Compile and run the LangGraph StateGraph.

        Sprint 1 implementation:
            compiled = self._get_or_compile(graph)
            config = {"configurable": {"thread_id": state["session_id"]}}
            result = await compiled.ainvoke(state, config=config)
            interrupted = compiled.get_state(config).next != ()
            return ExecutionResult(session_id=state["session_id"], final_state=result, interrupted=interrupted)
        """
        raise NotImplementedError("LangGraphConnector.execute — implement in Sprint 1")

    async def resume(
        self,
        session_id: str,
        human_input: HumanInput,
        graph: GraphDefinition,
    ) -> ExecutionResult:
        """
        Resume a graph paused at a HITL interrupt.

        Sprint 1 implementation:
            compiled = self._get_or_compile(graph)
            config = {"configurable": {"thread_id": session_id}}
            await compiled.aupdate_state(config, human_input.payload)
            result = await compiled.ainvoke(None, config=config)
            return ExecutionResult(session_id=session_id, final_state=result)
        """
        self.assert_capability(ConnectorCapability.HITL_INTERRUPTS)
        raise NotImplementedError("LangGraphConnector.resume — implement in Sprint 1")

    async def stream(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream execution events token-by-token via astream_events.

        Sprint 1 implementation:
            compiled = self._get_or_compile(graph)
            config = {"configurable": {"thread_id": state["session_id"]}}
            async for event in compiled.astream_events(state, config=config, version="v2"):
                yield StreamChunk(...)
        """
        self.assert_capability(ConnectorCapability.STREAMING)
        raise NotImplementedError("LangGraphConnector.stream — implement in Sprint 1")
        yield  # makes this an async generator

    def serialize_state(self, state: AgentState) -> dict[str, Any]:
        return dict(state)

    def deserialize_state(self, data: dict[str, Any]) -> AgentState:
        return AgentState(**data)  # type: ignore[arg-type]

    async def health_check(self) -> bool:
        try:
            import langgraph  # noqa: F401
            return True
        except ImportError:
            logger.warning("langgraph package not installed")
            return False
