"""Base agent class with common functionality."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Type

from pydantic import BaseModel

# Modular imports
from models import BrandIntelligenceState
from models.output_models import validate_agent_output
from utils import llm_client, get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the workflow."""

    def __init__(self, agent_name: str):
        """Initialize the agent.

        Args:
            agent_name: Name of the agent
        """
        self.agent_name = agent_name
        self.llm = llm_client

    @abstractmethod
    def execute(self, state: BrandIntelligenceState) -> BrandIntelligenceState:
        """Execute the agent's task.

        This method must be implemented by subclasses.

        Args:
            state: Current workflow state

        Returns:
            Updated workflow state
        """
        pass

    def _log_start(self) -> None:
        """Log agent execution start."""
        logger.info(f"{'='*60}")
        logger.info(f"Starting {self.agent_name}")
        logger.info(f"{'='*60}")

    def _log_end(self, success: bool = True) -> None:
        """Log agent execution end.

        Args:
            success: Whether execution was successful
        """
        status = "Completed" if success else "Failed"
        logger.info(f"{self.agent_name} {status}")
        logger.info(f"{'='*60}\n")

    def _add_error(self, state: BrandIntelligenceState, error_msg: str) -> None:
        """Add an error to the state.

        Args:
            state: Current workflow state
            error_msg: Error message to add
        """
        if "errors" not in state:
            state["errors"] = []
        state["errors"].append({
            "agent": self.agent_name,
            "error": error_msg
        })
        logger.error(f"[{self.agent_name}] {error_msg}")

    def _validate_and_store(
        self,
        state: BrandIntelligenceState,
        key: str,
        data: Any,
        model_class: Type[BaseModel],
    ) -> None:
        """Validate agent output with a Pydantic model and store in state.

        On success the validated dict is stored; on failure the original
        data is stored unchanged and a validation warning is recorded in
        state["errors"].

        Args:
            state: Current workflow state
            key: State key to write to (e.g. "raw_data")
            data: The raw dict produced by the agent
            model_class: Pydantic model to validate against
        """
        validated, warnings = validate_agent_output(data, model_class, self.agent_name)

        if validated is not None:
            # Store the validated model dumped back to dict so state stays
            # JSON-serialisable and downstream code sees plain dicts.
            state[key] = validated.model_dump(mode="python")
        else:
            # Validation failed — store original data and record warning.
            state[key] = data
            if warnings:
                if "errors" not in state:
                    state["errors"] = []
                state["errors"].append(warnings)
