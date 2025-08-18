"""
Global pytest configuration and shared fixtures.

Provides common test fixtures and configuration for all test modules.
Follows pytest best practices for fixture sharing and test isolation.
"""

import shutil
import tempfile
from pathlib import Path
from typing import Dict
from unittest.mock import Mock

import pytest
from pyspark.sql import SparkSession


@pytest.fixture(scope="session")
def test_data_dir():
    """Create temporary directory for test data files."""
    temp_dir = tempfile.mkdtemp(prefix="spark_simplicity_test_")
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def mock_spark_session():
    """Create mock SparkSession for unit tests."""
    mock_spark = Mock(spec=SparkSession)
    mock_context = Mock()
    mock_context.applicationId = "test-application-id"
    mock_spark.sparkContext = mock_context

    # Mock common SparkSession methods
    mock_spark.read = Mock()
    mock_spark.createDataFrame = Mock()
    mock_spark.sql = Mock()

    return mock_spark


@pytest.fixture(scope="function")
def mock_logger():
    """Create mock logger for testing."""
    return Mock()


@pytest.fixture(scope="function")
def sample_database_config() -> Dict[str, str]:
    """Standard database configuration for testing."""
    return {
        "host": "localhost",
        "port": "1433",
        "database": "test_database",
        "user": "test_user",
        "password": "test_password",
    }


@pytest.fixture(scope="function")
def minimal_database_config() -> Dict[str, str]:
    """Minimal database configuration (no port specified)."""
    return {
        "host": "test-host",
        "database": "test_db",
        "user": "user",
        "password": "pass",
    }


# Pytest configuration hooks
def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Add custom markers programmatically if needed
    config.addinivalue_line("markers", "database: Tests requiring database connection")
    config.addinivalue_line(
        "markers", "spark_required: Tests requiring real Spark session"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers automatically."""
    for item in items:
        # Auto-mark database tests
        if "database" in str(item.fspath).lower():
            item.add_marker(pytest.mark.database)

        # Auto-mark slow tests based on naming
        if "performance" in item.name or "stress" in item.name:
            item.add_marker(pytest.mark.slow)


# Test parametrization data
DATABASE_TEST_CONFIGS = [
    pytest.param(
        {"host": "localhost", "database": "db1", "user": "user1", "password": "pass1"},
        id="basic-config",
    ),
    pytest.param(
        {
            "host": "server.com",
            "port": "1434",
            "database": "db2",
            "user": "user2",
            "password": "pass2",
        },
        id="custom-port",
    ),
    pytest.param(
        {
            "host": "192.168.1.100",
            "database": "prod_db",
            "user": "prod_user",
            "password": "prod_pass",
        },
        id="production-like",
    ),
]
