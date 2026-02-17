"""LangGraph workflow definition for brand intelligence system."""

from langgraph.graph import StateGraph, END

# Modular imports
from models import BrandIntelligenceState
from agents import (
    DataCollectionAgent,
    RelationshipMappingAgent,
    CategorizationAgent,
    ProductCatalogAgent,
    StrategicInsightsAgent,
    OutputFormatterAgent,
    CustomerIntelligenceAgent,
)
from utils import get_logger
from utils.exceptions import APIKeyError
from utils.llm_client import llm_client

logger = get_logger(__name__)


def create_workflow(google_sheets_credentials: str = None, google_sheets_id: str = None) -> StateGraph:
    """Create and configure the LangGraph workflow.

    Args:
        google_sheets_credentials: Path to Google service account JSON credentials (optional)
        google_sheets_id: Google Sheets ID for customer intelligence data (optional)

    Returns:
        Configured StateGraph ready for execution
    """
    logger.info("Creating brand intelligence workflow...")

    # Initialize all agents
    data_collector = DataCollectionAgent()
    relationship_mapper = RelationshipMappingAgent()
    categorizer = CategorizationAgent()
    product_catalog_extractor = ProductCatalogAgent()
    insights_generator = StrategicInsightsAgent()
    formatter = OutputFormatterAgent()

    # Initialize customer intelligence agent if credentials provided
    customer_intelligence_enabled = False
    if google_sheets_credentials and google_sheets_id:
        try:
            customer_intelligence = CustomerIntelligenceAgent(
                google_sheets_credentials,
                google_sheets_id
            )
            customer_intelligence_enabled = True
            logger.info("[OK] Customer Intelligence Agent enabled")
        except Exception as e:
            logger.warning(f"Could not initialize Customer Intelligence Agent: {e}")

    # Create the graph
    workflow = StateGraph(BrandIntelligenceState)

    # Add nodes (agents)
    workflow.add_node("data_collection", data_collector.execute)
    workflow.add_node("relationship_mapping", relationship_mapper.execute)
    workflow.add_node("categorization", categorizer.execute)
    workflow.add_node("product_catalog_extraction", product_catalog_extractor.execute)
    workflow.add_node("insights_generation", insights_generator.execute)
    workflow.add_node("output_formatting", formatter.execute)

    # Add customer intelligence node if enabled
    if customer_intelligence_enabled:
        workflow.add_node("customer_intelligence", customer_intelligence.execute)

    # Define the workflow edges (sequential pipeline)
    workflow.set_entry_point("data_collection")
    workflow.add_edge("data_collection", "relationship_mapping")
    workflow.add_edge("relationship_mapping", "categorization")
    workflow.add_edge("categorization", "product_catalog_extraction")
    workflow.add_edge("product_catalog_extraction", "insights_generation")
    workflow.add_edge("insights_generation", "output_formatting")

    # Connect customer intelligence after output formatting
    if customer_intelligence_enabled:
        workflow.add_edge("output_formatting", "customer_intelligence")
        workflow.add_edge("customer_intelligence", END)
    else:
        workflow.add_edge("output_formatting", END)

    logger.info("[OK] Workflow created successfully")

    return workflow


def run_workflow(
    brand_name: str,
    brand_website: str = None,
    parent_company: str = None,
    google_sheets_credentials: str = None,
    google_sheets_id: str = None,
    skip_api_validation: bool = False
) -> dict:
    """Run the brand intelligence workflow.

    Args:
        brand_name: Name of the brand to analyze
        brand_website: Optional website URL
        parent_company: Optional parent company name
        google_sheets_credentials: Path to Google service account JSON credentials (optional)
        google_sheets_id: Google Sheets ID for customer intelligence data (optional)
        skip_api_validation: Skip API validation (used in batch mode where validation happens once)

    Returns:
        Final state with all analysis results
    """
    logger.info(f"Starting brand intelligence analysis for: {brand_name}")

    # Validate API key before starting (fail fast) - unless already validated in batch mode
    if not skip_api_validation:
        logger.info("Validating OpenRouter API key...")
        try:
            llm_client.validate_api_key_with_test_call()
        except APIKeyError as e:
            logger.error("API key validation failed - stopping immediately")
            raise  # Re-raise to stop processing

    # Create workflow
    workflow = create_workflow(google_sheets_credentials, google_sheets_id)

    # Compile the graph
    app = workflow.compile()

    # Initialize state
    initial_state = BrandIntelligenceState(
        brand_name=brand_name,
        brand_website=brand_website,
        parent_company=parent_company,
        raw_data={},
        relationships={},
        categorization={},
        product_catalog={},
        insights={},
        outputs={},
        errors=[],
        timestamp=None,
        processing_time=None
    )

    # Execute workflow
    try:
        import time
        start_time = time.time()

        final_state = app.invoke(initial_state)

        processing_time = time.time() - start_time
        final_state["processing_time"] = processing_time

        logger.info(f"[OK] Workflow completed in {processing_time:.2f} seconds")

        # Log summary
        _log_summary(final_state)

        return final_state

    except Exception as e:
        logger.error(f"Workflow execution failed: {e}")
        raise


def _log_summary(state: dict) -> None:
    """Log a summary of the workflow results.

    Args:
        state: Final workflow state
    """
    logger.info("\n" + "="*60)
    logger.info("WORKFLOW SUMMARY")
    logger.info("="*60)

    logger.info(f"Brand: {state['brand_name']}")

    if state.get("outputs"):
        logger.info("\nGenerated outputs:")
        for format_type, filepath in state["outputs"].items():
            logger.info(f"  - {format_type.upper()}: {filepath}")

    if state.get("errors"):
        logger.warning(f"\nErrors encountered: {len(state['errors'])}")
        for error in state["errors"]:
            logger.warning(f"  - [{error.get('agent', 'Unknown')}] {error.get('error', 'Unknown error')}")

    logger.info(f"\nProcessing time: {state.get('processing_time', 0):.2f} seconds")
    logger.info("="*60 + "\n")
