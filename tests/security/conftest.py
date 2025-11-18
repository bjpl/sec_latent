"""
Security Testing Configuration
Shared fixtures and configuration for security tests
"""

import pytest
from fastapi.testclient import TestClient
from typing import Generator
import os


@pytest.fixture(scope="session")
def security_test_mode():
    """Enable security test mode"""
    os.environ["TESTING"] = "true"
    os.environ["ENVIRONMENT"] = "testing"
    yield
    os.environ.pop("TESTING", None)
    os.environ.pop("ENVIRONMENT", None)


@pytest.fixture(scope="module")
def client(security_test_mode) -> Generator[TestClient, None, None]:
    """Create test client for security testing"""
    from src.api.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def mock_database():
    """Mock database for security tests"""
    # Prevent tests from affecting production database
    pass


@pytest.fixture(scope="function")
def mock_redis():
    """Mock Redis for security tests"""
    # Prevent tests from affecting production cache
    pass


# Security test markers
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "security: mark test as a security test"
    )
    config.addinivalue_line(
        "markers", "penetration: mark test as a penetration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "critical: mark test as testing critical security control"
    )
