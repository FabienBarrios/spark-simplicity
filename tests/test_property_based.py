"""
Property-based testing using Hypothesis.

Tests edge cases and invariants that should always hold true,
regardless of the input data provided.
"""

import string
from unittest.mock import Mock

import pytest
from hypothesis import assume, example, given
from hypothesis import strategies as st
from hypothesis.stateful import RuleBasedStateMachine, invariant, rule

from spark_simplicity.connections.database_connection import JdbcSqlServerConnection


class TestDatabaseConnectionProperties:
    """Property-based tests for database connection invariants."""

    def setup_method(self):
        """Clear singleton instances before each test."""
        JdbcSqlServerConnection._instances.clear()

    def teardown_method(self):
        """Clear singleton instances after each test."""
        JdbcSqlServerConnection._instances.clear()

    @given(
        host=st.text(
            alphabet=string.ascii_letters + string.digits + ".-",
            min_size=1,
            max_size=50,
        ),
        database=st.text(
            alphabet=string.ascii_letters + string.digits + "_", min_size=1, max_size=30
        ),
        user=st.text(
            alphabet=string.ascii_letters + string.digits + "_", min_size=1, max_size=20
        ),
        password=st.text(min_size=1, max_size=50),
        app_id=st.text(
            alphabet=string.ascii_letters + string.digits, min_size=1, max_size=20
        ),
    )
    @example(
        host="localhost",
        database="testdb",
        user="testuser",
        password="testpass",
        app_id="test-app",
    )
    def test_connection_creation_always_succeeds_with_valid_inputs(
        self, host, database, user, password, app_id
    ):
        """
        Test that connection creation always succeeds with any valid string inputs.
        """
        # Filter out problematic inputs
        assume(not any(char in host for char in [" ", "\n", "\t", "\r"]))
        assume(not any(char in database for char in [" ", "\n", "\t", "\r", ";"]))
        assume(len(host.strip()) > 0)
        assume(len(database.strip()) > 0)
        assume(len(user.strip()) > 0)
        assume(len(password.strip()) > 0)
        assume(len(app_id.strip()) > 0)

        # Clear instances to avoid singleton conflicts
        JdbcSqlServerConnection._instances.clear()

        mock_spark = Mock()
        mock_spark.sparkContext.applicationId = app_id  # Use unique app_id
        mock_logger = Mock()

        config = {
            "host": host,
            "database": database,
            "user": user,
            "password": password,
        }

        # Should always succeed
        conn = JdbcSqlServerConnection(mock_spark, config, mock_logger)

        # Invariants that should always hold
        assert conn.host == host
        assert conn.database == database
        assert conn.user == user
        assert conn.password == password
        assert conn.port == "1433"  # Default port
        assert "jdbc:sqlserver://" in conn.jdbc_url
        assert f"databaseName={database}" in conn.jdbc_url

    @given(port=st.integers(min_value=1, max_value=65535))
    def test_port_handling_for_any_valid_port_number(self, port):
        """Test that any valid port number is handled correctly."""
        mock_spark = Mock()
        mock_spark.sparkContext.applicationId = "port-test"
        mock_logger = Mock()

        config = {
            "host": "testhost",
            "port": str(port),
            "database": "testdb",
            "user": "testuser",
            "password": "testpass",
        }

        conn = JdbcSqlServerConnection(mock_spark, config, mock_logger)

        # Port should be preserved as string
        assert conn.port == str(port)
        assert f":{port};" in conn.jdbc_url

    @given(
        app_id=st.text(
            alphabet=string.ascii_letters + string.digits + "-_",
            min_size=1,
            max_size=50,
        )
    )
    def test_singleton_behavior_with_different_app_ids(self, app_id):
        """Test singleton behavior holds for any application ID."""
        assume(len(app_id.strip()) > 0)

        mock_spark = Mock()
        mock_spark.sparkContext.applicationId = app_id
        mock_logger = Mock()

        config = {
            "host": "testhost",
            "database": "testdb",
            "user": "testuser",
            "password": "testpass",
        }

        # Create two connections with same config and app ID
        conn1 = JdbcSqlServerConnection(mock_spark, config, mock_logger)
        conn2 = JdbcSqlServerConnection(mock_spark, config, mock_logger)

        # Should be the same instance (singleton)
        assert conn1 is conn2


class DatabaseConnectionStateMachine(RuleBasedStateMachine):
    """Stateful property-based testing for database connection lifecycle."""

    def __init__(self):
        super().__init__()
        self.connections = {}
        self.mock_spark_sessions = {}
        JdbcSqlServerConnection._instances.clear()

    @rule(
        app_id=st.text(
            alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10
        ),
        host=st.text(
            alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10
        ),
        database=st.text(
            alphabet=string.ascii_letters + string.digits, min_size=1, max_size=10
        ),
    )
    def create_connection(self, app_id, host, database):
        """Create a new database connection."""
        # Create unique mock spark session
        mock_spark = Mock()
        mock_spark.sparkContext.applicationId = app_id
        mock_logger = Mock()

        config = {
            "host": host,
            "database": database,
            "user": "testuser",
            "password": "testpass",
        }

        conn_key = f"{app_id}:{host}:{database}"

        conn = JdbcSqlServerConnection(mock_spark, config, mock_logger)
        self.connections[conn_key] = conn
        self.mock_spark_sessions[conn_key] = mock_spark

    @rule()
    def create_duplicate_connection(self):
        """Create duplicate connection and verify singleton behavior."""
        if not self.connections:
            return

        # Pick a random existing connection config
        conn_key = next(iter(self.connections.keys()))
        original_conn = self.connections[conn_key]
        original_spark = self.mock_spark_sessions[conn_key]

        # Extract config from original connection
        config = {
            "host": original_conn.host,
            "database": original_conn.database,
            "user": original_conn.user,
            "password": original_conn.password,
        }

        # Create new connection with same config
        duplicate_conn = JdbcSqlServerConnection(original_spark, config, Mock())

        # Should be the same instance
        assert duplicate_conn is original_conn

    @invariant()
    def instances_dict_consistency(self):
        """Verify that instances dictionary is always consistent."""
        # Number of unique connection keys should match instances
        unique_keys = set()
        for conn_key, conn in self.connections.items():
            app_id, host, database = conn_key.split(":", 2)
            port = getattr(conn, "port", "1433")
            unique_db_key = f"{app_id}:{host}:{port}:{database}"
            unique_keys.add(unique_db_key)

        assert len(JdbcSqlServerConnection._instances) >= len(unique_keys)

    @invariant()
    def all_connections_have_required_attributes(self):
        """Verify all connections have required attributes."""
        for conn in self.connections.values():
            assert hasattr(conn, "host")
            assert hasattr(conn, "port")
            assert hasattr(conn, "database")
            assert hasattr(conn, "user")
            assert hasattr(conn, "password")
            assert hasattr(conn, "jdbc_url")
            assert hasattr(conn, "base_options")


# Create test class from state machine
TestDatabaseConnectionStateful = DatabaseConnectionStateMachine.TestCase


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
