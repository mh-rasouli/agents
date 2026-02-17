"""Custom exceptions for brand intelligence system."""


class BrandIntelligenceError(Exception):
    """Base exception for brand intelligence errors."""
    pass


class APIKeyError(BrandIntelligenceError):
    """Raised when API key is invalid, missing, or disconnected."""

    def __init__(self, message="OpenRouter API key is invalid or disconnected", provider="OpenRouter"):
        self.provider = provider
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return f"""
╔══════════════════════════════════════════════════════════════╗
║                     API KEY ERROR                            ║
╚══════════════════════════════════════════════════════════════╝

❌ {self.provider} API authentication failed

{self.message}

ACTIONS REQUIRED:
1. Check your API key in .env file:
   OPENROUTER_API_KEY=sk-or-v1-YOUR_KEY_HERE

2. Verify your API key is valid:
   - Visit: https://openrouter.ai/keys
   - Check if key is active
   - Verify you have credits

3. Test your API key:
   python test_api.py

4. Once fixed, resume processing:
   python main.py --google-sheets --resume

Progress has been saved. You won't lose any work.
═══════════════════════════════════════════════════════════════
"""


class TavilyAPIKeyError(BrandIntelligenceError):
    """Raised when Tavily API key is invalid."""

    def __init__(self, message="Tavily API key is invalid or quota exceeded"):
        self.message = message
        super().__init__(self.message)


class BudgetExceededError(BrandIntelligenceError):
    """Raised when processing budget is exceeded."""

    def __init__(self, current_cost, budget_limit):
        self.current_cost = current_cost
        self.budget_limit = budget_limit
        self.message = f"Budget exceeded: ${current_cost:.2f} / ${budget_limit:.2f}"
        super().__init__(self.message)


class CheckpointError(BrandIntelligenceError):
    """Raised when checkpoint save/load fails."""
    pass
