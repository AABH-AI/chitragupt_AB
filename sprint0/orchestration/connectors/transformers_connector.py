"""
HuggingFace Transformers self-hosted connector.

This connector enables fully on-premise inference using HuggingFace
Transformers models served via vLLM or Text Generation Inference (TGI).
It satisfies the strictest data sovereignty and HIPAA requirements because
model weights run inside the client's infrastructure with no external API calls.

DISABLED by default in orchestration.yaml. Enable only when:
  1. Client has explicitly required on-premise or air-gapped deployment
  2. GPU infrastructure has been provisioned (ADR-009 decision)
  3. A model serving stack (vLLM or TGI) is operational

At scale (>10M tokens/month), self-hosted inference can break even vs
API pricing. Below that threshold, API providers are almost always cheaper.

STATUS: STUB — interface defined; enable and implement only after ADR-009 confirms GPU infra.
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


class TransformersConnector(OrchestrationConnector):
    """
    Self-hosted HuggingFace Transformers connector.

    Infrastructure requirements (must be satisfied before enabling):
    - GPU instances (A100/H100 or equivalent) provisioned via ADR-009
    - Model serving stack: vLLM (recommended) or HuggingFace TGI
    - Model weights downloaded and cached in the deployment environment
    - No orchestration framework: GraphDefinition nodes are called sequentially
      via the serving endpoint's OpenAI-compatible API

    Data sovereignty:
    - No data ever leaves the client's infrastructure
    - Suitable for air-gapped deployments
    - Full HIPAA, GDPR, and on-premise compliance achievable
    """

    CAPABILITIES = ConnectorCapabilities(
        hitl_interrupts=False,      # manual scaffolding required
        streaming=True,             # via TextIteratorStreamer or vLLM streaming
        state_persistence=False,
        parallel_execution=True,    # batched inference
        explicit_graph=False,
        self_hostable=True,
        multi_agent=False,
        zero_data_retention=True,   # fully self-hosted; no external egress
    )

    def __init__(self, config: dict[str, Any]) -> None:
        self._config = config
        self._serving_endpoint: str | None = config.get("serving_endpoint")

    @property
    def connector_id(self) -> str:
        return "transformers"

    @property
    def capabilities(self) -> ConnectorCapabilities:
        return self.CAPABILITIES

    async def execute(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> ExecutionResult:
        raise NotImplementedError(
            "TransformersConnector.execute — enable in orchestration.yaml and implement "
            "after GPU infrastructure is confirmed in ADR-009."
        )

    async def resume(
        self,
        session_id: str,
        human_input: HumanInput,
        graph: GraphDefinition,
    ) -> ExecutionResult:
        raise HITLNotSupportedError(
            "Transformers connector does not have native HITL support. "
            "Wrap it inside a LangGraph node and use the LangGraph connector for interrupts."
        )

    async def stream(
        self,
        graph: GraphDefinition,
        state: AgentState,
    ) -> AsyncIterator[StreamChunk]:
        self.assert_capability(ConnectorCapability.STREAMING)
        raise NotImplementedError("TransformersConnector.stream — implement after GPU infra confirmed")
        yield

    def serialize_state(self, state: AgentState) -> dict[str, Any]:
        return dict(state)

    def deserialize_state(self, data: dict[str, Any]) -> AgentState:
        return AgentState(**data)  # type: ignore[arg-type]

    async def health_check(self) -> bool:
        if not self._serving_endpoint:
            logger.warning(
                "TransformersConnector: no serving_endpoint configured. "
                "Set serving_endpoint in orchestration.yaml connector config."
            )
            return False
        try:
            import httpx
            async with httpx.AsyncClient() as client:
                resp = await client.get(f"{self._serving_endpoint}/health", timeout=5.0)
                return resp.status_code == 200
        except Exception as exc:
            logger.warning("TransformersConnector health check failed: %s", exc)
            return False
