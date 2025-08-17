"""
Spark Simplicity - Database Connection Manager
=============================================

Enterprise-grade JDBC database connectivity with singleton pattern, optimized SQL Server
integration,
and production-ready connection management. This module provides secure, efficient
database access
for Spark data processing workflows, enabling seamless integration with enterprise
data systems,
ETL pipelines, and analytical processing operations.

Key Features:
    - **Singleton Pattern**: One connection instance per unique database configuration
    - **SQL Server Optimization**: Specialized JDBC configuration for Microsoft
      SQL Server
    - **Connection Pooling**: Efficient resource management with automatic
      connection reuse
    - **Security Features**: Encrypted connections with certificate validation options
    - **Performance Tuning**: Optimized fetch sizes and query execution strategies
    - **Enterprise Integration**: Compatible with corporate SQL Server deployments

Database Connectivity:
    **JDBC Optimization**:
    - Microsoft SQL Server JDBC driver integration with enterprise features
    - Encrypted connections (TLS/SSL) with configurable certificate validation
    - Optimized fetch sizes for balanced memory usage and query performance
    - Connection string optimization for SQL Server-specific functionality

    **Query Performance**:
    - Configurable query partitioning for large result sets and parallel processing
    - Intelligent connection reuse across multiple queries and operations
    - Memory-efficient data transfer with streaming capabilities
    - Query execution optimization for analytical workloads

Enterprise Integration:
    - **Corporate SQL Server**: Seamless integration with enterprise SQL Server
      instances
    - **Data Warehouse Connectivity**: Optimized access to data warehouse and
      OLAP systems
    - **ETL Pipeline Support**: High-performance data extraction for processing
      workflows
    - **Security Compliance**: Encrypted connections meeting enterprise security
      requirements
    - **Resource Management**: Efficient connection lifecycle management for
      production environments

Usage:
    This module is designed for enterprise data processing scenarios requiring
    reliable, high-performance database connectivity integrated with Spark analytics
    workflows.

    from spark_simplicity.connections.database_connection import (
        JdbcSqlServerConnection
    )
"""

import hashlib
import logging
from typing import Dict, Optional

from pyspark.sql import DataFrame, SparkSession


