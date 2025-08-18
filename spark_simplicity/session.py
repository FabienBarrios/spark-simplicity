"""
Spark Simplicity - Session Management
=====================================

Optimized Spark session management with production-ready configurations.
This module provides easy session creation with environment-specific optimizations.

Key Features:
    - Environment-specific configurations (development, production, testing)
    - Automatic resource optimization based on available hardware
    - Built-in performance tuning for common use cases
    - Easy configuration override and customization
    - Comprehensive logging and monitoring setup

Usage:
    from spark_simplicity import get_spark_session
    spark = get_spark_session("my_application")
    spark = get_spark_session("my_app", environment="production")
"""

import os
import platform
from enum import Enum
from typing import Any, Dict, Optional, Union

from pyspark.sql import SparkSession

# Import du logger spécialisé
from .logger import get_logger

# Logger spécialisé pour la gestion des sessions
_session_logger = get_logger("spark_simplicity.session")

# Configuration constants
CONF_SERIALIZER = "spark.serializer"
CONF_ARROW_ENABLED = "spark.sql.execution.arrow.pyspark.enabled"
CONF_CONSOLE_PROGRESS = "spark.ui.showConsoleProgress"
CONF_WAREHOUSE_DIR = "spark.sql.warehouse.dir"
CONF_CATALOG_IMPL = "spark.sql.catalogImplementation"
CONF_EXECUTOR_MEMORY = "spark.executor.memory"
CONF_EXECUTOR_CORES = "spark.executor.cores"
CONF_EXECUTOR_INSTANCES = "spark.executor.instances"
CONF_DRIVER_MEMORY = "spark.driver.memory"
CONF_ADVISORY_PARTITION_SIZE = "spark.sql.adaptive.advisoryPartitionSizeInBytes"
CONF_SHUFFLE_PARTITIONS = "spark.sql.shuffle.partitions"
NOT_SET = "not set"


def get_simple_spark_session(app_name: str) -> SparkSession:
    """
    Create a simple Spark session without predefined configurations.
    Perfect for Airflow DAGs where configuration is managed externally.

    Args:
        app_name: Name for the Spark application

    Returns:
        SparkSession instance

    Example:
         # For Airflow DAGs - simple and clean
         spark = get_simple_spark_session("my_etl_dag")

         # Configuration handled in Airflow connection or DAG
         # spark.conf.set("spark.executor.memory", "4g")  # Set in DAG if needed
    """
    return SparkSession.builder.appName(app_name).getOrCreate()


