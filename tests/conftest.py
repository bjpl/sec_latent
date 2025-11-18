"""
Pytest Configuration and Global Fixtures
Shared fixtures for all test modules
"""
import pytest
import asyncio
from typing import Dict, Any, Generator
from unittest.mock import Mock, AsyncMock, patch
import tempfile
import os

# FastAPI test dependencies
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Application imports (will be created)
from config.settings import Settings, get_settings


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_settings() -> Settings:
    """Test configuration settings"""
    with tempfile.TemporaryDirectory() as tmpdir:
        os.environ.update({
            "ENVIRONMENT": "testing",
            "DEBUG": "true",
            "SUPABASE_URL": "http://test-supabase:54321",
            "SUPABASE_KEY": "test-key",
            "SUPABASE_SERVICE_ROLE_KEY": "test-service-key",
            "DUCKDB_PATH": f"{tmpdir}/test.duckdb",
            "SEC_USER_AGENT": "test-agent test@example.com",
            "SONNET_ENDPOINT": "http://test-sonnet/v1",
            "SONNET_API_KEY": "test-sonnet-key",
            "HAIKU_ENDPOINT": "http://test-haiku/v1",
            "HAIKU_API_KEY": "test-haiku-key",
            "CELERY_BROKER_URL": "redis://test-redis:6379/0",
            "CELERY_RESULT_BACKEND": "redis://test-redis:6379/0"
        })
        settings = Settings()
        yield settings


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client"""
    mock_client = Mock()
    mock_client.table = Mock(return_value=Mock())
    mock_client.table().select = Mock(return_value=Mock())
    mock_client.table().insert = Mock(return_value=Mock())
    mock_client.table().update = Mock(return_value=Mock())
    mock_client.table().delete = Mock(return_value=Mock())
    return mock_client


@pytest.fixture
def mock_duckdb_connection():
    """Mock DuckDB connection"""
    mock_conn = Mock()
    mock_conn.execute = Mock(return_value=Mock())
    mock_conn.fetchall = Mock(return_value=[])
    mock_conn.fetchone = Mock(return_value=None)
    return mock_conn


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic API client"""
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.content = [Mock(text="Test analysis response")]
    mock_response.usage = Mock(input_tokens=100, output_tokens=200)
    mock_response.stop_reason = "end_turn"
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    return mock_client


@pytest.fixture
def sample_filing_data() -> Dict[str, Any]:
    """Sample SEC filing data for testing"""
    return {
        "cik": "0000789019",
        "company_name": "Microsoft Corporation",
        "form_type": "10-K",
        "filing_date": "2024-07-31",
        "accession_number": "0000789019-24-000456",
        "text_content": """
        Management's Discussion and Analysis

        Revenue increased 15% year-over-year to $245 billion.
        Operating income grew 20% to $110 billion.
        Cloud revenue increased 25% to $112 billion.

        Risk Factors:
        We face intense competition in the cloud services market.
        Regulatory compliance requirements continue to increase.
        Cybersecurity threats pose ongoing operational risks.
        """,
        "sections": {
            "md_and_a": "Management's Discussion and Analysis...",
            "risk_factors": "Risk Factors: Competition, Regulation...",
            "financial_statements": "Balance Sheet, Income Statement..."
        },
        "tables": [
            {
                "index": 0,
                "type": "income_statement",
                "data": [
                    ["Revenue", "245000000000"],
                    ["Operating Income", "110000000000"],
                    ["Net Income", "88000000000"]
                ]
            }
        ]
    }


@pytest.fixture
def sample_signals() -> Dict[str, Any]:
    """Sample extracted signals"""
    return {
        "financial": [
            {"name": "revenue_growth", "value": 0.15, "confidence": 0.95},
            {"name": "operating_margin", "value": 0.45, "confidence": 0.92},
            {"name": "cash_flow", "value": "positive", "confidence": 0.90}
        ],
        "sentiment": [
            {"name": "md_and_a_sentiment", "value": 0.75, "confidence": 0.85},
            {"name": "forward_looking_sentiment", "value": 0.65, "confidence": 0.80}
        ],
        "risk": [
            {"name": "market_risk", "value": 0.6, "confidence": 0.88},
            {"name": "regulatory_risk", "value": 0.7, "confidence": 0.85}
        ],
        "management": [
            {"name": "management_changes", "value": 0, "confidence": 0.95}
        ]
    }


@pytest.fixture
def sample_prediction() -> Dict[str, Any]:
    """Sample prediction result"""
    return {
        "filing_id": "test-filing-123",
        "prediction_type": "price_movement",
        "prediction": {
            "direction": "up",
            "magnitude": 0.05,
            "confidence": 0.78,
            "time_horizon": "1_month"
        },
        "model_used": "claude-3-5-sonnet-20241022",
        "signals_used": 85,
        "timestamp": "2024-10-18T00:00:00Z"
    }


@pytest.fixture
def mock_celery_task():
    """Mock Celery task"""
    mock_task = Mock()
    mock_task.delay = Mock(return_value=Mock(id="test-task-123"))
    mock_task.apply_async = Mock(return_value=Mock(id="test-task-123"))
    return mock_task


@pytest.fixture
def mock_redis_client():
    """Mock Redis client for caching"""
    mock_redis = Mock()
    mock_redis.get = Mock(return_value=None)
    mock_redis.set = Mock(return_value=True)
    mock_redis.delete = Mock(return_value=True)
    mock_redis.exists = Mock(return_value=False)
    mock_redis.expire = Mock(return_value=True)
    return mock_redis


@pytest.fixture
async def async_client(test_settings) -> Generator:
    """Async test client for API testing"""
    # Import will be created with API
    # from api.main import app
    # async with AsyncClient(app=app, base_url="http://test") as client:
    #     yield client
    mock_client = AsyncMock()
    yield mock_client


@pytest.fixture
def sync_client(test_settings) -> Generator:
    """Sync test client for API testing"""
    # from api.main import app
    # with TestClient(app) as client:
    #     yield client
    mock_client = Mock()
    yield mock_client


# Performance testing fixtures

@pytest.fixture
def performance_metrics():
    """Track performance metrics during tests"""
    metrics = {
        "response_times": [],
        "cache_hits": 0,
        "cache_misses": 0,
        "api_calls": 0,
        "errors": 0
    }
    return metrics


@pytest.fixture
def benchmark_timer():
    """Timer for benchmarking test execution"""
    import time

    class Timer:
        def __init__(self):
            self.start_time = None
            self.end_time = None

        def start(self):
            self.start_time = time.perf_counter()

        def stop(self):
            self.end_time = time.perf_counter()

        @property
        def elapsed_ms(self):
            if self.start_time and self.end_time:
                return (self.end_time - self.start_time) * 1000
            return None

    return Timer()


# WebSocket testing fixtures

@pytest.fixture
def mock_websocket():
    """Mock WebSocket connection"""
    mock_ws = AsyncMock()
    mock_ws.accept = AsyncMock()
    mock_ws.send_json = AsyncMock()
    mock_ws.send_text = AsyncMock()
    mock_ws.receive_json = AsyncMock()
    mock_ws.receive_text = AsyncMock()
    mock_ws.close = AsyncMock()
    return mock_ws


# Database fixtures

@pytest.fixture
async def test_database(test_settings):
    """Test database setup and teardown"""
    # Setup test database
    # This would create temporary tables for testing
    db_state = {"initialized": True, "tables": []}

    yield db_state

    # Teardown - clean up test data
    pass


# Marker for slow tests
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )
    config.addinivalue_line(
        "markers", "websocket: marks tests as websocket tests"
    )