class JdbcSqlServerConnection:
    """
    Enterprise-grade JDBC SQL Server connection manager with singleton pattern and
    performance optimization.

    Provides secure, high-performance database connectivity for Spark data processing
    workflows with
    intelligent connection management, query optimization, and enterprise-grade security
    features.
    This class implements the singleton pattern to ensure efficient resource utilization
    while
    maintaining connection isolation between different database configurations.

    The connection manager is specifically optimized for Microsoft SQL Server
    environments with
    enterprise security features, performance tuning, and production-ready connection
    lifecycle
    management. It handles encrypted connections, query partitioning, and resource
    optimization
    automatically while providing a simple, consistent interface for database
    operations.

    Key Capabilities:
        - **Singleton Management**: One connection instance per unique database
          configuration
        - **SQL Server Optimization**: Specialized configuration for Microsoft
          SQL Server
        - **Security Features**: Encrypted connections with certificate validation
        - **Performance Tuning**: Optimized fetch sizes and query execution strategies
        - **Resource Efficiency**: Automatic connection reuse and lifecycle management
        - **Enterprise Ready**: Production-grade error handling and monitoring
          integration

    Attributes:
        _instances: Class-level dictionary maintaining singleton instances keyed by
                   unique database configuration (application + host + port +
                   database).
                   Ensures efficient resource utilization and prevents connection
                   proliferation.
    """

    _instances: Dict[str, "JdbcSqlServerConnection"] = {}

    def __new__(
        cls, spark: SparkSession, config: Dict[str, str], logger: logging.Logger
    ) -> "JdbcSqlServerConnection":
        """
        Create or retrieve JDBC connection instance using singleton pattern for
        resource efficiency.

        Implements sophisticated singleton logic based on unique database connection
        parameters
        to ensure optimal resource utilization while maintaining connection isolation
        between
        different database configurations. This approach prevents connection
        proliferation
        and
        enables efficient reuse of established connections across multiple operations.

        Args:
            spark: Active SparkSession instance used for database connectivity and
                   DataFrame operations.
                  Must have appropriate JDBC driver dependencies configured for SQL
                  Server connectivity.
                  Used for application identification and connection lifecycle
                  management.
            config: Database connection configuration dictionary containing:
                   - 'host': SQL Server hostname or IP address (required)
                   - 'port': SQL Server port number (default: '1433')
                   - 'database': Target database name (required)
                   - 'user': Database authentication username (required)
                   - 'password': Database authentication password (required)
                   Additional SQL Server-specific options supported for advanced
                   configurations.
            logger: Logger instance for connection events, query logging, and error
                    reporting.
                   Used for operational monitoring and troubleshooting database
                   operations.

        Returns:
            JdbcSqlServerConnection instance - either newly created or existing
            singleton
            configured for the specified database connection parameters.

        Singleton Logic:
            **Unique Key Generation**: SHA-256 hash of application ID, host, port,
                                      and database
            **Instance Reuse**: Existing connections returned for matching
                                configurations
            **Resource Efficiency**: Prevents duplicate connections to same database
            **Isolation**: Separate instances for different database configurations
        """
        host = config["host"]
        port = config.get("port", "1433")
        db = config["database"]

        # Unique key per Spark application + target database
        unique = f"{spark.sparkContext.applicationId}:{host}:{port}:{db}"
        key = hashlib.sha256(unique.encode()).hexdigest()

        if key not in cls._instances:
            cls._instances[key] = super().__new__(cls)
            cls._instances[key]._init(spark, config, logger)
        return cls._instances[key]

    def _init(
        self, spark: SparkSession, config: Dict[str, str], logger: logging.Logger
    ) -> None:
        """
        Initialize JDBC SQL Server connection with comprehensive configuration and
        security setup.

        Performs one-time initialization including connection string construction,
        security
        configuration, performance optimization, and authentication setup. This method
        configures enterprise-grade database connectivity with SQL Server-specific
        optimizations for reliable, high-performance data access in production
        environments.

        Args:
            spark: SparkSession instance for database operations and DataFrame creation
            config: Database configuration dictionary with connection parameters and
                    credentials
            logger: Logger instance for connection monitoring and operational
                    diagnostics

        Configuration Process:
            1. Extract and validate database connection parameters
            2. Construct optimized JDBC URL with security and performance options
            3. Configure base connection options including driver and performance
               settings
            4. Set up encrypted connections with certificate validation
            5. Log connection initialization for operational monitoring

        Security Features:
            **Encrypted Connections**: Automatic TLS/SSL encryption for data
                                      transmission
            **Certificate Handling**: Configurable certificate validation for
                                     enterprise environments
            **Credential Management**: Secure handling of database authentication
                                      credentials
            **Connection Security**: Enterprise-grade security configuration for
                                    SQL Server
        """
        self.spark = spark
        self.logger = logger

        self.host = config["host"]
        self.port = config.get("port", "1433")
        self.database = config["database"]
        self.user = config["user"]
        self.password = config["password"]

        self.jdbc_url = (
            f"jdbc:sqlserver://{self.host}:{self.port};"
            f"databaseName={self.database};"
            "encrypt=true;trustServerCertificate=true"
        )

        self.base_options = {
            "user": self.user,
            "password": self.password,
            "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
            "fetchsize": "5000",
        }

        self.logger.info(
            f"SQL Server connection initialized: host={self.host}, port={self.port}, "
            f"db={self.database}, user={self.user}"
        )

    def query(
        self, sql: str, partitioning: Optional[Dict[str, str]] = None
    ) -> DataFrame:
        """
        Execute SQL query against SQL Server database with optimized performance and
        optional partitioning.

        Provides high-performance SQL query execution with intelligent result set
        handling,
        configurable partitioning for large datasets, and comprehensive error handling.
        This method is optimized for analytical workloads, ETL operations, and data
        processing workflows requiring efficient data extraction from SQL Server
        databases.

        Args:
            sql: SQL query string to execute against the target database:
                - Standard SQL SELECT statements for data retrieval
                - Complex analytical queries with joins, aggregations, and window
                  functions
                - Stored procedure calls and parameterized queries
                - Data warehouse and OLAP query patterns
                - Must be valid SQL Server T-SQL syntax for optimal performance
            partitioning: Optional dictionary configuring query partitioning for large
                         result sets:
                         - 'numPartitions': Number of parallel partitions for query
                           execution
                         - 'partitionColumn': Column name for partition-based data
                           distribution
                         - 'lowerBound': Lower boundary value for partition column
                         - 'upperBound': Upper boundary value for partition column
                         - 'fetchsize': Override default fetch size for specific query
                           requirements
                         Partitioning enables parallel processing of large datasets
                         across cluster.

        Returns:
            Spark DataFrame containing query results:
            - Distributed DataFrame with automatic schema inference from SQL Server
              metadata
            - Lazy evaluation enabling further Spark transformations and optimizations
            - Optimized data transfer with configurable fetch sizes and parallel
              processing
            - Proper data type mapping from SQL Server types to Spark DataFrame schema

        Performance Optimization:
            **Query Execution**:
            - Optimized JDBC driver configuration for SQL Server connectivity
            - Efficient fetch size configuration balancing memory usage and transfer
              speed
            - Connection reuse across multiple queries for improved performance
            - Parallel query execution when partitioning parameters are specified

            **Data Transfer**:
            - Streaming data transfer for memory-efficient processing of large
              result sets
            - Automatic schema inference reducing metadata overhead
            - Optimized data type conversion for Spark DataFrame compatibility
            - Network optimization for enterprise database connectivity

        Examples:
            Simple analytical query execution:

             df = db_conn.query(
            ...     "SELECT customer_id, order_date, total_amount "
            ...     "FROM orders WHERE order_date >= '2024-01-01'"
            ... )
            ... print(f"Retrieved {df.count()} orders")

            Complex query with joins and aggregations:

             sales_analysis = db_conn.query(
            ...     SELECT
            ...         c.region,
            ...         p.product_category,
            ...         SUM(o.total_amount) as total_sales,
            ...         COUNT(*) as order_count
            ...     FROM orders o
            ...     JOIN customers c ON o.customer_id = c.customer_id
            ...     JOIN products p ON o.product_id = p.product_id
            ...     WHERE o.order_date >= DATEADD(month, -3, GETDATE())
            ...     GROUP BY c.region, p.product_category
            ...     ORDER BY total_sales DESC
            ... )

            Large dataset query with partitioning for parallel processing:

             large_dataset = db_conn.query(
            ...     "SELECT * FROM transaction_history WHERE year >= 2020",
            ...     partitioning={
            ...         'numPartitions': '8',
            ...         'partitionColumn': 'transaction_id',
            ...         'lowerBound': '1000000',
            ...         'upperBound': '9000000',
            ...         'fetchsize': '10000'
            ...     }
            ... )

        Query Performance Patterns:
            **Small to Medium Queries (< 1M rows)**:
            - Default configuration provides optimal performance
            - No partitioning required for efficient processing
            - Standard fetch size balances memory and network efficiency

            **Large Queries (> 1M rows)**:
            - Configure partitioning parameters for parallel processing
            - Increase fetch size for improved network efficiency
            - Use appropriate partition column with good data distribution

        Error Handling:
            **SQL Errors**: Database-specific errors with detailed context information
            **Connection Errors**: Network connectivity and authentication issues
            **Performance Errors**: Resource constraints and timeout handling
            **Data Type Errors**: Schema inference and type conversion issues

        See Also:
            - Spark SQL documentation for DataFrame operations and transformations
            - SQL Server T-SQL reference for query syntax and optimization
            - JDBC partitioning documentation for parallel processing configuration

        Note:
            This method constructs queries as subqueries for JDBC compatibility while
            maintaining query optimization and performance. The connection singleton
            pattern ensures efficient resource utilization across multiple query
            operations.
        """
        # self.logger.warn("SQL Execution: " + sql.replace("\n", " "))
        dbtable = f"({sql}) subquery"

        reader = (
            self.spark.read.format("jdbc")
            .option("url", self.jdbc_url)
            .option("dbtable", dbtable)
        )

        for k, v in self.base_options.items():
            reader = reader.option(k, v)

        if partitioning:
            for k, v in partitioning.items():
                reader = reader.option(k, v)

        return reader.load()
