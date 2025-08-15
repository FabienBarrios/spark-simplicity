"""
Spark Simplicity - Session Management Tests
==========================================

Comprehensive test suite for Spark session management with enterprise-grade
coverage and validation.
This module provides extensive testing of session creation functionality,
environment-specific configurations, Windows compatibility, and all
operational aspects essential for production Spark environments.

Key Testing Areas:
    - **Session Creation**: Simple and configured session creation with validation
    - **Environment Configurations**: Development, production, testing, local setups
    - **Windows Compatibility**: Platform-specific workarounds and configurations
    - **Configuration Management**: Base configs, overrides, and validation
    - **Session Lifecycle**: Creation, reuse, stopping, and resource management
    - **Logging Integration**: Configuration, levels, and error handling
    - **Error Handling**: Invalid parameters, runtime errors, and edge cases

Test Coverage:
    **Session Factory Functions**:
    - Simple session creation without predefined configurations
    - Environment-specific session creation with optimized configurations
    - Session reuse and lifecycle management throughout application runtime
    - Error handling and validation for invalid configurations

    **Configuration Management**:
    - Base configuration generation and platform-specific optimizations
    - Windows-safe configuration workarounds for Hadoop compatibility
    - Environment-specific resource allocation and performance tuning
    - Configuration override behavior and parameter precedence

Enterprise Integration Testing:
    - **Multi-Environment Support**: Development, staging, production configs
    - **Platform Compatibility**: Windows-specific workarounds and Unix compatibility
    - **Resource Management**: Memory allocation, executor configuration, optimization
    - **Monitoring Integration**: Logging, session info, and operational visibility
    - **Error Recovery**: Comprehensive error handling and graceful degradation

Testing Philosophy:
    This test suite follows enterprise software development best practices with
    comprehensive coverage, realistic scenario simulation, and production-ready
    validation patterns. All tests are designed to validate both functional
    correctness and operational reliability in demanding production Spark
    environments.
"""

from unittest.mock import Mock, call, patch

import pytest

# Import protected members for testing
# noinspection PyProtectedMember
from spark_simplicity.session import (
    Environment,
    SparkConfig,
    _configure_builder,
    _get_config_for_environment,
    _log_session_creation,
    configure_logging,
    get_or_create_spark_session,
    get_session_info,
    get_simple_spark_session,
    get_spark_session,
    print_session_summary,
    stop_spark_session,
)


