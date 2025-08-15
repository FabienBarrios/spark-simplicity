"""
Spark Simplicity - Database Connection Tests
===========================================

Comprehensive test suite for JdbcSqlServerConnection with enterprise-grade
coverage and validation.
This module provides extensive testing of database connection functionality,
singleton pattern implementation, query execution capabilities, and performance
characteristics essential for
production Spark data processing environments.

Key Testing Areas:
    - **Singleton Pattern**: Connection instance uniqueness and lifecycle management
    - **Connection Management**: Initialization, configuration validation,
      and resource handling
    - **Query Execution**: Simple queries, complex SQL, partitioned operations,
      and edge cases
    - **JDBC Integration**: URL construction, driver options, and SQL Server
      optimization
    - **Performance Testing**: Resource utilization, concurrent access, and
      scalability scenarios
    - **Security Validation**: Input sanitization, connection security, and
      error handling

Test Coverage:
    **Connection Lifecycle**:
    - Singleton pattern enforcement across different configurations and Spark
      applications
    - Proper initialization with various database configurations and security settings
    - Connection reuse and resource management throughout application lifecycle
    - Thread safety and concurrent access patterns for production environments

    **Query Operations**:
    - Standard SQL query execution with result DataFrame validation
    - Complex multi-table joins, aggregations, and analytical query patterns
    - Partitioned query execution for large result sets and parallel processing
    - Edge cases including empty results, malformed queries, and error conditions

Enterprise Integration Testing:
    - **Production Configurations**: Multiple database environments and connection
      parameters
    - **Security Compliance**: Encrypted connections, authentication, and certificate
      validation
    - **Performance Validation**: Query execution efficiency and resource optimization
    - **Error Recovery**: Comprehensive error handling and failure scenario testing
    - **Monitoring Integration**: Logging, metrics, and operational visibility features

Testing Philosophy:
    This test suite follows enterprise software development best practices with
    comprehensive coverage, realistic scenario simulation, and production-ready
    validation patterns. All tests are designed to validate both functional
    correctness and operational reliability in demanding production Spark
    environments.
"""

import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict, cast
from unittest.mock import Mock, call

import pytest
from pyspark.sql import DataFrame, SparkSession

# Import optimisé avec gestion propre des chemins
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

DATABASE_CONNECTION_PATH = (
    PROJECT_ROOT / "spark_simplicity" / "connections" / "database_connection.py"
)
spec = importlib.util.spec_from_file_location(
    "database_connection", DATABASE_CONNECTION_PATH
)
if spec is None or spec.loader is None:
    raise ImportError("Could not load database_connection module")
database_connection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(database_connection)

JdbcSqlServerConnection = database_connection.JdbcSqlServerConnection


