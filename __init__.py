"""Brand Intelligence Agent - Multi-Agent System for Iranian Brand Analysis.

A comprehensive brand intelligence system leveraging LangGraph and Gemini 3 Pro
to analyze Iranian brands across multiple data sources.
"""

__version__ = "1.0.0"
__author__ = "Trend Agency"
__description__ = "Multi-Agent Brand Intelligence System for Iranian Market"

# Expose main components for easy importing
from graph import create_workflow, run_workflow
from config import settings

__all__ = [
    "create_workflow",
    "run_workflow",
    "settings",
    "__version__",
]
