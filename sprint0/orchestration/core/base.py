"""
Orchestration connector base interface.

Every orchestration backend must implement OrchestrationConnector.
Application code and agents interact only with this interface — never
with framework-specific APIs directly. This isolation means the backend
can be swapped by changing configuration with no agent code changes.
"""

from __future__ import annotations

import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, AsyncIterator, TypedDict


# ---------------------------------------------------------------------------
# Capability model
# ---------------------------------------------------------------------------

class ConnectorCapability(StrEnum):
    HITL_INTERRUPTS = "hitl_interrupts"
    STREAMING = "streaming"
    STATE_PERSISTENCE = "state_persistence"
    PARALLEL_EXECUTION = "parallel_execution"
    EXPLICIT_GRAPH = "explicit_graph"
    SELF_HOSTABLE = "self_hostable"
    MULTI_AGENT = "multi_agent"
    ZERO_DATA_RETENTION = "zero_data_retention"


@dataclass(frozen=True)
class ConnectorCapabilities:
    hitl_interrupts: bool = False
    streaming: bool = False
    state_persistence: bool = False
    parallel_execution: bool = False
    explicit_graph: bool = False
    self_hostable: bool = False
    multi_agent: bool = False
    zero_data_retention: bool = False

    def has(self, capability: ConnectorCapability) -> bool:
        return bool(getattr(self, capability.value, False))

    def satisfies_all(self, required: list[ConnectorCapability]) -> bool:
        return all(self.has(cap) for cap in required)


# ---------------------------------------------------------------------------
# Shared state and data types
# (Concrete agents will extend AgentState via TypedDict inheritance)
# ---------------------------------------------------------------------------

class AgentState(TypedDict, total=False):
    session_id: str
    project_id: str
    tenant_id: str
    current_agent: str
    phase: str
    iteration_count: int
    total_cost_usd: float
    human_pending_actions: list[dict[str, Any]]
    completed_sections: list[str]
    remaining_sections: list[str]
    last_updated: str
    error: str | None


@dataclass
class GraphNode:
    node_id: str
    name: str
    agent_class: str
    config: dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    from_node: str
    to_node: str
    condition: str | None = None   # Python expression string; None = unconditional


@dataclass
class GraphDefinition:
    graph_id: str
    entry_point: str
    nodes: list[GraphNode]
    edges: list[GraphEdge]
    interrupt_before: list[str] = field(default_factory=list)   # node IDs to pause before
    interrupt_after: list[str] = field(default_factory=list)    # node IDs to pause after
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class HumanInput:
    session_id: str
    action: str                    # "approve" | "reject" | "edit" | "resolve_conflict"
    payload: dict[str, Any]
    user_id: str
    timestamp: str


@dataclass
class StreamChunk:
    session_id: str
    node_id: str
    chunk_type: str                # "token" | "tool_call" | "state_update" | "complete"
    content: str | dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionResult:
    session_id: str
    final_state: AgentState
    interrupted: bool = False      # True if paused at a HITL interrupt point
    interrupt_node: str | None = None
    cost_usd: float = 0.0
    duration_ms: int = 0


# ---------------------------------------------------------------------------
# Constraint model (mirrors orchestration.yaml constraint_defaults)
# ---------------------------------------------------------------------------

@dataclass
class OrchestrationConstraints:
    environment: str = "development"
    data_residency: str = "us"
    plan_tier: str = "professional"
    compliance_flags: list[str] = field(default_factory=list)
    required_capabilities: list[ConnectorCapability] = field(default_factory=list)
    client_mandated_connector: str | None = None
    allow_external_apis: bool = True

    def requires(self, capability: ConnectorCapability) -> bool:
        return capability in self.required_capabilities


# ---------------------------------------------------------------------------
# Abstract connector interface
# ---------------------------------------------------------------------------

class OrchestrationConnector(ABC):
    """
    Abstract base for all orchestration backends.

    Implementations must be stateless between calls — all context is passed
    explicitly via AgentState. This satisfies INV-PERF-02.
    """

    @property
    @abstractmethod
    def connector_id(self) -> str:
        """Unique identifier matching the key in orchestration.yaml connectors."""

    @property
    @abstractmethod
    def capabilities(self) -> ConnectorCapabilities:
        """Declared capabilities. Must match orchestration.yaml for this connector."""

    @abstractmethod
    async def execute(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> ExecutionResult:
        """
        Run the graph to completion (or until the next HITL interrupt).
        Must be re-entrant: calling execute() on a paused session resumes it.
        """

    @abstractmethod
    async def resume(
        self,
        session_id: str,
        human_input: HumanInput,
        graph: GraphDefinition,
    ) -> ExecutionResult:
        """
        Resume a graph paused at a HITL interrupt node.
        Raises NotImplementedError if the connector lacks HITL capability.
        """

    @abstractmethod
    def stream(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> AsyncIterator[StreamChunk]:
        """
        Stream execution chunks token-by-token.
        Raises NotImplementedError if the connector lacks streaming capability.
        """

    @abstractmethod
    def serialize_state(self, state: AgentState) -> dict[str, Any]:
        """Serialize AgentState to a JSON-serializable dict for external storage."""

    @abstractmethod
    def deserialize_state(self, data: dict[str, Any]) -> AgentState:
        """Restore AgentState from serialized dict."""

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the connector and its dependencies are reachable."""

    def assert_capability(self, capability: ConnectorCapability) -> None:
        if not self.capabilities.has(capability):
            raise NotImplementedError(
                f"Connector '{self.connector_id}' does not support {capability}. "
                f"Check orchestration.yaml and routing rules."
            )


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class OrchestrationError(Exception):
    """Base class for all orchestration errors."""


class OrchestrationConfigurationError(OrchestrationError):
    """Raised when constraint evaluation produces no valid connector."""


class ConnectorNotFoundError(OrchestrationError):
    """Raised when a requested connector ID is not in the registry."""


class HITLNotSupportedError(OrchestrationError):
    """Raised when resume() is called on a connector without HITL capability."""
