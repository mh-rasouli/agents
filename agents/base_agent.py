"""Base agent class with common functionality."""

from abc import ABC, abstractmethod
from typing import Dict, Any

# Modular imports
from models import BrandIntelligenceState
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