class Environment(Enum):
    """Enumeration of supported deployment environments."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TESTING = "testing"
    LOCAL = "local"


class SparkConfig:
    """
    Predefined Spark configurations for different environments and use cases.

    This class contains optimized configuration sets for various scenarios,
    from local development to production clusters.
    """

    @staticmethod
    def get_base_config() -> Dict[str, str]:
        """
        Get base configuration applicable to all environments.

        Returns:
            Dictionary of base Spark configuration options
        """
        config = {
            # Serialization optimization
            CONF_SERIALIZER: "org.apache.spark.serializer.KryoSerializer",
            "spark.sql.adaptive.enabled": "true",
            "spark.sql.adaptive.coalescePartitions.enabled": "true",
            # Memory management
            CONF_ARROW_ENABLED: "true",
            "spark.sql.execution.arrow.pyspark.fallback.enabled": "true",
            # Dynamic allocation
            "spark.dynamicAllocation.enabled": "true",
            "spark.dynamicAllocation.minExecutors": "1",
            "spark.dynamicAllocation.maxExecutors": "10",
            # Optimization
            "spark.sql.adaptive.skewJoin.enabled": "true",
            "spark.sql.adaptive.localShuffleReader.enabled": "true",
            # UI and monitoring
            CONF_CONSOLE_PROGRESS: "true",
        }

        # Windows-specific configurations
        if platform.system() == "Windows":
            config.update(
                {
                    # Disable Hadoop native library warnings on Windows
                    CONF_WAREHOUSE_DIR: "file:///tmp/spark-warehouse",
                    "spark.hadoop.fs.defaultFS": "file:///",
                    # Reduce Hadoop-related operations that cause issues on Windows
                    CONF_CATALOG_IMPL: "in-memory",
                    # File system configurations for Windows
                    CONF_ARROW_ENABLED: "false",  # Disable Arrow on Windows
                    # Reduce verbosity of Hadoop warnings
                    "spark.hadoop.io.native.lib.available": "false",
                }
            )

        return config

    @staticmethod
    def get_windows_safe_config() -> Dict[str, str]:
        """
        Get Windows-specific configuration to avoid Hadoop issues.

        Returns:
            Dictionary of Windows-safe Spark configuration options
        """
        config = {
            # Hadoop workarounds for Windows
            CONF_WAREHOUSE_DIR: "file:///tmp/spark-warehouse",
            "spark.hadoop.fs.defaultFS": "file:///",
            CONF_CATALOG_IMPL: "in-memory",
            # Disable problematic features on Windows
            CONF_ARROW_ENABLED: "false",
            "spark.hadoop.io.native.lib.available": "false",
            # Reduce file system operations that require winutils
            "spark.sql.hive.convertMetastoreParquet": "false",
            "spark.sql.hive.convertMetastoreOrc": "false",
            # Reduce logging verbosity for Hadoop warnings
            "spark.hadoop.fs.file.impl.disable.cache": "true",
        }

        # Python version compatibility for Windows
        try:
            import os
            import sys

            python_executable = sys.executable

            # Set both Spark config and environment variables to ensure consistency
            config.update(
                {
                    "spark.pyspark.python": python_executable,
                    "spark.pyspark.driver.python": python_executable,
                }
            )

            # Also set environment variables directly (this is critical for Windows)
            os.environ["PYSPARK_PYTHON"] = python_executable
            os.environ["PYSPARK_DRIVER_PYTHON"] = python_executable

        except (OSError, AttributeError, ImportError) as e:
            _session_logger.warning(
                f"Could not configure Python executable for Spark: {e}"
            )
            # Continue without Python executable configuration

        return config

    @staticmethod
    def get_development_config() -> Dict[str, str]:
        """
        Get configuration optimized for local development.

        Returns:
            Dictionary of development-specific Spark configuration
        """
        config = SparkConfig.get_base_config()
        config.update(
            {
                # Resource allocation for development
                CONF_EXECUTOR_MEMORY: "2g",
                CONF_EXECUTOR_CORES: "2",
                CONF_EXECUTOR_INSTANCES: "2",
                CONF_DRIVER_MEMORY: "1g",
                # Development-friendly settings
                "spark.sql.execution.arrow.maxRecordsPerBatch": "1000",
                CONF_ADVISORY_PARTITION_SIZE: "64MB",
                # Logging
                "spark.sql.adaptive.logLevel": "INFO",
            }
        )
        return config

    @staticmethod
    def get_production_config() -> Dict[str, str]:
        """
        Get configuration optimized for production clusters.

        Returns:
            Dictionary of production-specific Spark configuration
        """
        config = SparkConfig.get_base_config()
        config.update(
            {
                # Production resource allocation
                CONF_EXECUTOR_MEMORY: "8g",
                CONF_EXECUTOR_CORES: "4",
                CONF_EXECUTOR_INSTANCES: "4",
                CONF_DRIVER_MEMORY: "4g",
                "spark.driver.maxResultSize": "2g",
                # Performance optimization
                CONF_ADVISORY_PARTITION_SIZE: "128MB",
                "spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold": "128MB",
                # Memory tuning
                "spark.executor.memoryFraction": "0.8",
                "spark.storage.memoryFraction": "0.5",
                # Network optimization
                "spark.network.timeout": "600s",
                "spark.executor.heartbeatInterval": "30s",
                # Shuffle optimization
                CONF_SHUFFLE_PARTITIONS: "400",
                "spark.shuffle.compress": "true",
                # Checkpointing
                "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes": "256MB",
            }
        )
        return config

    @staticmethod
    def get_testing_config() -> Dict[str, str]:
        """
        Get configuration optimized for automated testing.

        Returns:
            Dictionary of testing-specific Spark configuration
        """
        config = SparkConfig.get_base_config()
        config.update(
            {
                # Minimal resource allocation for tests
                CONF_EXECUTOR_MEMORY: "512m",
                CONF_EXECUTOR_CORES: "1",
                CONF_EXECUTOR_INSTANCES: "1",
                CONF_DRIVER_MEMORY: "512m",
                # Fast execution for tests
                CONF_SHUFFLE_PARTITIONS: "4",
                CONF_ADVISORY_PARTITION_SIZE: "8MB",
                # Disable UI for tests
                "spark.ui.enabled": "false",
                CONF_CONSOLE_PROGRESS: "false",
                # Testing-friendly settings
                "spark.sql.execution.arrow.maxRecordsPerBatch": "100",
            }
        )
        return config

    @staticmethod
    def get_local_config() -> Dict[str, str]:
        """
        Get configuration for local single-machine execution.

        Returns:
            Dictionary of local execution Spark configuration
        """
        # Auto-detect system resources
        cpu_count = os.cpu_count() or 2

        config = SparkConfig.get_base_config()
        config.update(
            {
                # Use available system resources efficiently
                "spark.master": "local[*]",
                CONF_EXECUTOR_MEMORY: "1g",
                CONF_DRIVER_MEMORY: "1g",
                # Optimize for single machine
                CONF_SHUFFLE_PARTITIONS: str(cpu_count * 2),
                CONF_ADVISORY_PARTITION_SIZE: "32MB",
                # Local-friendly settings
                "spark.ui.port": "4040",
                "spark.serializer.objectStreamReset": "100",
            }
        )
        return config


def _get_config_for_environment(environment: Environment) -> Dict[str, str]:
    """Get configuration for the specified environment."""
    config_map = {
        Environment.DEVELOPMENT: SparkConfig.get_development_config,
        Environment.PRODUCTION: SparkConfig.get_production_config,
        Environment.TESTING: SparkConfig.get_testing_config,
        Environment.LOCAL: SparkConfig.get_local_config,
    }
    return config_map[environment]()


def _configure_builder(
    builder: SparkSession.Builder,
    base_config: Dict[str, str],
    master: Optional[str],
    environment: Environment,
    enable_hive_support: bool,
    checkpoint_dir: Optional[str],
    warehouse_dir: Optional[str],
) -> SparkSession.Builder:
    """Configure SparkSession builder with all options."""
    # Set master if provided
    if master:
        builder = builder.master(master)
    elif environment == Environment.LOCAL and "spark.master" not in base_config:
        builder = builder.master("local[*]")

    # Apply all configuration options
    for key, value in base_config.items():
        builder = builder.config(key, value)

    # Enable Hive support if requested
    if enable_hive_support:
        builder = builder.enableHiveSupport()

    # Set checkpoint directory
    if checkpoint_dir:
        builder = builder.config(
            "spark.sql.streaming.checkpointLocation", checkpoint_dir
        )

    # Set warehouse directory
    if warehouse_dir:
        builder = builder.config("spark.sql.warehouse.dir", warehouse_dir)

    return builder


def _log_session_creation(
    spark: SparkSession,
    app_name: str,
    environment: Environment,
    base_config: Dict[str, str],
) -> None:
    """Log session creation details with Windows-safe fallback."""
    try:
        _session_logger.info("Spark session created: %s", app_name)
        _session_logger.info("   Environment: %s", environment.value)
        _session_logger.info("   Spark Version: %s", spark.version)
        _session_logger.info("   Master: %s", spark.sparkContext.master)

        # Log resource allocation
        executor_memory = base_config.get(CONF_EXECUTOR_MEMORY, "default")
        executor_cores = base_config.get(CONF_EXECUTOR_CORES, "default")
        _session_logger.info(
            "   Executor Config: %s memory, %s cores", executor_memory, executor_cores
        )
    except UnicodeEncodeError:
        # Fallback for Windows console encoding issues
        _session_logger.info("Spark session created: %s", app_name)
        _session_logger.info("Environment: %s", environment.value)
        _session_logger.info("Spark Version: %s", spark.version)


def get_spark_session(
    app_name: str,
    environment: Union[str, Environment] = Environment.LOCAL,
    master: Optional[str] = None,
    config_overrides: Optional[Dict[str, str]] = None,
    enable_hive_support: bool = False,
    checkpoint_dir: Optional[str] = None,
    warehouse_dir: Optional[str] = None,
) -> SparkSession:
    """
    Create an optimized Spark session with environment-specific configurations.

    This function creates a Spark session with predefined configurations optimized
    for the specified environment, while allowing for custom overrides.

    Args:
        app_name: Name of the Spark application
        environment: Deployment environment (development, production, testing, local)
        master: Spark master URL (overrides environment default)
        config_overrides: Additional configuration options to override defaults
        enable_hive_support: Whether to enable Hive support
        checkpoint_dir: Directory for Spark checkpointing
        warehouse_dir: Hive warehouse directory

    Returns:
        Configured SparkSession instance

    Raises:
        ValueError: If environment is not supported
        RuntimeError: If session creation fails

    Example:
         # Simple local session
         spark = get_spark_session("my_app")

         # Production session with overrides
         spark = get_spark_session(
        ...     "production_app",
        ...     environment="production",
        ...     config_overrides={"spark.executor.memory": "16g"}
        ... )

         # Testing session
         spark = get_spark_session("test_app", environment="testing")
    """
    # Convert string to Environment enum if needed
    if isinstance(environment, str):
        try:
            environment = Environment(environment.lower())
        except ValueError:
            valid_envs = [e.value for e in Environment]
            raise ValueError(
                f"Invalid environment '{environment}'. Valid options: {valid_envs}"
            )

    # Get environment-specific configuration
    base_config = _get_config_for_environment(environment)

    # Apply Windows-specific configurations automatically
    if platform.system() == "Windows":
        windows_config = SparkConfig.get_windows_safe_config()
        base_config.update(windows_config)

    # Apply custom overrides (these take precedence over Windows configs)
    if config_overrides:
        base_config.update(config_overrides)

    try:
        # Create and configure SparkSession builder
        builder = SparkSession.builder.appName(app_name)
        builder = _configure_builder(
            builder,
            base_config,
            master,
            environment,
            enable_hive_support,
            checkpoint_dir,
            warehouse_dir,
        )

        # Create or get existing session
        spark = builder.getOrCreate()

        # Set checkpoint directory on SparkContext if provided
        if checkpoint_dir:
            spark.sparkContext.setCheckpointDir(checkpoint_dir)

        # Log session creation
        _log_session_creation(spark, app_name, environment, base_config)

        return spark

    except Exception as e:
        raise RuntimeError(
            f"Failed to create Spark session '{app_name}': {str(e)}"
        ) from e


def get_or_create_spark_session(
    app_name: str,
    environment: Union[str, Environment] = Environment.LOCAL,
    **kwargs: Any,
) -> SparkSession:
    """
    Get existing Spark session or create new one if none exists.

    This is a convenience function that wraps get_spark_session() but first
    tries to get any existing active session.

    Args:
        app_name: Name of the Spark application
        environment: Deployment environment
        **kwargs: Additional arguments passed to get_spark_session()

    Returns:
        SparkSession instance (existing or newly created)

    Example:
         spark = get_or_create_spark_session("my_app")
         # Later in the same application...
         spark = get_or_create_spark_session("my_app")  # Returns existing session
    """
    try:
        # Try to get existing active session
        existing_session = SparkSession.getActiveSession()
        if existing_session:
            _session_logger.info(
                "Using existing Spark session: %s",
                existing_session.sparkContext.appName,
            )
            return existing_session
    except (AttributeError, RuntimeError) as e:
        _session_logger.debug(f"No active Spark session found: {e}")
        # No active session found, create new one

    # Create new session
    return get_spark_session(app_name, environment, **kwargs)


def stop_spark_session(spark: Optional[SparkSession] = None) -> None:
    """
    Stop Spark session and clean up resources.

    Args:
        spark: SparkSession to stop (if None, stops active session)

    Example:
         stop_spark_session(spark)
         stop_spark_session()  # Stops active session
    """
    try:
        if spark is None:
            spark = SparkSession.getActiveSession()

        if spark:
            app_name = spark.sparkContext.appName
            spark.stop()
            _session_logger.info("Spark session stopped: %s", app_name)
        else:
            _session_logger.warning("No active Spark session to stop")

    except Exception as e:
        _session_logger.error("Error stopping Spark session: %s", str(e))


def configure_logging(
    spark: SparkSession, log_level: str = "INFO", enable_console_progress: bool = True
) -> None:
    """
    Configure Spark logging and progress reporting.

    Args:
        spark: SparkSession to configure
        log_level: Logging level (DEBUG, INFO, WARN, ERROR)
        enable_console_progress: Whether to show progress bars in console

    Example:
         configure_logging(spark, log_level="WARN")
         configure_logging(spark, log_level="DEBUG", enable_console_progress=False)
    """
    valid_levels = ["ALL", "DEBUG", "INFO", "WARN", "ERROR", "FATAL", "OFF"]
    if log_level.upper() not in valid_levels:
        raise ValueError(
            f"Invalid log level '{log_level}'. Valid levels: {valid_levels}"
        )

    try:
        # Set Spark log level
        spark.sparkContext.setLogLevel(log_level.upper())

        # Configure progress display
        spark.conf.set(CONF_CONSOLE_PROGRESS, str(enable_console_progress).lower())

        _session_logger.debug(
            "Logging configured: level=%s, console_progress=%s",
            log_level,
            enable_console_progress,
        )

    except Exception as e:
        _session_logger.error("Error configuring logging: %s", str(e))


def get_session_info(spark: SparkSession) -> Dict[str, Any]:
    """
    Get comprehensive information about the current Spark session.

    Args:
        spark: SparkSession to inspect

    Returns:
        Dictionary containing session information

    Example:
         info = get_session_info(spark)
         info['spark_version']  # Returns Spark version
         info['executor_count']  # Returns executor count
    """
    try:
        sc = spark.sparkContext

        info = {
            "app_name": sc.appName,
            "app_id": sc.applicationId,
            "spark_version": spark.version,
            "master": sc.master,
            "deploy_mode": getattr(sc, "deployMode", "unknown"),
            "executor_count": len(
                getattr(sc.statusTracker(), "getExecutorInfos", lambda: [])()
            )
            - 1,  # Exclude driver
            "default_parallelism": sc.defaultParallelism,
            "python_version": platform.python_version(),
            "java_version": sc.environment.get("java.version", "unknown"),
        }

        # Get key configuration settings
        key_configs = {
            CONF_EXECUTOR_MEMORY: spark.conf.get(CONF_EXECUTOR_MEMORY, NOT_SET),
            CONF_EXECUTOR_CORES: spark.conf.get(CONF_EXECUTOR_CORES, NOT_SET),
            CONF_DRIVER_MEMORY: spark.conf.get(CONF_DRIVER_MEMORY, NOT_SET),
            CONF_SHUFFLE_PARTITIONS: spark.conf.get(CONF_SHUFFLE_PARTITIONS, NOT_SET),
            CONF_SERIALIZER: spark.conf.get(CONF_SERIALIZER, NOT_SET),
        }
        info["key_configs"] = key_configs

        return info

    except Exception as e:
        return {"error": f"Failed to get session info: {e}"}


def print_session_summary(spark: SparkSession) -> None:
    """
    Print a formatted summary of the current Spark session.

    Args:
        spark: SparkSession to summarize

    Example:
         print_session_summary(spark)
        ========================================
        Spark Session Summary
        ========================================
        Application: my_application
        Spark Version: 3.5.0
        ...
    """
    info = get_session_info(spark)

    if "error" in info:
        _session_logger.warning("⚠️  %s", info["error"])
        return

    _session_logger.info("=" * 50)
    _session_logger.info("Spark Session Summary")
    _session_logger.info("=" * 50)
    _session_logger.info("Application: %s", info["app_name"])
    _session_logger.info("Application ID: %s", info["app_id"])
    _session_logger.info("Spark Version: %s", info["spark_version"])
    _session_logger.info("Master: %s", info["master"])
    _session_logger.info("Deploy Mode: %s", info["deploy_mode"])
    _session_logger.info("Executor Count: %s", info["executor_count"])
    _session_logger.info("Default Parallelism: %s", info["default_parallelism"])
    _session_logger.info("Python Version: %s", info["python_version"])
    _session_logger.info("")
    _session_logger.info("Key Configurations:")
    for key, value in info["key_configs"].items():
        _session_logger.info("  %s: %s", key, value)
    _session_logger.info("=" * 50)
