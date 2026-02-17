"""Real-time cost tracking for API usage."""

from threading import Lock
from typing import Optional, Dict
from datetime import datetime

from utils.logger import get_logger
from utils.exceptions import BudgetExceededError

logger = get_logger(__name__)


class CostTracker:
    """Thread-safe cost tracker for batch processing.

    Tracks costs from Tavily and LLM API calls with budget enforcement.
    """

    def __init__(self, budget_limit: Optional[float] = None):
        """Initialize the cost tracker.

        Args:
            budget_limit: Optional budget limit in dollars
        """
        self.budget_limit = budget_limit
        self.lock = Lock()

        # Cost breakdown
        self.costs = {
            "tavily": 0.0,
            "tavily_calls": 0,
            "openrouter": 0.0,
            "openrouter_calls": 0,
            "openrouter_input_tokens": 0,
            "openrouter_output_tokens": 0,
            "total": 0.0
        }

        # Pricing (per API documentation)
        self.pricing = {
            "tavily_per_result": 0.001,  # $0.001 per search result
            "openrouter_input_per_1m": 0.075,  # Gemini Flash 3: $0.075 per 1M input tokens
            "openrouter_output_per_1m": 0.30,  # Gemini Flash 3: $0.30 per 1M output tokens
        }

        self.start_time = datetime.now()

    def record_tavily_call(self, results_count: int = 30):
        """Record cost of Tavily API call.

        Args:
            results_count: Number of search results (default: 30)
        """
        cost = results_count * self.pricing["tavily_per_result"]

        with self.lock:
            self.costs["tavily"] += cost
            self.costs["tavily_calls"] += 1
            self.costs["total"] += cost
            self._check_budget()

        logger.debug(f"Tavily call: {results_count} results = ${cost:.4f}")

    def record_llm_call(self, input_tokens: int, output_tokens: int):
        """Record cost of LLM API call.

        Args:
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
        """
        input_cost = input_tokens * self.pricing["openrouter_input_per_1m"] / 1_000_000
        output_cost = output_tokens * self.pricing["openrouter_output_per_1m"] / 1_000_000
        total_cost = input_cost + output_cost

        with self.lock:
            self.costs["openrouter"] += total_cost
            self.costs["openrouter_calls"] += 1
            self.costs["openrouter_input_tokens"] += input_tokens
            self.costs["openrouter_output_tokens"] += output_tokens
            self.costs["total"] += total_cost
            self._check_budget()

        logger.debug(f"LLM call: {input_tokens} in + {output_tokens} out = ${total_cost:.4f}")

    def _check_budget(self):
        """Check if budget exceeded (must be called with lock held).

        Raises:
            BudgetExceededError: If budget limit exceeded
        """
        if self.budget_limit and self.costs["total"] > self.budget_limit:
            raise BudgetExceededError(
                f"Budget limit ${self.budget_limit:.2f} exceeded. "
                f"Current cost: ${self.costs['total']:.2f}"
            )

    def get_summary(self) -> Dict[str, any]:
        """Get cost summary.

        Returns:
            Dictionary with cost breakdown and statistics
        """
        with self.lock:
            elapsed = (datetime.now() - self.start_time).total_seconds()

            summary = {
                # Cost breakdown
                "tavily_cost": self.costs["tavily"],
                "tavily_calls": self.costs["tavily_calls"],
                "openrouter_cost": self.costs["openrouter"],
                "openrouter_calls": self.costs["openrouter_calls"],
                "total_cost": self.costs["total"],

                # Token usage
                "input_tokens": self.costs["openrouter_input_tokens"],
                "output_tokens": self.costs["openrouter_output_tokens"],
                "total_tokens": self.costs["openrouter_input_tokens"] + self.costs["openrouter_output_tokens"],

                # Budget
                "budget_limit": self.budget_limit,
                "budget_remaining": self.budget_limit - self.costs["total"] if self.budget_limit else None,
                "budget_used_percent": (self.costs["total"] / self.budget_limit * 100) if self.budget_limit else None,

                # Time
                "elapsed_seconds": elapsed,
                "cost_per_minute": (self.costs["total"] / (elapsed / 60)) if elapsed > 0 else 0
            }

            return summary

    def get_formatted_summary(self) -> str:
        """Get formatted cost summary as string.

        Returns:
            Formatted string with cost breakdown
        """
        summary = self.get_summary()

        lines = [
            "\n[COST SUMMARY]",
            f"  Tavily: ${summary['tavily_cost']:.2f} ({summary['tavily_calls']} calls)",
            f"  OpenRouter: ${summary['openrouter_cost']:.2f} ({summary['openrouter_calls']} calls)",
            f"    - Input tokens: {summary['input_tokens']:,}",
            f"    - Output tokens: {summary['output_tokens']:,}",
            f"  Total: ${summary['total_cost']:.2f}"
        ]

        if self.budget_limit:
            lines.append(f"  Budget: ${summary['total_cost']:.2f} / ${summary['budget_limit']:.2f} "
                        f"({summary['budget_used_percent']:.1f}%)")
            lines.append(f"  Remaining: ${summary['budget_remaining']:.2f}")

        return "\n".join(lines)

    def get_progress_display(self) -> str:
        """Get compact cost display for progress bar.

        Returns:
            Compact string like "$12.50/50.00 (25%)"
        """
        with self.lock:
            if self.budget_limit:
                return f"${self.costs['total']:.2f}/${self.budget_limit:.2f}"
            else:
                return f"${self.costs['total']:.2f}"

    def reset(self):
        """Reset cost tracking."""
        with self.lock:
            self.costs = {
                "tavily": 0.0,
                "tavily_calls": 0,
                "openrouter": 0.0,
                "openrouter_calls": 0,
                "openrouter_input_tokens": 0,
                "openrouter_output_tokens": 0,
                "total": 0.0
            }
            self.start_time = datetime.now()