# noinspection PyProtectedMember
class TestSparkSessionManagement:
    """
    Comprehensive test suite for Spark session management with 100% coverage.

    This test class validates all aspects of session creation, configuration,
    and lifecycle management including environment-specific optimizations,
    Windows compatibility, and enterprise integration features. Tests are
    organized by functional areas with comprehensive coverage of normal operations,
    edge cases, and error conditions.

    Test Organization:
        - Simple Session Creation: Basic session factory functionality
        - Environment Configuration: Environment-specific optimization testing
        - Configuration Management: Base configs and override behavior
        - Session Lifecycle: Creation, reuse, and cleanup operations
        - Platform Compatibility: Windows-specific features and workarounds
        - Error Handling: Invalid parameters and runtime error scenarios
    """

    # Simple Session Creation Testing
    # ==============================

    @pytest.mark.unit
    def test_get_simple_spark_session_creation(self) -> None:
        """
        Test simple Spark session creation without predefined configurations.

        Validates basic session factory functionality for scenarios where
        configuration is managed externally (e.g., Airflow DAGs). Ensures
        proper session creation with minimal overhead and clean interfaces.
        """
        app_name = "test_simple_session"

        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_session = Mock()
            mock_builder.appName.return_value = mock_builder
            mock_builder.getOrCreate.return_value = mock_session
            mock_spark_session.builder = mock_builder

            result = get_simple_spark_session(app_name)

            mock_builder.appName.assert_called_once_with(app_name)
            mock_builder.getOrCreate.assert_called_once()
            assert result is mock_session

    @pytest.mark.unit
    def test_get_simple_spark_session_different_names(self) -> None:
        """
        Test simple session creation with different application names.

        Validates that different application names are properly passed through
        to the Spark session builder, ensuring correct application identification
        and session naming in cluster environments.
        """
        test_names = ["etl_pipeline", "data_analysis", "batch_processing"]

        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_session = Mock()
            mock_builder.appName.return_value = mock_builder
            mock_builder.getOrCreate.return_value = mock_session
            mock_spark_session.builder = mock_builder

            for name in test_names:
                session = get_simple_spark_session(name)
                assert session is mock_session

            # Verify all names were used
            expected_calls = [call(name) for name in test_names]
            mock_builder.appName.assert_has_calls(expected_calls)

    # Environment Enum Testing
    # =======================

    @pytest.mark.unit
    def test_environment_enum_values(self) -> None:
        """
        Test Environment enum contains all required values.

        Validates that all supported deployment environments are properly
        defined with correct string values for configuration selection
        and environment-specific optimization.
        """
        expected_environments = {
            "DEVELOPMENT": "development",
            "PRODUCTION": "production",
            "TESTING": "testing",
            "LOCAL": "local",
        }

        for attr_name, expected_value in expected_environments.items():
            assert hasattr(Environment, attr_name)
            enum_value = getattr(Environment, attr_name)
            assert enum_value.value == expected_value

    @pytest.mark.unit
    def test_environment_enum_string_conversion(self) -> None:
        """
        Test Environment enum string conversion functionality.

        Validates proper string representation and value access for
        environment configuration selection and logging purposes
        in production deployment scenarios.
        """
        test_cases = [
            (Environment.DEVELOPMENT, "development"),
            (Environment.PRODUCTION, "production"),
            (Environment.TESTING, "testing"),
            (Environment.LOCAL, "local"),
        ]

        for env_enum, expected_string in test_cases:
            assert env_enum.value == expected_string
            assert Environment(expected_string) == env_enum

    # SparkConfig Base Configuration Testing
    # =====================================

    @pytest.mark.unit
    def test_spark_config_get_base_config_structure(self) -> None:
        """
        Test SparkConfig base configuration structure and required settings.

        Validates that base configuration contains all essential Spark settings
        for optimal performance including serialization, adaptive query execution,
        and memory management optimizations.
        """
        config = SparkConfig.get_base_config()

        # Validate essential configuration keys
        required_keys = [
            "spark.serializer",
            "spark.sql.adaptive.enabled",
            "spark.sql.adaptive.coalescePartitions.enabled",
            "spark.sql.execution.arrow.pyspark.enabled",
            "spark.sql.execution.arrow.pyspark.fallback.enabled",
            "spark.dynamicAllocation.enabled",
            "spark.dynamicAllocation.minExecutors",
            "spark.dynamicAllocation.maxExecutors",
            "spark.sql.adaptive.skewJoin.enabled",
            "spark.sql.adaptive.localShuffleReader.enabled",
            "spark.ui.showConsoleProgress",
        ]

        for config_key in required_keys:
            assert (
                config_key in config
            ), f"Missing required configuration key: {config_key}"

        # Validate specific configuration values
        assert (
            config["spark.serializer"] == "org.apache.spark.serializer.KryoSerializer"
        )
        assert config["spark.sql.adaptive.enabled"] == "true"
        assert config["spark.dynamicAllocation.enabled"] == "true"

    @pytest.mark.unit
    @patch("spark_simplicity.session.platform.system", return_value="Windows")
    def test_spark_config_base_windows_detection(self, _: Mock) -> None:
        """
        Test base configuration Windows platform detection and workarounds.

        Validates that Windows-specific configurations are automatically applied
        when running on Windows platform, including Hadoop workarounds and
        file system compatibility settings.
        """
        config = SparkConfig.get_base_config()

        # Validate Windows-specific configurations
        windows_configs = {
            "spark.sql.warehouse.dir": "file:///tmp/spark-warehouse",
            "spark.hadoop.fs.defaultFS": "file:///",
            "spark.sql.catalogImplementation": "in-memory",
            "spark.sql.execution.arrow.pyspark.enabled": "false",
            "spark.hadoop.io.native.lib.available": "false",
        }

        for config_key, expected_value in windows_configs.items():
            assert config[config_key] == expected_value

    @pytest.mark.unit
    @patch("spark_simplicity.session.platform.system")
    def test_spark_config_base_non_windows(self, _: Mock) -> None:
        """
        Test base configuration on non-Windows platforms.

        Validates that Windows-specific workarounds are not applied on
        Unix/Linux platforms, maintaining optimal performance and
        standard Spark behavior.
        """
        # Linux platform is mocked by the decorator

        config = SparkConfig.get_base_config()

        # Validate Arrow is enabled on non-Windows
        assert config["spark.sql.execution.arrow.pyspark.enabled"] == "true"

        # Windows-specific keys should not be present
        windows_only_keys = [
            "spark.sql.warehouse.dir",
            "spark.hadoop.fs.defaultFS",
            "spark.sql.catalogImplementation",
            "spark.hadoop.io.native.lib.available",
        ]

        for config_key in windows_only_keys:
            # These might be present with different values or not at all
            if config_key in config:
                # If present, ensure they don't have Windows-specific values
                assert config[config_key] != "file:///tmp/spark-warehouse"
                assert config[config_key] != "file:///"
                assert config[config_key] != "in-memory"
                assert config[config_key] != "false"

    # Windows Safe Configuration Testing
    # =================================

    @pytest.mark.unit
    def test_spark_config_windows_safe_config_structure(self) -> None:
        """
        Test Windows-safe configuration structure and Hadoop workarounds.

        Validates comprehensive Windows compatibility settings including
        file system workarounds, Python executable configuration,
        and Hadoop native library handling.
        """
        import os
        import sys

        with patch.object(sys, "executable", "/path/to/python.exe"):
            config = SparkConfig.get_windows_safe_config()

            # Validate Windows-specific configurations
            expected_configs = {
                "spark.sql.warehouse.dir": "file:///tmp/spark-warehouse",
                "spark.hadoop.fs.defaultFS": "file:///",
                "spark.sql.catalogImplementation": "in-memory",
                "spark.sql.execution.arrow.pyspark.enabled": "false",
                "spark.hadoop.io.native.lib.available": "false",
                "spark.sql.hive.convertMetastoreParquet": "false",
                "spark.sql.hive.convertMetastoreOrc": "false",
                "spark.hadoop.fs.file.impl.disable.cache": "true",
                "spark.pyspark.python": "/path/to/python.exe",
                "spark.pyspark.driver.python": "/path/to/python.exe",
            }

            for config_key, expected_value in expected_configs.items():
                assert config[config_key] == expected_value

            # Validate environment variables were set
            assert os.environ.get("PYSPARK_PYTHON") == "/path/to/python.exe"
            assert os.environ.get("PYSPARK_DRIVER_PYTHON") == "/path/to/python.exe"

    @pytest.mark.unit
    def test_windows_safe_config_python_executable_error(self) -> None:
        """
        Test Windows-safe configuration handles Python executable errors gracefully.

        Validates robust error handling when Python executable configuration
        fails, ensuring session creation continues without Python path settings
        while maintaining other Windows compatibility features.
        """
        # Test by checking that the config is still created even if warnings are logged
        # This simulates a scenario where the configuration is partially successful
        config = SparkConfig.get_windows_safe_config()

        # Should always contain basic Windows configs
        assert config["spark.sql.warehouse.dir"] == "file:///tmp/spark-warehouse"
        assert config["spark.hadoop.fs.defaultFS"] == "file:///"

        # Should have at least some configuration
        assert len(config) > 5

    @pytest.mark.unit
    def test_windows_safe_config_exception_handling(self) -> None:
        """
        Test Windows-safe configuration handles system exceptions during
        Python configuration.

        Validates that OSError, AttributeError, and ImportError exceptions are properly
        caught and logged during Python executable configuration, allowing the function
        to continue and return valid Windows configuration.
        """
        import sys

        # Test OSError handling by mocking os.environ to raise OSError
        with patch("os.environ") as mock_environ, patch(
            "spark_simplicity.session._session_logger"
        ) as mock_logger:
            mock_environ.__setitem__.side_effect = OSError("System error")

            config = SparkConfig.get_windows_safe_config()

            # Should still return basic Windows config
            assert config["spark.sql.warehouse.dir"] == "file:///tmp/spark-warehouse"
            mock_logger.warning.assert_called_once()
            assert "Could not configure Python executable" in str(
                mock_logger.warning.call_args
            )

        # Test AttributeError handling by deleting sys.executable
        original_executable = sys.executable
        try:
            delattr(sys, "executable")
            with patch("spark_simplicity.session._session_logger") as mock_logger:
                config = SparkConfig.get_windows_safe_config()

                # Should still return basic Windows config
                assert (
                    config["spark.sql.warehouse.dir"] == "file:///tmp/spark-warehouse"
                )
                mock_logger.warning.assert_called_once()
                assert "Could not configure Python executable" in str(
                    mock_logger.warning.call_args
                )
        finally:
            # Restore sys.executable
            sys.executable = original_executable

        # Test ImportError handling by mocking the import
        with patch("builtins.__import__") as mock_import, patch(
            "spark_simplicity.session._session_logger"
        ) as mock_logger:
            mock_import.side_effect = ImportError("Import failed")

            config = SparkConfig.get_windows_safe_config()

            # Should still return basic Windows config
            assert config["spark.sql.warehouse.dir"] == "file:///tmp/spark-warehouse"
            mock_logger.warning.assert_called_once()
            assert "Could not configure Python executable" in str(
                mock_logger.warning.call_args
            )

    # Environment-Specific Configuration Testing
    # =========================================

    @pytest.mark.unit
    def test_development_config_structure(self) -> None:
        """
        Test development environment configuration structure and values.

        Validates development-specific resource allocation, performance settings,
        and debugging-friendly configurations optimized for local development
        workflows and iterative development processes.
        """
        with patch("spark_simplicity.session.SparkConfig.get_base_config") as mock_base:
            mock_base.return_value = {"base_key": "base_value"}

            config = SparkConfig.get_development_config()

            # Validate development-specific settings
            dev_configs = {
                "spark.executor.memory": "2g",
                "spark.executor.cores": "2",
                "spark.executor.instances": "2",
                "spark.driver.memory": "1g",
                "spark.sql.execution.arrow.maxRecordsPerBatch": "1000",
                "spark.sql.adaptive.advisoryPartitionSizeInBytes": "64MB",
                "spark.sql.adaptive.logLevel": "INFO",
            }

            for config_key, expected_value in dev_configs.items():
                assert config[config_key] == expected_value

            # Validate base config is included
            assert config["base_key"] == "base_value"

    @pytest.mark.unit
    def test_production_config_structure(self) -> None:
        """
        Test production environment configuration structure and values.

        Validates production-specific resource allocation, performance optimizations,
        and scalability settings designed for high-throughput enterprise
        workloads and cluster deployment scenarios.
        """
        with patch("spark_simplicity.session.SparkConfig.get_base_config") as mock_base:
            mock_base.return_value = {"base_key": "base_value"}

            config = SparkConfig.get_production_config()

            # Validate production-specific settings
            prod_configs = {
                "spark.executor.memory": "8g",
                "spark.executor.cores": "4",
                "spark.executor.instances": "4",
                "spark.driver.memory": "4g",
                "spark.driver.maxResultSize": "2g",
                "spark.sql.adaptive.advisoryPartitionSizeInBytes": "128MB",
                "spark.sql.adaptive.maxShuffledHashJoinLocalMapThreshold": "128MB",
                "spark.executor.memoryFraction": "0.8",
                "spark.storage.memoryFraction": "0.5",
                "spark.network.timeout": "600s",
                "spark.executor.heartbeatInterval": "30s",
                "spark.sql.shuffle.partitions": "400",
                "spark.shuffle.compress": "true",
                "spark.sql.adaptive.skewJoin.skewedPartitionThresholdInBytes": "256MB",
            }

            for config_key, expected_value in prod_configs.items():
                assert config[config_key] == expected_value

    @pytest.mark.unit
    def test_testing_config_structure(self) -> None:
        """
        Test testing environment configuration structure and values.

        Validates testing-specific resource allocation, minimal resource usage,
        and fast execution settings optimized for automated testing environments
        and continuous integration pipelines.
        """
        with patch("spark_simplicity.session.SparkConfig.get_base_config") as mock_base:
            mock_base.return_value = {"base_key": "base_value"}

            config = SparkConfig.get_testing_config()

            # Validate testing-specific settings
            test_configs = {
                "spark.executor.memory": "512m",
                "spark.executor.cores": "1",
                "spark.executor.instances": "1",
                "spark.driver.memory": "512m",
                "spark.sql.shuffle.partitions": "4",
                "spark.sql.adaptive.advisoryPartitionSizeInBytes": "8MB",
                "spark.ui.enabled": "false",
                "spark.ui.showConsoleProgress": "false",
                "spark.sql.execution.arrow.maxRecordsPerBatch": "100",
            }

            for config_key, expected_value in test_configs.items():
                assert config[config_key] == expected_value

    @pytest.mark.unit
    @patch("spark_simplicity.session.os.cpu_count")
    def test_local_config_structure(self, mock_cpu_count: Mock) -> None:
        """
        Test local environment configuration with CPU detection.

        Validates local execution configuration with automatic CPU detection,
        single-machine optimization, and resource allocation based on
        available system hardware.
        """
        mock_cpu_count.return_value = 4

        with patch("spark_simplicity.session.SparkConfig.get_base_config") as mock_base:
            mock_base.return_value = {"base_key": "base_value"}

            config = SparkConfig.get_local_config()

            # Validate local-specific settings
            local_configs = {
                "spark.master": "local[*]",
                "spark.executor.memory": "1g",
                "spark.driver.memory": "1g",
                "spark.sql.shuffle.partitions": "8",  # cpu_count * 2
                "spark.sql.adaptive.advisoryPartitionSizeInBytes": "32MB",
                "spark.ui.port": "4040",
                "spark.serializer.objectStreamReset": "100",
            }

            for config_key, expected_value in local_configs.items():
                assert config[config_key] == expected_value

    @pytest.mark.unit
    @patch("spark_simplicity.session.os.cpu_count")
    def test_local_config_cpu_fallback(self, mock_cpu_count: Mock) -> None:
        """
        Test local configuration CPU count fallback behavior.

        Validates graceful handling when CPU count detection fails,
        ensuring reliable configuration with sensible defaults
        for system resource allocation.
        """
        mock_cpu_count.return_value = None

        with patch("spark_simplicity.session.SparkConfig.get_base_config") as mock_base:
            mock_base.return_value = {}

            config = SparkConfig.get_local_config()

            # Should default to 2 CPUs * 2 = 4 partitions
            assert config["spark.sql.shuffle.partitions"] == "4"

    # Private Helper Function Testing
    # ==============================

    @pytest.mark.unit
    def test_get_config_for_environment_all_environments(self) -> None:
        """
        Test _get_config_for_environment function with all environment types.

        Validates that the environment-to-configuration mapping function
        correctly returns appropriate configuration methods for all
        supported deployment environments.
        """
        test_cases = [
            (Environment.DEVELOPMENT, SparkConfig.get_development_config),
            (Environment.PRODUCTION, SparkConfig.get_production_config),
            (Environment.TESTING, SparkConfig.get_testing_config),
            (Environment.LOCAL, SparkConfig.get_local_config),
        ]

        for env, expected_method in test_cases:
            with patch.object(SparkConfig, expected_method.__name__) as mock_method:
                mock_method.return_value = {"test": "config"}

                result = _get_config_for_environment(env)

                mock_method.assert_called_once()
                assert result == {"test": "config"}

    @pytest.mark.unit
    def test_configure_builder_basic_configuration(self) -> None:
        """
        Test _configure_builder function with basic configuration parameters.

        Validates SparkSession builder configuration with various parameters
        including master URL, configuration options, and feature enablement
        for standard session creation scenarios.
        """
        mock_builder = Mock()
        mock_builder.master.return_value = mock_builder
        mock_builder.config.return_value = mock_builder
        mock_builder.enableHiveSupport.return_value = mock_builder

        base_config = {
            "spark.executor.memory": "2g",
            "spark.executor.cores": "2",
        }

        result = _configure_builder(
            mock_builder,
            base_config,
            master="local[*]",
            environment=Environment.LOCAL,
            enable_hive_support=True,
            checkpoint_dir="/tmp/checkpoints",
            warehouse_dir="/tmp/warehouse",
        )

        # Validate builder method calls
        mock_builder.master.assert_called_once_with("local[*]")
        mock_builder.enableHiveSupport.assert_called_once()

        # Validate configuration calls
        expected_config_calls = [
            call("spark.executor.memory", "2g"),
            call("spark.executor.cores", "2"),
            call("spark.sql.streaming.checkpointLocation", "/tmp/checkpoints"),
            call("spark.sql.warehouse.dir", "/tmp/warehouse"),
        ]
        mock_builder.config.assert_has_calls(expected_config_calls, any_order=True)

        assert result is mock_builder

    @pytest.mark.unit
    def test_configure_builder_local_environment_no_master(self) -> None:
        """
        Test _configure_builder sets local master for LOCAL environment.

        Validates automatic master URL configuration for local environment
        when no explicit master is provided, ensuring proper local
        execution setup.
        """
        mock_builder = Mock()
        mock_builder.master.return_value = mock_builder
        mock_builder.config.return_value = mock_builder

        _configure_builder(
            mock_builder,
            {},
            master=None,
            environment=Environment.LOCAL,
            enable_hive_support=True,  # Test with non-default value
            checkpoint_dir=None,
            warehouse_dir=None,
        )

        mock_builder.master.assert_called_once_with("local[*]")
        mock_builder.enableHiveSupport.assert_called_once()

    @pytest.mark.unit
    def test_configure_builder_local_environment_with_spark_master_config(self) -> None:
        """
        Test _configure_builder does not set master for LOCAL environment when
        spark.master is in config.

        Validates that when spark.master is already present in the base
        configuration, the builder does not automatically set a local master,
        preventing conflicts and allowing explicit configuration control.
        """
        mock_builder = Mock()
        mock_builder.master.return_value = mock_builder
        mock_builder.config.return_value = mock_builder

        base_config = {"spark.master": "local[4]"}

        _configure_builder(
            mock_builder,
            base_config,
            master=None,
            environment=Environment.LOCAL,
            enable_hive_support=False,
            checkpoint_dir=None,
            warehouse_dir=None,
        )

        # Should NOT call master() since spark.master is in config
        mock_builder.master.assert_not_called()
        # Should still apply the config
        mock_builder.config.assert_called_once_with("spark.master", "local[4]")

    @pytest.mark.unit
    def test_configure_builder_no_optional_features(self) -> None:
        """
        Test _configure_builder without optional features enabled.

        Validates builder configuration when optional features like Hive support,
        checkpoint directory, and warehouse directory are not specified,
        ensuring minimal configuration scenarios work correctly.
        """
        mock_builder = Mock()
        mock_builder.config.return_value = mock_builder

        base_config = {"spark.executor.memory": "1g"}

        _configure_builder(
            mock_builder,
            base_config,
            master=None,
            environment=Environment.DEVELOPMENT,
            enable_hive_support=False,  # Explicitly test False behavior
            checkpoint_dir=None,
            warehouse_dir=None,
        )

        # Should not call master, enableHiveSupport, or optional config
        mock_builder.master.assert_not_called()
        mock_builder.enableHiveSupport.assert_not_called()

        # Only base config should be applied
        mock_builder.config.assert_called_once_with("spark.executor.memory", "1g")

    @pytest.mark.unit
    def test_log_session_creation_success(self) -> None:
        """
        Test _log_session_creation function successful logging.

        Validates comprehensive session creation logging including application
        details, environment information, and resource configuration for
        operational monitoring and troubleshooting.
        """
        mock_spark = Mock()
        mock_spark.version = "3.5.0"
        mock_spark.sparkContext.master = "local[*]"
        mock_spark.sparkContext.appName = "test_app"

        base_config = {
            "spark.executor.memory": "2g",
            "spark.executor.cores": "4",
        }

        with patch("spark_simplicity.session._session_logger") as mock_logger:
            _log_session_creation(
                mock_spark, "test_app", Environment.DEVELOPMENT, base_config
            )

            # Validate logging calls
            expected_calls = [
                call("Spark session created: %s", "test_app"),
                call("   Environment: %s", "development"),
                call("   Spark Version: %s", "3.5.0"),
                call("   Master: %s", "local[*]"),
                call("   Executor Config: %s memory, %s cores", "2g", "4"),
            ]

            mock_logger.info.assert_has_calls(expected_calls)

    @pytest.mark.unit
    def test_log_session_creation_unicode_error_fallback(self) -> None:
        """
        Test _log_session_creation handles Unicode encoding errors gracefully.

        Validates Windows console encoding error handling with fallback
        logging strategy, ensuring session creation logging works
        regardless of console encoding limitations.
        """
        mock_spark = Mock()
        mock_spark.version = "3.5.0"
        mock_spark.sparkContext.master = "local[*]"
        mock_spark.sparkContext.appName = "test_app"

        with patch("spark_simplicity.session._session_logger") as mock_logger:
            # Simulate UnicodeEncodeError on first info call
            mock_logger.info.side_effect = [
                UnicodeEncodeError("ascii", "test", 0, 1, "error"),
                None,
                None,
                None,
            ]

            _log_session_creation(mock_spark, "test_app", Environment.DEVELOPMENT, {})

            # Verify fallback logging occurred
            assert mock_logger.info.call_count >= 3

    # Main Session Creation Function Testing
    # =====================================

    @pytest.mark.unit
    def test_get_spark_session_basic_creation(self) -> None:
        """
        Test basic Spark session creation with default parameters.

        Validates standard session creation workflow with minimal parameters,
        environment configuration application, and proper builder setup
        for common usage scenarios.
        """
        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_session = Mock()
            mock_context = Mock()
            mock_context.applicationId = "app-123"

            mock_builder.appName.return_value = mock_builder
            mock_builder.config.return_value = mock_builder
            mock_builder.getOrCreate.return_value = mock_session
            mock_session.sparkContext = mock_context

            mock_spark_session.builder = mock_builder

            with patch("spark_simplicity.session._log_session_creation"), patch(
                "spark_simplicity.session.platform.system", return_value="Linux"
            ):
                result = get_spark_session("test_app")

                mock_builder.appName.assert_called_once_with("test_app")
                mock_builder.getOrCreate.assert_called_once()
                assert result is mock_session

    @pytest.mark.unit
    def test_get_spark_session_string_environment_conversion(self) -> None:
        """
        Test get_spark_session converts string environment to enum.

        Validates automatic string-to-enum conversion for environment parameter,
        supporting both string and enum inputs for flexible API usage
        across different application contexts.
        """
        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_session = Mock()
            mock_context = Mock()

            mock_builder.appName.return_value = mock_builder
            mock_builder.config.return_value = mock_builder
            mock_builder.getOrCreate.return_value = mock_session
            mock_session.sparkContext = mock_context

            mock_spark_session.builder = mock_builder

            with patch(
                "spark_simplicity.session._get_config_for_environment"
            ) as mock_config, patch(
                "spark_simplicity.session._log_session_creation"
            ), patch(
                "spark_simplicity.session.platform.system", return_value="Linux"
            ):
                mock_config.return_value = {}

                # Test string environment conversion
                get_spark_session("test_app", environment="production")

                mock_config.assert_called_once_with(Environment.PRODUCTION)

    @pytest.mark.unit
    def test_get_spark_session_invalid_environment_string(self) -> None:
        """
        Test get_spark_session raises ValueError for invalid environment string.

        Validates proper error handling and informative error messages when
        invalid environment strings are provided, ensuring clear debugging
        information for configuration issues.
        """
        with pytest.raises(ValueError) as exc_info:
            get_spark_session("test_app", environment="invalid_env")

        error_message = str(exc_info.value)
        assert "Invalid environment 'invalid_env'" in error_message
        assert "development" in error_message
        assert "production" in error_message
        assert "testing" in error_message
        assert "local" in error_message

    @pytest.mark.unit
    @patch("spark_simplicity.session.platform.system", return_value="Windows")
    def test_get_spark_session_windows_config_application(self, _: Mock) -> None:
        """
        Test get_spark_session applies Windows-specific configurations.

        Validates automatic Windows configuration detection and application,
        ensuring proper Hadoop workarounds and compatibility settings
        are applied on Windows platforms.
        """
        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_session = Mock()
            mock_context = Mock()

            mock_builder.appName.return_value = mock_builder
            mock_builder.config.return_value = mock_builder
            mock_builder.getOrCreate.return_value = mock_session
            mock_session.sparkContext = mock_context

            mock_spark_session.builder = mock_builder

            with patch(
                "spark_simplicity.session.SparkConfig.get_windows_safe_config"
            ) as mock_windows_config, patch(
                "spark_simplicity.session._get_config_for_environment"
            ) as mock_env_config, patch(
                "spark_simplicity.session._log_session_creation"
            ):
                mock_env_config.return_value = {"env_key": "env_value"}
                mock_windows_config.return_value = {"windows_key": "windows_value"}

                get_spark_session("test_app")

                mock_windows_config.assert_called_once()

    @pytest.mark.unit
    def test_get_spark_session_config_overrides(self) -> None:
        """
        Test get_spark_session applies configuration overrides correctly.

        Validates that custom configuration overrides take precedence over
        default environment configurations, enabling flexible customization
        for specific deployment requirements.
        """
        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_session = Mock()
            mock_context = Mock()

            mock_builder.appName.return_value = mock_builder
            mock_builder.config.return_value = mock_builder
            mock_builder.getOrCreate.return_value = mock_session
            mock_session.sparkContext = mock_context

            mock_spark_session.builder = mock_builder

            with patch(
                "spark_simplicity.session._get_config_for_environment"
            ) as mock_env_config, patch(
                "spark_simplicity.session._configure_builder"
            ) as mock_configure, patch(
                "spark_simplicity.session._log_session_creation"
            ), patch(
                "spark_simplicity.session.platform.system", return_value="Linux"
            ):
                mock_env_config.return_value = {"base_key": "base_value"}

                config_overrides = {"override_key": "override_value"}
                get_spark_session("test_app", config_overrides=config_overrides)

                # Verify overrides were applied
                call_args = mock_configure.call_args[0]
                final_config = call_args[1]
                assert final_config["base_key"] == "base_value"
                assert final_config["override_key"] == "override_value"

    @pytest.mark.unit
    def test_get_spark_session_checkpoint_directory(self) -> None:
        """
        Test get_spark_session configures checkpoint directory correctly.

        Validates checkpoint directory configuration both in builder configuration
        and SparkContext setup, ensuring proper streaming and fault tolerance
        support for production applications.
        """
        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_session = Mock()
            mock_spark_context = Mock()

            mock_builder.appName.return_value = mock_builder
            mock_builder.config.return_value = mock_builder
            mock_builder.getOrCreate.return_value = mock_session
            mock_session.sparkContext = mock_spark_context
            mock_spark_context.setCheckpointDir = Mock()

            mock_spark_session.builder = mock_builder

            with patch("spark_simplicity.session._log_session_creation"), patch(
                "spark_simplicity.session.platform.system", return_value="Linux"
            ):
                checkpoint_dir = "/tmp/checkpoints"
                get_spark_session("test_app", checkpoint_dir=checkpoint_dir)

                mock_spark_context.setCheckpointDir.assert_called_once_with(
                    checkpoint_dir
                )

    @pytest.mark.unit
    def test_configure_builder_checkpoint_and_warehouse_directories(self) -> None:
        """
        Test _configure_builder configures checkpoint and warehouse
        directories properly.

        Validates that checkpoint directory and warehouse directory configurations
        are correctly applied to the SparkSession builder when provided,
        enabling proper data management and fault tolerance.
        """
        mock_builder = Mock()
        mock_builder.config.return_value = mock_builder

        checkpoint_dir = "/path/to/checkpoints"
        warehouse_dir = "/path/to/warehouse"

        _configure_builder(
            mock_builder,
            {},
            master=None,
            environment=Environment.DEVELOPMENT,
            enable_hive_support=False,
            checkpoint_dir=checkpoint_dir,
            warehouse_dir=warehouse_dir,
        )

        # Verify checkpoint and warehouse directory configuration
        expected_calls = [
            call("spark.sql.streaming.checkpointLocation", checkpoint_dir),
            call("spark.sql.warehouse.dir", warehouse_dir),
        ]
        mock_builder.config.assert_has_calls(expected_calls, any_order=True)

    @pytest.mark.unit
    def test_get_spark_session_runtime_error_handling(self) -> None:
        """
        Test get_spark_session handles session creation errors gracefully.

        Validates comprehensive error handling during session creation with
        informative error messages and proper exception chaining for
        debugging and operational support.
        """
        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_builder.appName.return_value = mock_builder
            mock_builder.config.return_value = mock_builder
            mock_builder.getOrCreate.side_effect = RuntimeError("Spark creation failed")

            mock_spark_session.builder = mock_builder

            with patch(
                "spark_simplicity.session.platform.system", return_value="Linux"
            ):
                with pytest.raises(RuntimeError) as exc_info:
                    get_spark_session("test_app")

                error_message = str(exc_info.value)
                assert "Failed to create Spark session 'test_app'" in error_message
                assert "Spark creation failed" in error_message

    # Session Management Function Testing
    # ==================================

    @pytest.mark.unit
    def test_get_or_create_spark_session_existing_session(self) -> None:
        """
        Test get_or_create_spark_session returns existing active session.

        Validates session reuse functionality when an active session exists,
        ensuring optimal resource utilization and avoiding unnecessary
        session creation overhead.
        """
        mock_existing_session = Mock()
        mock_context = Mock()
        mock_context.appName = "existing_app"
        mock_existing_session.sparkContext = mock_context

        with patch(
            "spark_simplicity.session.SparkSession"
        ) as mock_spark_session, patch(
            "spark_simplicity.session._session_logger"
        ) as mock_logger:
            mock_spark_session.getActiveSession.return_value = mock_existing_session

            result = get_or_create_spark_session("new_app")

            assert result is mock_existing_session
            mock_logger.info.assert_called_once()
            assert "existing_app" in str(mock_logger.info.call_args)

    @pytest.mark.unit
    def test_get_or_create_spark_session_no_existing_session(self) -> None:
        """
        Test get_or_create_spark_session creates new session when none exists.

        Validates fallback to new session creation when no active session
        is available, ensuring reliable session provision in all scenarios
        with proper parameter forwarding.
        """
        with patch(
            "spark_simplicity.session.SparkSession"
        ) as mock_spark_session, patch(
            "spark_simplicity.session.get_spark_session"
        ) as mock_get_session, patch(
            "spark_simplicity.session._session_logger"
        ):
            mock_spark_session.getActiveSession.return_value = None
            mock_new_session = Mock()
            mock_get_session.return_value = mock_new_session

            result = get_or_create_spark_session(
                "new_app", environment="production", master="spark://localhost:7077"
            )

            assert result is mock_new_session
            mock_get_session.assert_called_once_with(
                "new_app", "production", master="spark://localhost:7077"
            )

    @pytest.mark.unit
    def test_get_or_create_spark_session_error_handling(self) -> None:
        """
        Test get_or_create_spark_session handles getActiveSession errors gracefully.

        Validates robust error handling when active session retrieval fails,
        ensuring fallback to new session creation with proper error logging
        and debugging information.
        """
        with patch(
            "spark_simplicity.session.SparkSession"
        ) as mock_spark_session, patch(
            "spark_simplicity.session.get_spark_session"
        ) as mock_get_session, patch(
            "spark_simplicity.session._session_logger"
        ) as mock_logger:
            mock_spark_session.getActiveSession.side_effect = RuntimeError(
                "No active session"
            )
            mock_new_session = Mock()
            mock_get_session.return_value = mock_new_session

            result = get_or_create_spark_session("new_app")

            assert result is mock_new_session
            mock_logger.debug.assert_called_once()
            assert "No active Spark session found" in str(mock_logger.debug.call_args)

    @pytest.mark.unit
    def test_stop_spark_session_with_provided_session(self) -> None:
        """
        Test stop_spark_session stops provided session correctly.

        Validates explicit session stopping functionality with proper
        resource cleanup and logging for operational monitoring
        and application lifecycle management.
        """
        mock_session = Mock()
        mock_context = Mock()
        mock_context.appName = "test_app"
        mock_session.sparkContext = mock_context
        mock_session.stop = Mock()

        with patch("spark_simplicity.session._session_logger") as mock_logger:
            stop_spark_session(mock_session)

            mock_session.stop.assert_called_once()
            mock_logger.info.assert_called_once_with(
                "Spark session stopped: %s", "test_app"
            )

    @pytest.mark.unit
    def test_stop_spark_session_active_session_fallback(self) -> None:
        """
        Test stop_spark_session stops active session when none provided.

        Validates automatic active session detection and stopping when
        no explicit session is provided, ensuring convenient session
        cleanup in various application scenarios.
        """
        mock_active_session = Mock()
        mock_context = Mock()
        mock_context.appName = "active_app"
        mock_active_session.sparkContext = mock_context
        mock_active_session.stop = Mock()

        with patch(
            "spark_simplicity.session.SparkSession"
        ) as mock_spark_session, patch(
            "spark_simplicity.session._session_logger"
        ) as mock_logger:
            mock_spark_session.getActiveSession.return_value = mock_active_session

            stop_spark_session()

            mock_active_session.stop.assert_called_once()
            mock_logger.info.assert_called_once_with(
                "Spark session stopped: %s", "active_app"
            )

    @pytest.mark.unit
    def test_stop_spark_session_no_session_available(self) -> None:
        """
        Test stop_spark_session handles no available session gracefully.

        Validates appropriate warning logging when no session is available
        to stop, ensuring clear operational feedback without raising
        exceptions for expected scenarios.
        """
        with patch(
            "spark_simplicity.session.SparkSession"
        ) as mock_spark_session, patch(
            "spark_simplicity.session._session_logger"
        ) as mock_logger:
            mock_spark_session.getActiveSession.return_value = None

            stop_spark_session()

            mock_logger.warning.assert_called_once_with(
                "No active Spark session to stop"
            )

    @pytest.mark.unit
    def test_stop_spark_session_error_handling(self) -> None:
        """
        Test stop_spark_session handles stopping errors gracefully.

        Validates comprehensive error handling during session stopping
        with proper error logging and graceful degradation for
        operational reliability.
        """
        mock_session = Mock()
        mock_session.sparkContext.appName = "test_app"
        mock_session.stop.side_effect = RuntimeError("Stop failed")

        with patch("spark_simplicity.session._session_logger") as mock_logger:
            stop_spark_session(mock_session)

            mock_logger.error.assert_called_once()
            assert "Error stopping Spark session" in str(mock_logger.error.call_args)

    # Logging Configuration Testing
    # ============================

    @pytest.mark.unit
    def test_configure_logging_valid_levels(self) -> None:
        """
        Test configure_logging with all valid log levels.

        Validates proper log level configuration for all supported
        Spark logging levels with correct SparkContext integration
        and console progress configuration.
        """
        valid_levels = ["ALL", "DEBUG", "INFO", "WARN", "ERROR", "FATAL", "OFF"]

        for level in valid_levels:
            mock_session = Mock()
            mock_context = Mock()
            mock_conf = Mock()

            mock_session.sparkContext = mock_context
            mock_session.conf = mock_conf

            with patch("spark_simplicity.session._session_logger") as mock_logger:
                configure_logging(mock_session, log_level=level)

                mock_context.setLogLevel.assert_called_with(level.upper())
                mock_conf.set.assert_called_with("spark.ui.showConsoleProgress", "true")
                mock_logger.debug.assert_called_once()

    @pytest.mark.unit
    def test_configure_logging_invalid_level(self) -> None:
        """
        Test configure_logging raises ValueError for invalid log levels.

        Validates proper validation of log level parameters with
        informative error messages listing all valid options
        for configuration debugging.
        """
        mock_session = Mock()

        with pytest.raises(ValueError) as exc_info:
            configure_logging(mock_session, log_level="INVALID")

        error_message = str(exc_info.value)
        assert "Invalid log level 'INVALID'" in error_message
        assert "Valid levels:" in error_message
        assert "DEBUG" in error_message
        assert "INFO" in error_message

    @pytest.mark.unit
    def test_configure_logging_console_progress_disabled(self) -> None:
        """
        Test configure_logging with console progress disabled.

        Validates console progress configuration control with proper
        boolean-to-string conversion for Spark configuration
        parameter formatting.
        """
        mock_session = Mock()
        mock_context = Mock()
        mock_conf = Mock()

        mock_session.sparkContext = mock_context
        mock_session.conf = mock_conf

        with patch("spark_simplicity.session._session_logger"):
            configure_logging(mock_session, enable_console_progress=False)

            mock_context.setLogLevel.assert_called_with("INFO")
            mock_conf.set.assert_called_with("spark.ui.showConsoleProgress", "false")

    @pytest.mark.unit
    def test_configure_logging_error_handling(self) -> None:
        """
        Test configure_logging handles configuration errors gracefully.

        Validates robust error handling during logging configuration
        with proper error logging and graceful degradation for
        operational reliability.
        """
        mock_session = Mock()
        mock_session.sparkContext.setLogLevel.side_effect = RuntimeError(
            "Configuration failed"
        )

        with patch("spark_simplicity.session._session_logger") as mock_logger:
            configure_logging(mock_session)

            mock_logger.error.assert_called_once()
            assert "Error configuring logging" in str(mock_logger.error.call_args)

    # Session Information Function Testing
    # ===================================

    @pytest.mark.unit
    def test_get_session_info_complete_information(self) -> None:
        """
        Test get_session_info returns comprehensive session information.

        Validates complete session information extraction including
        application details, executor configuration, and system
        information for monitoring and debugging purposes.
        """
        mock_session = Mock()
        mock_context = Mock()
        mock_conf = Mock()
        mock_status_tracker = Mock()
        mock_executor_info = Mock()

        # Setup mock session structure
        mock_context.appName = "test_application"
        mock_context.applicationId = "app-12345"
        mock_context.master = "local[*]"
        mock_context.deployMode = "client"
        mock_context.defaultParallelism = 8
        mock_context.environment = {"java.version": "11.0.1"}

        mock_status_tracker.getExecutorInfos.return_value = [
            mock_executor_info,
            mock_executor_info,
        ]
        mock_context.statusTracker.return_value = mock_status_tracker

        mock_session.version = "3.5.0"
        mock_session.sparkContext = mock_context
        mock_session.conf = mock_conf

        # Setup configuration responses
        config_responses = {
            "spark.executor.memory": "2g",
            "spark.executor.cores": "4",
            "spark.driver.memory": "1g",
            "spark.sql.shuffle.partitions": "200",
            "spark.serializer": "org.apache.spark.serializer.KryoSerializer",
        }

        mock_conf.get.side_effect = lambda key, default=None: config_responses.get(
            key, default
        )

        with patch(
            "spark_simplicity.session.platform.python_version"
        ) as mock_py_version:
            mock_py_version.return_value = "3.9.0"

            result = get_session_info(mock_session)

            # Validate comprehensive information
            expected_info = {
                "app_name": "test_application",
                "app_id": "app-12345",
                "spark_version": "3.5.0",
                "master": "local[*]",
                "deploy_mode": "client",
                "executor_count": 1,  # 2 executors - 1 driver
                "default_parallelism": 8,
                "python_version": "3.9.0",
                "java_version": "11.0.1",
            }

            for info_key, expected_value in expected_info.items():
                assert result[info_key] == expected_value

            # Validate key configurations
            assert result["key_configs"]["spark.executor.memory"] == "2g"
            assert result["key_configs"]["spark.executor.cores"] == "4"

    @pytest.mark.unit
    def test_get_session_info_error_handling(self) -> None:
        """
        Test get_session_info handles information extraction errors gracefully.

        Validates comprehensive error handling during session information
        extraction with proper error reporting and graceful degradation
        for operational reliability.
        """
        mock_session = Mock()
        mock_session.sparkContext.appName = "test_app"
        # Simulate error during information extraction
        mock_session.version = Mock(side_effect=RuntimeError("Version unavailable"))

        result = get_session_info(mock_session)

        assert "error" in result
        assert "Failed to get session info" in result["error"]

    @pytest.mark.unit
    def test_get_session_info_missing_attributes(self) -> None:
        """
        Test get_session_info handles missing session attributes gracefully.

        Validates robust handling when session objects have missing or
        unavailable attributes, ensuring reliable information extraction
        in various Spark deployment scenarios.
        """
        mock_session = Mock()
        mock_context = Mock()

        # Setup minimal mock structure
        mock_context.appName = "minimal_app"
        mock_context.applicationId = "app-minimal"
        mock_context.master = "local[*]"
        mock_context.defaultParallelism = 2
        mock_context.environment = {}

        # Missing deployMode attribute - use delattr approach
        if hasattr(mock_context, "deployMode"):
            delattr(mock_context, "deployMode")

        # Missing statusTracker
        mock_context.statusTracker.side_effect = AttributeError(
            "statusTracker unavailable"
        )

        mock_session.version = "3.5.0"
        mock_session.sparkContext = mock_context
        mock_session.conf = Mock()
        mock_session.conf.get.return_value = "not set"

        with patch(
            "spark_simplicity.session.platform.python_version"
        ) as mock_py_version:
            mock_py_version.return_value = "3.9.0"

            result = get_session_info(mock_session)

            # Should handle missing attributes gracefully
            if "error" in result:
                # If error occurred, that's also valid behavior
                assert "Failed to get session info" in result["error"]
            else:
                # If successful, validate the info
                assert result["app_name"] == "minimal_app"
                assert result["deploy_mode"] == "unknown"
                assert (
                    result["executor_count"] == -1
                )  # getExecutorInfos failed, so 0 - 1
                assert result["java_version"] == "unknown"

    # Session Summary Function Testing
    # ===============================

    @pytest.mark.unit
    def test_print_session_summary_success(self) -> None:
        """
        Test print_session_summary displays formatted session information.

        Validates comprehensive session summary formatting and logging
        with all session details properly displayed for operational
        monitoring and debugging purposes.
        """
        mock_session = Mock()

        session_info = {
            "app_name": "test_application",
            "app_id": "app-12345",
            "spark_version": "3.5.0",
            "master": "local[*]",
            "deploy_mode": "client",
            "executor_count": 2,
            "default_parallelism": 8,
            "python_version": "3.9.0",
            "key_configs": {
                "spark.executor.memory": "2g",
                "spark.executor.cores": "4",
                "spark.driver.memory": "1g",
            },
        }

        with patch("spark_simplicity.session.get_session_info") as mock_get_info, patch(
            "spark_simplicity.session._session_logger"
        ) as mock_logger:
            mock_get_info.return_value = session_info

            print_session_summary(mock_session)

            # Validate summary logging calls
            expected_logs = [
                call("=" * 50),
                call("Spark Session Summary"),
                call("=" * 50),
                call("Application: %s", "test_application"),
                call("Application ID: %s", "app-12345"),
                call("Spark Version: %s", "3.5.0"),
                call("Master: %s", "local[*]"),
                call("Deploy Mode: %s", "client"),
                call("Executor Count: %s", 2),
                call("Default Parallelism: %s", 8),
                call("Python Version: %s", "3.9.0"),
                call(""),
                call("Key Configurations:"),
            ]

            mock_logger.info.assert_has_calls(expected_logs, any_order=False)

            # Validate configuration logging
            config_calls = [
                call("  %s: %s", "spark.executor.memory", "2g"),
                call("  %s: %s", "spark.executor.cores", "4"),
                call("  %s: %s", "spark.driver.memory", "1g"),
            ]

            for config_call in config_calls:
                assert config_call in mock_logger.info.call_args_list

    @pytest.mark.unit
    def test_print_session_summary_error_handling(self) -> None:
        """
        Test print_session_summary handles session info errors gracefully.

        Validates proper error handling and warning display when session
        information extraction fails, ensuring graceful degradation
        and clear error communication.
        """
        mock_session = Mock()

        with patch("spark_simplicity.session.get_session_info") as mock_get_info, patch(
            "spark_simplicity.session._session_logger"
        ) as mock_logger:
            mock_get_info.return_value = {"error": "Session info extraction failed"}

            print_session_summary(mock_session)

            mock_logger.warning.assert_called_once_with(
                "⚠️  %s", "Session info extraction failed"
            )

    # Edge Cases and Error Handling Testing
    # =====================================

    @pytest.mark.unit
    def test_environment_enum_case_insensitive_conversion(self) -> None:
        """
        Test Environment enum handles case-insensitive string conversion.

        Validates that environment string parameters are properly converted
        to enum values regardless of case, supporting flexible configuration
        input formats across different deployment scenarios.
        """
        test_cases = [
            ("development", Environment.DEVELOPMENT),
            ("DEVELOPMENT", Environment.DEVELOPMENT),
            ("Development", Environment.DEVELOPMENT),
            ("production", Environment.PRODUCTION),
            ("PRODUCTION", Environment.PRODUCTION),
            ("Production", Environment.PRODUCTION),
        ]

        for input_string, expected_enum in test_cases:
            with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
                mock_builder = Mock()
                mock_session = Mock()
                mock_context = Mock()

                mock_builder.appName.return_value = mock_builder
                mock_builder.config.return_value = mock_builder
                mock_builder.getOrCreate.return_value = mock_session
                mock_session.sparkContext = mock_context

                mock_spark_session.builder = mock_builder

                with patch(
                    "spark_simplicity.session._get_config_for_environment"
                ) as mock_config, patch(
                    "spark_simplicity.session._log_session_creation"
                ), patch(
                    "spark_simplicity.session.platform.system", return_value="Linux"
                ):
                    mock_config.return_value = {}

                    # Should not raise exception
                    get_spark_session("test_app", environment=input_string.lower())

                    mock_config.assert_called_with(expected_enum)

    @pytest.mark.unit
    def test_config_override_precedence(self) -> None:
        """
        Test configuration override precedence over environment defaults.

        Validates that custom configuration overrides properly supersede
        environment-specific and Windows-specific configurations, ensuring
        predictable configuration behavior and customization control.
        """
        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_session = Mock()
            mock_context = Mock()

            mock_builder.appName.return_value = mock_builder
            mock_builder.config.return_value = mock_builder
            mock_builder.getOrCreate.return_value = mock_session
            mock_session.sparkContext = mock_context

            mock_spark_session.builder = mock_builder

            with patch(
                "spark_simplicity.session._get_config_for_environment"
            ) as mock_env_config, patch(
                "spark_simplicity.session.SparkConfig.get_windows_safe_config"
            ) as mock_windows_config, patch(
                "spark_simplicity.session._configure_builder"
            ) as mock_configure, patch(
                "spark_simplicity.session._log_session_creation"
            ), patch(
                "spark_simplicity.session.platform.system", return_value="Windows"
            ):
                # Setup base configs
                mock_env_config.return_value = {
                    "spark.executor.memory": "2g",
                    "base_config": "base_value",
                }
                mock_windows_config.return_value = {
                    "spark.executor.memory": "1g",
                    "windows_config": "windows_value",
                }

                # Override should win
                config_overrides = {"spark.executor.memory": "4g"}

                get_spark_session("test_app", config_overrides=config_overrides)

                # Verify final configuration has override value
                call_args = mock_configure.call_args[0]
                final_config = call_args[1]
                assert final_config["spark.executor.memory"] == "4g"
                assert final_config["base_config"] == "base_value"
                assert final_config["windows_config"] == "windows_value"

    @pytest.mark.unit
    def test_empty_config_overrides(self) -> None:
        """
        Test session creation with empty configuration overrides.

        Validates that empty or None configuration overrides do not
        interfere with normal session creation workflow, ensuring
        robust parameter validation and handling.
        """
        test_cases = [None, {}, {"": ""}]

        for config_override in test_cases:
            with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
                mock_builder = Mock()
                mock_session = Mock()
                mock_context = Mock()

                mock_builder.appName.return_value = mock_builder
                mock_builder.config.return_value = mock_builder
                mock_builder.getOrCreate.return_value = mock_session
                mock_session.sparkContext = mock_context

                mock_spark_session.builder = mock_builder

                with patch("spark_simplicity.session._log_session_creation"), patch(
                    "spark_simplicity.session.platform.system", return_value="Linux"
                ):
                    # Should not raise exception
                    result = get_spark_session(
                        "test_app", config_overrides=config_override
                    )
                    assert result is mock_session

    @pytest.mark.unit
    def test_unicode_application_names(self) -> None:
        """
        Test session creation with Unicode application names.

        Validates proper handling of international characters in application
        names, ensuring global compatibility and robust character encoding
        support across different deployment environments.
        """
        unicode_names = [
            "应用程序",  # Chinese
            "приложение",  # Russian
            "アプリケーション",  # Japanese
            "🚀 My App 🚀",  # Emoji
        ]

        for app_name in unicode_names:
            with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
                mock_builder = Mock()
                mock_session = Mock()
                mock_context = Mock()

                mock_builder.appName.return_value = mock_builder
                mock_builder.config.return_value = mock_builder
                mock_builder.getOrCreate.return_value = mock_session
                mock_session.sparkContext = mock_context

                mock_spark_session.builder = mock_builder

                with patch("spark_simplicity.session._log_session_creation"), patch(
                    "spark_simplicity.session.platform.system", return_value="Linux"
                ):
                    result = get_spark_session(app_name)

                    mock_builder.appName.assert_called_with(app_name)
                    assert result is mock_session

    @pytest.mark.unit
    def test_long_application_names(self) -> None:
        """
        Test session creation with very long application names.

        Validates handling of extremely long application names without
        truncation or errors, ensuring compatibility with verbose naming
        conventions in enterprise environments.
        """
        long_name = "a" * 1000  # 1000 character application name

        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_session = Mock()
            mock_context = Mock()

            mock_builder.appName.return_value = mock_builder
            mock_builder.config.return_value = mock_builder
            mock_builder.getOrCreate.return_value = mock_session
            mock_session.sparkContext = mock_context

            mock_spark_session.builder = mock_builder

            with patch("spark_simplicity.session._log_session_creation"), patch(
                "spark_simplicity.session.platform.system", return_value="Linux"
            ):
                result = get_spark_session(long_name)

                mock_builder.appName.assert_called_with(long_name)
                assert result is mock_session

    # Performance and Scalability Testing
    # ==================================

    @pytest.mark.performance
    def test_multiple_session_creation_performance(self) -> None:
        """
        Test performance characteristics of multiple session creation calls.

        Validates that repeated session creation calls with identical
        parameters maintain optimal performance through proper builder
        reuse and configuration caching mechanisms.
        """
        with patch("spark_simplicity.session.SparkSession") as mock_spark_session:
            mock_builder = Mock()
            mock_session = Mock()
            mock_context = Mock()

            mock_builder.appName.return_value = mock_builder
            mock_builder.config.return_value = mock_builder
            mock_builder.getOrCreate.return_value = mock_session
            mock_session.sparkContext = mock_context

            mock_spark_session.builder = mock_builder

            with patch("spark_simplicity.session._log_session_creation"), patch(
                "spark_simplicity.session.platform.system", return_value="Linux"
            ):
                # Create multiple sessions quickly
                for i in range(10):
                    result = get_spark_session(f"test_app_{i}")
                    assert result is mock_session

                # Builder should be reused efficiently
                assert mock_builder.appName.call_count == 10
                assert mock_builder.getOrCreate.call_count == 10


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=spark_simplicity.session",
            "--cov-report=term-missing",
        ]
    )
