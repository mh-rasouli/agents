"""LangGraph state models for the brand intelligence workflow."""

from typing import TypedDict, Optional, Any
from typing_extensions import Annotated
from langgraph.graph import add_messages


class BrandIntelligenceState(TypedDict):
    """Shared state passed between agents in the workflow.

    This state accumulates brand intelligence data as it flows through
    the multi-agent pipeline.
    """

    # Input parameters
    brand_name: str
    brand_website: Optional[str]
    parent_company: Optional[str]  # Parent company provided by user

    # Agent outputs
    raw_data: dict  # Output from DataCollectionAgent
    relationships: dict  # Output from RelationshipMappingAgent
    categorization: dict  # Output from CategorizationAgent
    product_catalog: dict  # Output from ProductCatalogAgent
    insights: dict  # Output from StrategicInsightsAgent
    outputs: dict  # Output from OutputFormatterAgent

    # Error tracking
    errors: list  # List of errors encountered during processing

    # Metadata
    timestamp: Optional[str]
    processing_time: Optional[float]
