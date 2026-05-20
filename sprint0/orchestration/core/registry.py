"""
Connector registry.

Loads all enabled connectors from orchestration.yaml and exposes them
for selection. Connectors are instantiated lazily on first use.
"""

from __future__ import annotations

import importlib
import logging
from pathlib import Path
from typing import ClassVar

import yaml

from .base import (
    ConnectorNotFoundError,
    OrchestrationConfigurationError,
    OrchestrationConnector,
)

logger = logging.getLogger(__name__)

_CONNECTOR_MODULE_MAP: dict[str, str] = {
    "langgraph":     "sprint0.orchestration.connectors.langgraph_connector.LangGraphConnector",
    "langchain":     "sprint0.orchestration.connectors.langchain_connector.LangChainConnector",
    "crewai":        "sprint0.orchestration.connectors.crewai_connector.CrewAIConnector",
    "together_ai":   "sprint0.orchestration.connectors.together_ai_connector.TogetherAIConnector",
    "anthropic_sdk": "sprint0.orchestration.connectors.anthropic_sdk_connector.AnthropicSDKConnector",
    "transformers":  "sprint0.orchestration.connectors.transformers_connector.TransformersConnector",
}


class ConnectorRegistry:
    """
    Singleton registry that holds all available orchestration connectors.

    Reads enabled/disabled state from orchestration.yaml. Instantiates
    connector classes lazily so that packages for disabled connectors
    (e.g., HuggingFace Transformers) are never imported.
    """

    _instance: ClassVar[ConnectorRegistry | None] = None

    def __init__(self, config_path: Path) -> None:
        self._config = self._load_config(config_path)
        self._instances: dict[str, OrchestrationConnector] = {}

    @classmethod
    def get_instance(cls, config_path: Path | None = None) -> ConnectorRegistry:
        if cls._instance is None:
            if config_path is None:
                config_path = Path(__file__).parent.parent / "config" / "orchestration.yaml"
            cls._instance = cls(config_path)
        return cls._instance

    # ------------------------------------------------------------------

    def get(self, connector_id: str) -> OrchestrationConnector:
        """Return a connector by ID. Raises ConnectorNotFoundError if unknown."""
        if connector_id not in self._instances:
            self._instances[connector_id] = self._instantiate(connector_id)
        return self._instances[connector_id]

    def all_enabled(self) -> list[OrchestrationConnector]:
        """Return all connectors that are marked enabled in config."""
        enabled_ids = [
            cid
            for cid, cfg in self._config["orchestration"]["connectors"].items()
            if cfg.get("enabled", False)
        ]
        return [self.get(cid) for cid in enabled_ids]

    def is_enabled(self, connector_id: str) -> bool:
        connectors = self._config["orchestration"]["connectors"]
        return connectors.get(connector_id, {}).get("enabled", False)

    # ------------------------------------------------------------------

    def _instantiate(self, connector_id: str) -> OrchestrationConnector:
        if not self.is_enabled(connector_id):
            raise OrchestrationConfigurationError(
                f"Connector '{connector_id}' is disabled in orchestration.yaml. "
                f"Set enabled: true to activate it."
            )

        module_path = _CONNECTOR_MODULE_MAP.get(connector_id)
        if module_path is None:
            raise ConnectorNotFoundError(
                f"No module mapping found for connector '{connector_id}'. "
                f"Add it to _CONNECTOR_MODULE_MAP in registry.py."
            )

        module_name, class_name = module_path.rsplit(".", 1)
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
        except (ImportError, AttributeError) as exc:
            raise ConnectorNotFoundError(
                f"Could not load connector '{connector_id}' from '{module_path}': {exc}. "
                f"Ensure the package is installed."
            ) from exc

        connector_config = self._config["orchestration"]["connectors"][connector_id]
        instance: OrchestrationConnector = cls(connector_config)
        logger.info("Loaded orchestration connector: %s", connector_id)
        return instance

    @staticmethod
    def _load_config(config_path: Path) -> dict:
        if not config_path.exists():
            raise FileNotFoundError(
                f"Orchestration config not found at: {config_path}"
            )
        with config_path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh)