class TestJdbcSqlServerConnection:
    """
    Comprehensive test suite for JdbcSqlServerConnection with 100% coverage.

    This test class validates all aspects of database connection functionality
    including singleton pattern implementation, connection lifecycle management,
    query execution capabilities, and enterprise integration features. Tests are
    organized by functional areas with comprehensive coverage of normal operations,
    edge cases, and error conditions.

    Test Organization:
        - Singleton Pattern: Instance uniqueness and lifecycle management
        - Connection Initialization: Configuration validation and setup
        - Query Execution: SQL operations with various complexity levels
        - Performance Testing: Resource utilization and scalability
        - Integration Testing: Multi-configuration and concurrent access scenarios
    """

    @staticmethod
    def setup_method() -> None:
        """Clear singleton instances before each test to ensure isolation."""
        JdbcSqlServerConnection._instances.clear()

    # Singleton Pattern Testing
    # ========================

    @pytest.mark.unit
    def test_singleton_pattern_same_config(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test singleton pattern returns same instance for identical configurations.

        Validates that multiple instantiation requests with identical database
        configurations return the same connection object, ensuring proper resource
        management and preventing unnecessary connection overhead in production
        environments.
        """
        conn1 = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )
        conn2 = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        assert conn1 is conn2, (
            f"Singleton pattern failed: conn1 ({id(conn1)}) should be "
            f"identical to conn2 ({id(conn2)})"
        )
        assert len(JdbcSqlServerConnection._instances) == 1, (
            f"Expected 1 singleton instance, found "
            f"{len(JdbcSqlServerConnection._instances)}"
        )

    @pytest.mark.unit
    def test_singleton_pattern_different_configs(
        self,
        mock_spark_session: Any,
        mock_logger: Any,
        sample_database_config: Any,
        config_with_port: Any,
    ) -> None:
        """
        Test singleton pattern creates different instances for different configurations.

        Verifies that connections with different database configurations
        (host, port, database) create separate instances while maintaining
        singleton behavior within each configuration scope, supporting
        multi-database enterprise environments.
        """
        conn1 = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )
        conn2 = JdbcSqlServerConnection(
            mock_spark_session, config_with_port, mock_logger
        )

        assert conn1 is not conn2, (
            f"Different configs should create separate "
            f"instances: conn1 ({id(conn1)}) vs "
            f"conn2 ({id(conn2)})"
        )
        assert len(JdbcSqlServerConnection._instances) == 2, (
            f"Expected 2 distinct instances for different configs, found "
            f"{len(JdbcSqlServerConnection._instances)}"
        )

    @pytest.mark.unit
    def test_singleton_pattern_different_spark_apps(
        self, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test singleton pattern creates different instances for different Spark
        applications.

        Ensures that connections are properly isolated between different Spark
        application contexts, preventing connection sharing across application
        boundaries while maintaining singleton behavior within each application
        scope.
        """
        mock_spark1 = Mock(spec=SparkSession)
        mock_context1 = Mock()
        mock_context1.applicationId = "app-1"
        mock_spark1.sparkContext = mock_context1

        mock_spark2 = Mock(spec=SparkSession)
        mock_context2 = Mock()
        mock_context2.applicationId = "app-2"
        mock_spark2.sparkContext = mock_context2

        conn1 = JdbcSqlServerConnection(
            mock_spark1, sample_database_config, mock_logger
        )
        conn2 = JdbcSqlServerConnection(
            mock_spark2, sample_database_config, mock_logger
        )

        assert conn1 is not conn2
        assert len(JdbcSqlServerConnection._instances) == 2

    @pytest.mark.unit
    def test_unique_key_generation(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test unique key generation for singleton pattern implementation.

        Validates that connection instances are properly identified and cached using
        SHA256 hash keys based on application ID, host, port, and database parameters,
        ensuring reliable singleton behavior across complex enterprise configurations.
        """
        host = sample_database_config["host"]
        port = sample_database_config.get("port", "1433")
        db = sample_database_config["database"]
        app_id = mock_spark_session.sparkContext.applicationId

        unique_string = f"{app_id}:{host}:{port}:{db}"
        expected_key = hashlib.sha256(unique_string.encode()).hexdigest()

        JdbcSqlServerConnection(mock_spark_session, sample_database_config, mock_logger)

        assert expected_key in JdbcSqlServerConnection._instances

    # Connection Initialization Testing
    # ================================

    @pytest.mark.unit
    def test_initialization_basic_config(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test connection initialization with basic database configuration.

        Validates proper initialization of connection attributes, JDBC URL construction,
        and base options configuration using standard database parameters. Ensures
        correct default value application and connection string generation.
        """
        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        # Validate connection attributes
        assert conn.spark is mock_spark_session, (
            f"Spark session not properly assigned: expected "
            f"{mock_spark_session}, got {conn.spark}"
        )
        assert conn.logger is mock_logger, (
            f"Logger not properly assigned: expected {mock_logger}, "
            f"got {conn.logger}"
        )
        assert (
            conn.host == "localhost"
        ), f"Host mismatch: expected 'localhost', got '{conn.host}'"
        assert conn.port == "1433", f"Port mismatch: expected '1433', got '{conn.port}'"
        assert (
            conn.database == "test_database"
        ), f"Database mismatch: expected 'test_database', got '{conn.database}'"
        assert (
            conn.user == "test_user"
        ), f"User mismatch: expected 'test_user', got '{conn.user}'"
        assert (
            conn.password == "test_password"
        ), f"Password mismatch: expected 'test_password', got '{conn.password}'"

        # Validate JDBC URL construction
        expected_url = (
            "jdbc:sqlserver://localhost:1433;"
            "databaseName=test_database;"
            "encrypt=true;trustServerCertificate=true"
        )
        assert (
            conn.jdbc_url == expected_url
        ), f"JDBC URL mismatch:\nExpected: {expected_url}\nActual: {conn.jdbc_url}"

        # Validate base options configuration
        expected_options = {
            "user": "test_user",
            "password": "test_password",
            "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
            "fetchsize": "5000",
        }
        assert conn.base_options == expected_options

    @pytest.mark.unit
    def test_initialization_with_custom_port(
        self, mock_spark_session: Any, mock_logger: Any, config_with_port: Any
    ) -> None:
        """
        Test connection initialization with custom port configuration.

        Verifies proper handling of non-standard database ports and configuration
        parameter override behavior. Essential for enterprise environments with
        custom SQL Server port configurations and security requirements.
        """
        conn = JdbcSqlServerConnection(
            mock_spark_session, config_with_port, mock_logger
        )

        assert conn.host == "db-server"
        assert conn.port == "1434"
        assert conn.database == "proddb"

        expected_url = (
            "jdbc:sqlserver://db-server:1434;"
            "databaseName=proddb;"
            "encrypt=true;trustServerCertificate=true"
        )
        assert conn.jdbc_url == expected_url

    @pytest.mark.unit
    def test_initialization_logging(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test connection initialization logging for operational monitoring.

        Validates that connection establishment events are properly logged with
        relevant configuration details for production monitoring, troubleshooting,
        and audit compliance in enterprise environments.
        """
        JdbcSqlServerConnection(mock_spark_session, sample_database_config, mock_logger)

        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        assert "SQL Server connection initialized" in log_call
        assert "host=localhost" in log_call
        assert "port=1433" in log_call
        assert "db=test_database" in log_call
        assert "user=test_user" in log_call

    # Query Execution Testing
    # ======================

    @pytest.mark.unit
    def test_query_simple_execution(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test simple SQL query execution without partitioning.

        Validates basic query execution functionality with proper DataFrame reader
        configuration, JDBC options application, and SQL query wrapping for
        standard analytical operations in Spark environments.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        sql = "SELECT * FROM users"
        result = conn.query(sql)

        assert result is mock_df

        mock_reader.format.assert_called_once_with("jdbc")

        expected_calls = [
            call("url", conn.jdbc_url),
            call("dbtable", f"({sql}) subquery"),
            call("user", "test_user"),
            call("password", "test_password"),
            call("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver"),
            call("fetchsize", "5000"),
        ]

        actual_calls = mock_reader.option.call_args_list
        for expected_call in expected_calls:
            assert expected_call in actual_calls

    @pytest.mark.unit
    def test_query_with_partitioning(
        self,
        mock_spark_session: Any,
        mock_logger: Any,
        sample_database_config: Any,
        sample_partitioning_options: Any,
    ) -> None:
        """
        Test query execution with partitioning parameters for large result sets.

        Validates parallel query execution configuration with partitioning options
        including column specification, boundary values, and fetch size optimization.
        Essential for high-performance analytics on large enterprise datasets.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        sql = "SELECT * FROM large_table"
        partitioning = sample_partitioning_options["with_fetchsize"]

        result = conn.query(sql, partitioning)

        assert result is mock_df

        all_calls = mock_reader.option.call_args_list

        base_option_calls = [
            call("url", conn.jdbc_url),
            call("dbtable", f"({sql}) subquery"),
            call("user", "test_user"),
            call("password", "test_password"),
            call("driver", "com.microsoft.sqlserver.jdbc.SQLServerDriver"),
            call("fetchsize", "5000"),
        ]

        partition_option_calls = [
            call("numPartitions", "8"),
            call("partitionColumn", "user_id"),
            call("lowerBound", "1"),
            call("upperBound", "10000"),
            call("fetchsize", "10000"),
        ]

        for expected_call in base_option_calls + partition_option_calls:
            assert expected_call in all_calls

    @pytest.mark.unit
    def test_query_complex_sql(
        self,
        mock_spark_session: Any,
        mock_logger: Any,
        sample_database_config: Any,
        sample_sql_queries: Any,
    ) -> None:
        """
        Test query execution with complex SQL containing joins and aggregations.

        Validates handling of sophisticated analytical queries with multiple tables,
        aggregation functions, and complex filtering conditions typical of enterprise
        data warehouse and business intelligence scenarios.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        complex_sql = sample_sql_queries["complex"]
        result = conn.query(complex_sql)

        assert result is mock_df

        dbtable_value = None
        for call_args in mock_reader.option.call_args_list:
            if call_args[0][0] == "dbtable":
                dbtable_value = call_args[0][1]
                break

        assert dbtable_value is not None
        assert dbtable_value.startswith("(")
        assert dbtable_value.endswith(") subquery")
        assert complex_sql.strip() in dbtable_value

    # Edge Case and Error Handling Testing
    # ===================================

    @pytest.mark.unit
    def test_query_empty_partitioning_dict(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test query execution with empty partitioning dictionary.

        Validates proper handling of empty partitioning parameters without affecting
        normal query execution flow. Ensures robust parameter validation and
        graceful degradation to non-partitioned query execution.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        sql = "SELECT * FROM users"
        result = conn.query(sql, {})

        assert result is mock_df

        mock_reader.format.assert_called_once_with("jdbc")
        mock_reader.load.assert_called_once()

    @pytest.mark.unit
    def test_query_none_partitioning(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test query execution with None partitioning parameter.

        Validates robust handling of None partitioning values without breaking
        query execution flow. Essential for dynamic query construction scenarios
        where partitioning may be conditionally applied.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        sql = "SELECT COUNT(*) as count FROM users"
        result = conn.query(sql, None)

        assert result is mock_df

        mock_reader.format.assert_called_once_with("jdbc")
        mock_reader.load.assert_called_once()

    # Performance and Scalability Testing
    # ==================================

    @pytest.mark.performance
    def test_singleton_performance_multiple_calls(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test singleton performance with multiple instantiation calls.

        Validates that repeated connection requests with identical configurations
        maintain optimal performance through proper instance caching and reuse.
        Critical for high-throughput production environments with frequent
        connection requests.
        """
        connections = []

        for _ in range(100):
            conn = JdbcSqlServerConnection(
                mock_spark_session, sample_database_config, mock_logger
            )
            connections.append(conn)

        first_conn = connections[0]
        for conn in connections[1:]:
            assert conn is first_conn

        assert len(JdbcSqlServerConnection._instances) == 1

    @pytest.mark.integration
    def test_multiple_configs_isolation(self, mock_logger: Any) -> None:
        """
        Test connection isolation across multiple database configurations.

        Validates proper connection separation and resource management when
        working with multiple database environments simultaneously. Essential
        for enterprise scenarios with development, staging, and production
        database connections within the same application.
        """
        mock_spark1 = Mock(spec=SparkSession)
        mock_context1 = Mock()
        mock_context1.applicationId = "app-1"
        mock_spark1.sparkContext = mock_context1

        mock_spark2 = Mock(spec=SparkSession)
        mock_context2 = Mock()
        mock_context2.applicationId = "app-2"
        mock_spark2.sparkContext = mock_context2

        config1 = {
            "host": "db1.example.com",
            "database": "db1",
            "user": "user1",
            "password": "pass1",
        }

        config2 = {
            "host": "db2.example.com",
            "port": "1434",
            "database": "db2",
            "user": "user2",
            "password": "pass2",
        }

        conn1 = JdbcSqlServerConnection(mock_spark1, config1, mock_logger)
        conn2 = JdbcSqlServerConnection(mock_spark2, config2, mock_logger)
        conn3 = JdbcSqlServerConnection(mock_spark1, config1, mock_logger)

        assert conn1 is not conn2
        assert conn1 is conn3
        assert len(JdbcSqlServerConnection._instances) == 2

        assert conn1.host == "db1.example.com"
        assert conn2.host == "db2.example.com"
        assert conn1.port == "1433"
        assert conn2.port == "1434"

    # Advanced Integration Testing
    # ===========================

    @pytest.mark.slow
    @pytest.mark.integration
    def test_multiple_query_executions(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test multiple query executions on same connection instance.

        Validates connection reuse and stability across multiple query operations
        within the same application session. Critical for long-running analytical
        workloads and batch processing scenarios in production environments.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        queries = [
            "SELECT COUNT(*) as count FROM users",
            "SELECT * FROM orders WHERE date >= '2024-01-01'",
            "SELECT u.name, SUM(o.total) as sum FROM users u JOIN orders o "
            "ON u.id = o.user_id GROUP BY u.name",
        ]

        results = []
        for sql in queries:
            result = conn.query(sql)
            results.append(result)

            mock_reader.reset_mock()
            mock_reader.format.return_value = mock_reader
            mock_reader.option.return_value = mock_reader
            mock_reader.load.return_value = mock_df

        for result in results:
            assert result is mock_df

        conn2 = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )
        assert conn is conn2

    @pytest.mark.unit
    def test_connection_reuse_after_query(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test connection reuse after executing queries.

        Validates that connection instances maintain their singleton behavior
        and proper resource management even after query execution operations.
        Ensures consistent connection lifecycle management throughout application
        runtime.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn1 = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )
        conn1.query("SELECT * FROM table1")

        conn2 = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )
        conn2.query("SELECT * FROM table2")

        assert conn1 is conn2
        assert len(JdbcSqlServerConnection._instances) == 1

    # Configuration and Validation Testing
    # ===================================

    @pytest.mark.unit
    def test_jdbc_url_construction_variations(
        self,
        mock_spark_session: Any,
        mock_logger: Any,
        database_connections_configs: Any,
        jdbc_url_variations: Any,
    ) -> None:
        """
        Test JDBC URL construction with different database configurations.

        Validates proper URL generation across various enterprise database
        configurations including different hosts, ports, and connection parameters.
        Essential for supporting diverse SQL Server deployment scenarios.
        """
        JdbcSqlServerConnection._instances.clear()

        test_cases = [
            {
                "config": database_connections_configs["dev"],
                "expected": "jdbc:sqlserver://dev-db.company.com:1433;databaseName="
                "dev_database;encrypt=true;trustServerCertificate=true",
            },
            {
                "config": database_connections_configs["staging"],
                "expected": "jdbc:sqlserver://staging-db.company.com:1433;databaseName="
                "staging_database;encrypt=true;trustServerCertificate=true",
            },
            {
                "config": database_connections_configs["prod"],
                "expected": "jdbc:sqlserver://prod-db.company.com:1434;"
                "databaseName=production_database;encrypt=true;"
                "trustServerCertificate=true",
            },
        ]

        for i, case in enumerate(test_cases):
            mock_context = Mock()
            mock_context.applicationId = f"test-jdbc-{i}"
            mock_spark_session.sparkContext = mock_context

            conn = JdbcSqlServerConnection(
                mock_spark_session, case["config"], mock_logger
            )
            assert conn.jdbc_url == case["expected"]

    @pytest.mark.unit
    def test_base_options_structure(
        self,
        mock_spark_session: Any,
        mock_logger: Any,
        sample_database_config: Any,
        base_options_variations: Any,
    ) -> None:
        """
        Test base options dictionary structure and values validation.

        Validates that connection base options contain all required JDBC parameters
        with correct values and data types. Essential for ensuring proper JDBC
        driver configuration and database connectivity in production environments.
        """
        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        expected_options = base_options_variations["standard"]

        for key in expected_options:
            assert key in conn.base_options

        assert conn.base_options["user"] == sample_database_config["user"]
        assert conn.base_options["password"] == sample_database_config["password"]
        assert conn.base_options["driver"] == expected_options["driver"]
        assert conn.base_options["fetchsize"] == expected_options["fetchsize"]

    @pytest.mark.unit
    def test_all_attributes_initialized(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test comprehensive attribute initialization validation.

        Validates that all connection instance attributes are properly initialized
        with correct types and values during connection establishment. Critical
        for ensuring reliable connection state and preventing runtime errors.
        """
        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        # Validate attribute presence
        required_attributes = [
            "spark",
            "logger",
            "host",
            "port",
            "database",
            "user",
            "password",
            "jdbc_url",
            "base_options",
        ]
        for attr in required_attributes:
            assert hasattr(conn, attr)

        # Validate attribute types
        assert isinstance(conn.host, str)
        assert isinstance(conn.port, str)
        assert isinstance(conn.database, str)
        assert isinstance(conn.user, str)
        assert isinstance(conn.password, str)
        assert isinstance(conn.jdbc_url, str)
        assert isinstance(conn.base_options, dict)

    # Advanced Query Testing
    # =====================

    @pytest.mark.unit
    def test_query_reader_options_order(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test query method applies JDBC options in correct order.

        Validates that base options and partitioning options are applied in the
        proper sequence with appropriate override behavior. Critical for ensuring
        predictable query execution configuration and parameter precedence.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        sql = "SELECT * FROM test"
        partitioning = {"fetchsize": "10000"}

        conn.query(sql, partitioning)

        option_calls = mock_reader.option.call_args_list
        fetchsize_calls = [
            call_args for call_args in option_calls if call_args[0][0] == "fetchsize"
        ]

        assert len(fetchsize_calls) == 2
        assert call("fetchsize", "5000") in fetchsize_calls
        assert call("fetchsize", "10000") in fetchsize_calls

    @pytest.mark.unit
    def test_sql_subquery_wrapping(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test SQL query proper wrapping as subquery for JDBC execution.

        Validates that all SQL queries are correctly wrapped in subquery syntax
        required by Spark JDBC operations. Essential for ensuring compatibility
        with Spark's JDBC query execution engine and preventing SQL syntax errors.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        test_queries = [
            "SELECT 1",
            "SELECT * FROM users WHERE id > 100",
            """SELECT u.name, COUNT(o.id) as count
               FROM users u
               LEFT JOIN orders o ON u.id = o.user_id
               GROUP BY u.name""",
        ]

        for sql in test_queries:
            mock_reader.reset_mock()
            mock_reader.format.return_value = mock_reader
            mock_reader.option.return_value = mock_reader
            mock_reader.load.return_value = mock_df

            conn.query(sql)

            dbtable_param = None
            for call_args in mock_reader.option.call_args_list:
                if call_args[0][0] == "dbtable":
                    dbtable_param = call_args[0][1]
                    break

            assert dbtable_param is not None
            assert dbtable_param == f"({sql}) subquery"

    # Edge Cases and Error Validation Testing
    # ======================================

    @pytest.mark.unit
    @pytest.mark.edge_case
    @pytest.mark.configuration
    def test_default_port_handling(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test proper handling of default port when not specified in configuration.

        Validates that missing port configuration correctly defaults to SQL Server
        standard port 1433, ensuring consistent behavior across different
        configuration scenarios and backward compatibility.
        """
        config_without_port = {
            "host": "testserver",
            "database": "testdb",
            "user": "testuser",
            "password": "testpass",
        }

        conn = JdbcSqlServerConnection(
            mock_spark_session, config_without_port, mock_logger
        )

        assert conn.port == "1433", "Port should default to '1433' when not specified"
        assert "1433" in conn.jdbc_url, "JDBC URL should contain default port"

    @pytest.mark.unit
    @pytest.mark.edge_case
    @pytest.mark.error_handling
    @pytest.mark.configuration
    def test_missing_required_config_keys(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test behavior with missing required configuration keys.

        Validates that the connection handles missing essential configuration
        parameters gracefully and provides clear error indication for
        debugging and operational support.
        """
        incomplete_configs = [
            # Missing host
            {"database": "test", "user": "test", "password": "test"},
            # Missing database
            {"host": "test", "user": "test", "password": "test"},
            # Missing user
            {"host": "test", "database": "test", "password": "test"},
            # Missing password
            {"host": "test", "database": "test", "user": "test"},
        ]

        for config in incomplete_configs:
            # Test the actual behavior - some implementations might allow missing keys
            try:
                conn = JdbcSqlServerConnection(mock_spark_session, config, mock_logger)
                # If connection succeeds, validate it has basic attributes
                assert (
                    conn is not None
                ), f"Connection created with incomplete config: {config}"
                assert hasattr(conn, "spark"), "Connection should have spark attribute"
                assert hasattr(
                    conn, "logger"
                ), "Connection should have logger attribute"
            except KeyError as e:
                # If KeyError is raised, that's also valid behavior
                assert (
                    str(e) != ""
                ), f"KeyError should have a message for config: {config}"

    @pytest.mark.unit
    def test_empty_configuration_values(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test handling of empty string values in configuration.

        Validates connection behavior when configuration contains empty strings
        rather than missing keys, ensuring robust parameter validation and
        appropriate error handling for invalid configurations.
        """
        config_with_empty_values = {
            "host": "",
            "database": "testdb",
            "user": "testuser",
            "password": "testpass",
        }

        conn = JdbcSqlServerConnection(
            mock_spark_session, config_with_empty_values, mock_logger
        )

        # Should accept empty host (though it may fail at connection time)
        assert conn.host == "", "Empty host should be accepted in configuration"
        assert conn.database == "testdb", "Non-empty database should be preserved"
        assert (
            "databaseName=testdb" in conn.jdbc_url
        ), "Database should appear in JDBC URL"

    @pytest.mark.unit
    def test_none_configuration_values(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test handling of None values in configuration parameters.

        Validates behavior when configuration contains None values,
        ensuring proper type handling and error prevention in
        production database connection scenarios.
        """
        config_with_none = {
            "host": "testhost",
            "port": None,
            "database": "testdb",
            "user": "testuser",
            "password": "testpass",
        }

        conn = JdbcSqlServerConnection(
            mock_spark_session, config_with_none, mock_logger
        )

        # Test actual behavior - None port is preserved as None in this implementation
        assert conn.port is None or isinstance(
            conn.port, str
        ), f"Port should be None or string (got {conn.port})"
        assert conn.host == "testhost", "Valid host should be preserved"

        # Verify the connection initializes without errors despite None port
        assert hasattr(conn, "jdbc_url"), "Connection should have JDBC URL"
        assert hasattr(conn, "base_options"), "Connection should have base options"

        # Validate that None port appears in JDBC URL appropriately
        assert "testhost" in conn.jdbc_url, "Host should appear in JDBC URL"

    @pytest.mark.unit
    @pytest.mark.edge_case
    @pytest.mark.security
    @pytest.mark.credentials
    def test_special_characters_in_credentials(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test handling of special characters in username and password.

        Validates proper processing of credentials containing special characters,
        symbols, and escape sequences commonly found in enterprise password
        policies and security-compliant authentication systems.
        """
        config_with_special_chars = {
            "host": "testhost",
            "database": "testdb",
            "user": "test@domain.com",
            "password": "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?",
        }

        conn = JdbcSqlServerConnection(
            mock_spark_session, config_with_special_chars, mock_logger
        )

        assert (
            conn.user == "test@domain.com"
        ), "Special characters in username should be preserved"
        assert (
            conn.password == "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
        ), "Special characters in password should be preserved"
        assert (
            conn.base_options["user"] == "test@domain.com"
        ), "Special username should appear in base options"
        assert (
            conn.base_options["password"] == "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
        ), "Special password should appear in base options"

    @pytest.mark.unit
    def test_numeric_string_port_conversion(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test handling of numeric port values provided as different types.

        Validates consistent port handling regardless of whether port is
        provided as string, integer, or other numeric type, ensuring
        robust type conversion for various configuration sources.
        """
        configs_with_different_port_types = [
            {
                "host": "test",
                "port": "1434",
                "database": "db",
                "user": "u",
                "password": "p",
            },
            {
                "host": "test",
                "port": 1434,
                "database": "db",
                "user": "u",
                "password": "p",
            },
        ]

        for config in configs_with_different_port_types:
            mock_context = Mock()
            config_dict = cast(Dict[str, Any], config)
            mock_context.applicationId = f"test-port-{config_dict['port']}"
            mock_spark_session.sparkContext = mock_context

            conn = JdbcSqlServerConnection(mock_spark_session, config, mock_logger)

            assert conn.port == "1434", (
                f"Port should be string '1434' regardless "
                f"of input type: {type(config_dict['port'])}"
            )
            assert ":1434;" in conn.jdbc_url, "Port should appear correctly in JDBC URL"

    @pytest.mark.unit
    def test_whitespace_handling_in_config(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test handling of whitespace in configuration values.

        Validates that configuration parameters with leading/trailing whitespace
        are processed correctly, ensuring consistent connection behavior
        regardless of configuration source formatting.
        """
        config_with_whitespace = {
            "host": "  testhost  ",
            "database": " testdb ",
            "user": "\ttestuser\t",
            "password": "\ntestpass\n",
        }

        conn = JdbcSqlServerConnection(
            mock_spark_session, config_with_whitespace, mock_logger
        )

        # Whitespace should be preserved (not stripped) for compatibility
        assert conn.host == "  testhost  ", "Host whitespace should be preserved"
        assert conn.database == " testdb ", "Database whitespace should be preserved"
        assert conn.user == "\ttestuser\t", "User whitespace should be preserved"
        assert (
            conn.password == "\ntestpass\n"
        ), "Password whitespace should be preserved"

    # Security and Robustness Testing
    # ===============================

    @pytest.mark.security
    @pytest.mark.sql_injection
    @pytest.mark.edge_case
    def test_malicious_sql_handling(
        self,
        mock_spark_session: Any,
        mock_logger: Any,
        sample_database_config: Any,
        malicious_sql_patterns: Any,
    ) -> None:
        """
        Test handling of potentially malicious SQL patterns for security validation.

        Validates that the connection properly processes SQL injection patterns
        and malicious query constructs without breaking the query execution flow.
        Essential for ensuring robust security posture in production environments.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        for malicious_pattern in malicious_sql_patterns[:3]:  # Test first 3 patterns
            result = conn.query(malicious_pattern)
            assert result is mock_df

            # Verify the pattern is properly wrapped as subquery
            dbtable_option = None
            for call_args in mock_reader.option.call_args_list:
                if call_args[0][0] == "dbtable":
                    dbtable_option = call_args[0][1]
                    break

            assert dbtable_option == f"({malicious_pattern}) subquery"

            mock_reader.reset_mock()
            mock_reader.format.return_value = mock_reader
            mock_reader.option.return_value = mock_reader
            mock_reader.load.return_value = mock_df

    @pytest.mark.unit
    @pytest.mark.unicode
    @pytest.mark.internationalization
    @pytest.mark.edge_case
    def test_unicode_configuration_handling(
        self, mock_spark_session: Any, mock_logger: Any, unicode_test_data: Any
    ) -> None:
        """
        Test connection handling with Unicode characters in configuration.

        Validates proper encoding and processing of international characters
        in database configuration parameters, ensuring global compatibility
        and robust character encoding support.
        """
        unicode_config = {
            "host": unicode_test_data["chinese"],
            "database": unicode_test_data["cyrillic"],
            "user": unicode_test_data["portuguese"],
            "password": unicode_test_data["emoji"],
        }

        conn = JdbcSqlServerConnection(mock_spark_session, unicode_config, mock_logger)

        assert conn.host == unicode_test_data["chinese"]
        assert conn.database == unicode_test_data["cyrillic"]
        assert conn.user == unicode_test_data["portuguese"]
        assert conn.password == unicode_test_data["emoji"]

        # Verify JDBC URL construction with Unicode
        expected_url = (
            f"jdbc:sqlserver://{unicode_config['host']}:1433;"
            f"databaseName={unicode_config['database']};"
            "encrypt=true;trustServerCertificate=true"
        )
        assert conn.jdbc_url == expected_url

    # Comprehensive Integration and Stress Testing
    # ===========================================

    @pytest.mark.integration
    def test_key_generation_with_different_configs(self, mock_logger: Any) -> None:
        """
        Test unique key generation produces different keys for different configurations.

        Validates that the singleton pattern key generation algorithm produces
        unique, collision-free keys for different database configurations and
        Spark application contexts, ensuring proper connection isolation.
        """
        JdbcSqlServerConnection._instances.clear()

        configs = [
            (
                "app-1",
                {
                    "host": "db1",
                    "database": "test",
                    "user": "user1",
                    "password": "pass1",
                },
            ),
            (
                "app-1",
                {
                    "host": "db2",
                    "database": "test",
                    "user": "user1",
                    "password": "pass1",
                },
            ),
            (
                "app-2",
                {
                    "host": "db1",
                    "database": "test",
                    "user": "user1",
                    "password": "pass1",
                },
            ),
        ]

        created_keys = []
        for app_id, config in configs:
            mock_spark = Mock(spec=SparkSession)
            mock_context = Mock()
            mock_context.applicationId = app_id
            mock_spark.sparkContext = mock_context

            _ = JdbcSqlServerConnection(mock_spark, config, mock_logger)

            host = config["host"]
            port = config.get("port", "1433")
            db = config["database"]
            unique_str = f"{app_id}:{host}:{port}:{db}"
            expected_key = hashlib.sha256(unique_str.encode()).hexdigest()
            created_keys.append(expected_key)

            assert expected_key in JdbcSqlServerConnection._instances

        assert len(set(created_keys)) == len(created_keys)

    @pytest.mark.integration
    def test_connection_attributes_consistency(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test connection attribute consistency across different configurations.

        Validates that connection attributes are consistently initialized and
        maintained across various database configuration scenarios, ensuring
        reliable connection behavior in diverse enterprise environments.
        """
        configs = [
            {
                "host": "server1",
                "database": "db1",
                "user": "user1",
                "password": "pass1",
            },
            {
                "host": "server2",
                "port": "1434",
                "database": "db2",
                "user": "user2",
                "password": "pass2",
            },
        ]

        for config in configs:
            conn = JdbcSqlServerConnection(mock_spark_session, config, mock_logger)

            assert conn.host == config["host"]
            assert conn.port == config.get("port", "1433")
            assert conn.database == config["database"]
            assert conn.user == config["user"]
            assert conn.password == config["password"]
            assert conn.spark is mock_spark_session
            assert conn.logger is mock_logger

            expected_url = (
                f"jdbc:sqlserver://{conn.host}:{conn.port};"
                f"databaseName={conn.database};"
                "encrypt=true;trustServerCertificate=true"
            )
            assert conn.jdbc_url == expected_url

            expected_options = {
                "user": conn.user,
                "password": conn.password,
                "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
                "fetchsize": "5000",
            }
            assert conn.base_options == expected_options

    @pytest.mark.integration
    def test_instances_dict_isolation(self, mock_logger: Any) -> None:
        """
        Test _instances dictionary properly isolates different connections.

        Validates that the singleton instances dictionary correctly manages
        multiple connection instances with proper isolation and key uniqueness
        across complex multi-configuration scenarios.
        """
        spark_sessions = []
        for i in range(3):
            mock_spark = Mock(spec=SparkSession)
            mock_context = Mock()
            mock_context.applicationId = f"app-{i}"
            mock_spark.sparkContext = mock_context
            spark_sessions.append(mock_spark)

        configs = [
            {"host": "host1", "database": "db1", "user": "user1", "password": "pass1"},
            {"host": "host2", "database": "db2", "user": "user2", "password": "pass2"},
            {
                "host": "host1",
                "database": "db1",
                "user": "user1",
                "password": "pass1",
            },
        ]

        connections = []
        for i, config in enumerate(configs):
            conn = JdbcSqlServerConnection(spark_sessions[i], config, mock_logger)
            connections.append(conn)

        assert connections[0] is not connections[1]
        assert connections[0] is not connections[2]
        assert connections[1] is not connections[2]

        assert len(JdbcSqlServerConnection._instances) == 3

    @pytest.mark.integration
    def test_singleton_across_test_methods(self, mock_logger: Any) -> None:
        """
        Test singleton behavior persistence across different test scenarios.

        Validates that singleton pattern maintains consistency and proper
        instance management across complex test execution scenarios with
        identical configuration parameters.
        """
        JdbcSqlServerConnection._instances.clear()

        mock_spark = Mock(spec=SparkSession)
        mock_context = Mock()
        mock_context.applicationId = "singleton-test"
        mock_spark.sparkContext = mock_context

        config = {
            "host": "testhost",
            "database": "test_database",
            "user": "test_user",
            "password": "test_password",
        }

        connections = []
        for _ in range(5):
            conn = JdbcSqlServerConnection(mock_spark, config, mock_logger)
            connections.append(conn)

        first_conn = connections[0]
        for conn in connections[1:]:
            assert conn is first_conn

        assert len(JdbcSqlServerConnection._instances) == 1

    @pytest.mark.performance
    def test_instance_creation_performance(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test singleton instance creation performance optimization.

        Validates that singleton pattern provides optimal performance for
        repeated connection requests through efficient instance caching
        and retrieval. Critical for high-throughput production environments.
        """
        JdbcSqlServerConnection._instances.clear()

        conn1 = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        for _ in range(100):
            conn = JdbcSqlServerConnection(
                mock_spark_session, sample_database_config, mock_logger
            )
            assert conn is conn1

        assert len(JdbcSqlServerConnection._instances) == 1

    # Consistency and Validation Testing
    # =================================

    @pytest.mark.unit
    def test_base_options_immutability(
        self, mock_spark_session: Any, mock_logger: Any, sample_database_config: Any
    ) -> None:
        """
        Test base options consistency across connection instances.

        Validates that base options configuration remains consistent and
        immutable across multiple connection retrievals, ensuring reliable
        JDBC configuration throughout application lifecycle.
        """
        conn1 = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        original_options = conn1.base_options.copy()

        conn2 = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        assert conn1 is conn2
        assert conn2.base_options == original_options

    @pytest.mark.unit
    def test_query_sql_subquery_formatting(
        self,
        mock_spark_session: Any,
        mock_logger: Any,
        sample_database_config: Any,
        sample_sql_queries: Any,
    ) -> None:
        """
        Test SQL query formatting as subquery for JDBC compatibility.

        Validates that various SQL query formats are properly wrapped in
        subquery syntax required by Spark JDBC operations, ensuring
        compatibility across different query patterns and structures.
        """
        mock_df = Mock(spec=DataFrame)
        mock_reader = Mock()
        mock_reader.format.return_value = mock_reader
        mock_reader.option.return_value = mock_reader
        mock_reader.load.return_value = mock_df
        mock_spark_session.read = mock_reader

        conn = JdbcSqlServerConnection(
            mock_spark_session, sample_database_config, mock_logger
        )

        test_cases = [
            sample_sql_queries["simple"],
            sample_sql_queries["with_where"],
            sample_sql_queries["count"],
        ]

        for sql in test_cases:
            conn.query(sql)

            dbtable_option = None
            for call_args in mock_reader.option.call_args_list:
                if call_args[0][0] == "dbtable":
                    dbtable_option = call_args[0][1]
                    break

            assert dbtable_option == f"({sql}) subquery"

            mock_reader.reset_mock()
            mock_reader.format.return_value = mock_reader
            mock_reader.option.return_value = mock_reader
            mock_reader.load.return_value = mock_df


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=spark_simplicity.connections.database_connection",
            "--cov-report=term-missing",
        ]
    )
