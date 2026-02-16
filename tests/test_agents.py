"""Unit tests for agents."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from models.state import BrandIntelligenceState
from agents.data_collection_agent import DataCollectionAgent
from agents.relationship_agent import RelationshipMappingAgent
from agents.categorization_agent import CategorizationAgent
from agents.insights_agent import StrategicInsightsAgent
from agents.formatter_agent import OutputFormatterAgent


@pytest.fixture
def sample_state():
    """Create a sample state for testing."""
    return BrandIntelligenceState(
        brand_name="تست برند",
        brand_website="https://test.com",
        raw_data={
            "scraped": {
                "web_search": {
                    "source": "web_search",
                    "brand_name": "تست برند",
                    "page_title": "Test Brand",
                    "meta_data": {"description": "Test description"}
                }
            },
            "structured": {
                "legal_name_fa": "تست برند",
                "industry": "تجارت الکترونیک"
            }
        },
        relationships={
            "parent_company": {"name": "Parent Corp"},
            "subsidiaries": [],
            "sister_brands": []
        },
        categorization={
            "primary_industry": {
                "name_fa": "تجارت الکترونیک",
                "name_en": "E-commerce"
            },
            "business_model": "B2C"
        },
        insights={},
        outputs={},
        errors=[],
        timestamp=None,
        processing_time=None
    )


class TestDataCollectionAgent:
    """Test cases for DataCollectionAgent."""

    @pytest.fixture
    def agent(self):
        """Create DataCollectionAgent instance."""
        return DataCollectionAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.agent_name == "DataCollectionAgent"
        assert len(agent.scrapers) == 6

    def test_prepare_data_for_llm(self, agent):
        """Test data preparation for LLM."""
        raw_data = {
            "web_search": {
                "brand_name": "TestBrand",
                "page_title": "Test",
                "raw_html": "<html>...</html>"
            },
            "codal": {
                "revenue": 1000000,
                "profit": 200000
            }
        }

        result = agent._prepare_data_for_llm(raw_data)

        assert "web_search" in result.upper()
        assert "brand_name" in result
        assert "raw_html" not in result  # Should exclude raw HTML

    @patch.object(DataCollectionAgent, '_scrape_all_sources')
    def test_execute_with_no_data(self, mock_scrape, agent, sample_state):
        """Test execute when no data is collected."""
        mock_scrape.return_value = {
            "web_search": None,
            "codal": None,
            "tsetmc": None,
            "linka": None,
            "trademark": None,
            "rasmio": None
        }

        result = agent.execute(sample_state)

        assert "errors" in result
        assert len(result["errors"]) > 0


class TestRelationshipMappingAgent:
    """Test cases for RelationshipMappingAgent."""

    @pytest.fixture
    def agent(self):
        """Create RelationshipMappingAgent instance."""
        return RelationshipMappingAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.agent_name == "RelationshipMappingAgent"

    def test_execute_with_no_data(self, agent):
        """Test execute with no raw data."""
        state = BrandIntelligenceState(
            brand_name="Test",
            brand_website=None,
            raw_data={},
            relationships={},
            categorization={},
            insights={},
            outputs={},
            errors=[],
            timestamp=None,
            processing_time=None
        )

        result = agent.execute(state)

        assert result["relationships"] == {}
        assert len(result["errors"]) > 0

    def test_prepare_relationship_data(self, agent, sample_state):
        """Test relationship data preparation."""
        result = agent._prepare_relationship_data(
            "TestBrand",
            sample_state["raw_data"]
        )

        assert "STRUCTURED DATA" in result or "structured" in result.lower()


class TestCategorizationAgent:
    """Test cases for CategorizationAgent."""

    @pytest.fixture
    def agent(self):
        """Create CategorizationAgent instance."""
        return CategorizationAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.agent_name == "CategorizationAgent"

    def test_execute_with_no_data(self, agent):
        """Test execute with no raw data."""
        state = BrandIntelligenceState(
            brand_name="Test",
            brand_website=None,
            raw_data={},
            relationships={},
            categorization={},
            insights={},
            outputs={},
            errors=[],
            timestamp=None,
            processing_time=None
        )

        result = agent.execute(state)

        assert result["categorization"] == {}
        assert len(result["errors"]) > 0

    def test_prepare_categorization_data(self, agent, sample_state):
        """Test categorization data preparation."""
        result = agent._prepare_categorization_data(
            "TestBrand",
            sample_state["raw_data"],
            sample_state["relationships"]
        )

        assert len(result) > 0


class TestStrategicInsightsAgent:
    """Test cases for StrategicInsightsAgent."""

    @pytest.fixture
    def agent(self):
        """Create StrategicInsightsAgent instance."""
        return StrategicInsightsAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.agent_name == "StrategicInsightsAgent"

    def test_execute_with_no_data(self, agent):
        """Test execute with no data."""
        state = BrandIntelligenceState(
            brand_name="Test",
            brand_website=None,
            raw_data={},
            relationships={},
            categorization={},
            insights={},
            outputs={},
            errors=[],
            timestamp=None,
            processing_time=None
        )

        result = agent.execute(state)

        assert result["insights"] == {}
        assert len(result["errors"]) > 0

    def test_prepare_insights_data(self, agent, sample_state):
        """Test insights data preparation."""
        result = agent._prepare_insights_data(
            "TestBrand",
            sample_state["raw_data"],
            sample_state["relationships"],
            sample_state["categorization"]
        )

        assert len(result) > 0
        assert "BRAND DATA" in result or "brand" in result.lower()


class TestOutputFormatterAgent:
    """Test cases for OutputFormatterAgent."""

    @pytest.fixture
    def agent(self):
        """Create OutputFormatterAgent instance."""
        return OutputFormatterAgent()

    def test_initialization(self, agent):
        """Test agent initializes correctly."""
        assert agent.agent_name == "OutputFormatterAgent"
        assert agent.output_dir.exists()

    def test_generate_json(self, agent, sample_state, tmp_path):
        """Test JSON generation."""
        agent.output_dir = tmp_path

        json_path = agent._generate_json(sample_state, "test_brand_123")

        assert json_path.exists()
        assert json_path.suffix == ".json"

        # Verify JSON is valid
        import json
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        assert data["brand_name"] == "تست برند"

    def test_generate_csv(self, agent, sample_state, tmp_path):
        """Test CSV generation."""
        agent.output_dir = tmp_path

        csv_path = agent._generate_csv(sample_state, "test_brand_123")

        assert csv_path.exists()
        assert csv_path.suffix == ".csv"

    def test_generate_txt(self, agent, sample_state, tmp_path):
        """Test TXT generation."""
        agent.output_dir = tmp_path

        txt_path = agent._generate_txt(sample_state, "test_brand_123")

        assert txt_path.exists()
        assert txt_path.suffix == ".txt"

        # Verify format is key-value
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        assert "brand_name:" in content

    def test_generate_markdown(self, agent, sample_state, tmp_path):
        """Test Markdown generation."""
        agent.output_dir = tmp_path

        md_path = agent._generate_markdown(sample_state, "test_brand_123")

        assert md_path.exists()
        assert md_path.suffix == ".md"

    def test_execute(self, agent, sample_state, tmp_path):
        """Test full execute method."""
        agent.output_dir = tmp_path

        result = agent.execute(sample_state)

        assert "outputs" in result
        assert len(result["outputs"]) == 4  # JSON, CSV, TXT, MD
        assert "json" in result["outputs"]
        assert "csv" in result["outputs"]
        assert "txt" in result["outputs"]
        assert "markdown" in result["outputs"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
