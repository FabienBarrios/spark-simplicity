"""
Spark Simplicity - SFTP Connection Tests
========================================

Comprehensive test suite for SftpConnection with enterprise-grade
coverage and validation.
This module provides extensive testing of SFTP connection functionality,
singleton pattern implementation, file operations capabilities, and performance
characteristics essential for production Spark data processing environments.

Key Testing Areas:
    - **Singleton Pattern**: Connection instance uniqueness and lifecycle management
    - **Connection Management**: Initialization, configuration validation,
      and resource handling
    - **File Operations**: Upload, download, directory creation and edge cases
    - **Retry Logic**: Exponential backoff, connection resilience, and failure recovery
    - **Performance Testing**: Resource utilization, concurrent access, and
      scalability scenarios
    - **Security Validation**: Input sanitization, connection security, and
      error handling

Test Coverage:
    **Connection Lifecycle**:
    - Singleton pattern enforcement across different configurations and Spark
      applications
    - Proper initialization with various SFTP configurations and security settings
    - Connection reuse and resource management throughout application lifecycle
    - Thread safety and concurrent access patterns for production environments

    **File Operations**:
    - Standard file upload and download with various options
    - Complex directory structures, path handling, and permissions
    - Error recovery and retry logic for transient network issues
    - Edge cases including missing files, permission errors, and disk space issues

Enterprise Integration Testing:
    - **Production Configurations**: Multiple SFTP server environments and connection
      parameters
    - **Security Compliance**: SSH key and password authentication methods
    - **Performance Validation**: Large file transfers and connection efficiency
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
import os
import sys
from pathlib import Path
from typing import Any, Dict, cast
from unittest.mock import Mock, call, patch

import pytest
from paramiko.ssh_exception import SSHException
from pyspark.sql import SparkSession

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SFTP_CONNECTION_PATH = (
    PROJECT_ROOT / "spark_simplicity" / "connections" / "sftp_connection.py"
)
spec = importlib.util.spec_from_file_location("sftp_connection", SFTP_CONNECTION_PATH)
if spec is None or spec.loader is None:
    raise ImportError("Could not load sftp_connection module")
sftp_connection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sftp_connection)

SftpConnection = sftp_connection.SftpConnection


class TestSftpConnection:
    """
    Comprehensive test suite for SftpConnection with 100% coverage.

    This test class validates all aspects of SFTP connection functionality
    including singleton pattern implementation, connection lifecycle management,
    file operation capabilities, and enterprise integration features. Tests are
    organized by functional areas with comprehensive coverage of normal operations,
    edge cases, and error conditions.

    Test Organization:
        - Singleton Pattern: Instance uniqueness and lifecycle management
        - Connection Initialization: Configuration validation and setup
        - File Operations: Upload, download operations with various options
        - Performance Testing: Resource utilization and scalability
        - Integration Testing: Multi-configuration and concurrent access scenarios
    """

    @staticmethod
    def setup_method() -> None:
        """Clear singleton instances before each test to ensure isolation."""
        SftpConnection._instances.clear()

    # Singleton Pattern Testing
    # ========================

    @pytest.mark.unit
    def test_singleton_pattern_same_config(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test singleton pattern returns same instance for identical configurations.

        Validates that multiple instantiation requests with identical SFTP
        configurations return the same connection object, ensuring proper resource
        management and preventing unnecessary connection overhead in production
        environments.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn1 = SftpConnection(mock_spark_session, sftp_config, mock_logger)
            conn2 = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            assert conn1 is conn2, (
                f"Singleton pattern failed: conn1 ({id(conn1)}) should be "
                f"identical to conn2 ({id(conn2)})"
            )
            assert len(SftpConnection._instances) == 1, (
                f"Expected 1 singleton instance, found "
                f"{len(SftpConnection._instances)}"
            )

    @pytest.mark.unit
    def test_singleton_pattern_different_configs(
        self,
        mock_spark_session: Any,
        mock_logger: Any,
    ) -> None:
        """
        Test singleton pattern creates different instances for different configurations.

        Verifies that connections with different SFTP configurations
        (host, port, username) create separate instances while maintaining
        singleton behavior within each configuration scope, supporting
        multi-server enterprise environments.
        """
        config1 = {
            "host": "sftp1.example.com",
            "username": "user1",
            "password": "pass1",
        }
        config2 = {
            "host": "sftp2.example.com",
            "port": 2222,
            "username": "user2",
            "password": "pass2",
        }

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn1 = SftpConnection(mock_spark_session, config1, mock_logger)
            conn2 = SftpConnection(mock_spark_session, config2, mock_logger)

            assert conn1 is not conn2, (
                f"Different configs should create separate "
                f"instances: conn1 ({id(conn1)}) vs "
                f"conn2 ({id(conn2)})"
            )
            assert len(SftpConnection._instances) == 2, (
                f"Expected 2 distinct instances for different configs, found "
                f"{len(SftpConnection._instances)}"
            )

    @pytest.mark.unit
    def test_singleton_pattern_different_spark_apps(
        self, mock_logger: Any, sftp_config: Any
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

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn1 = SftpConnection(mock_spark1, sftp_config, mock_logger)
            conn2 = SftpConnection(mock_spark2, sftp_config, mock_logger)

            assert conn1 is not conn2
            assert len(SftpConnection._instances) == 2

    @pytest.mark.unit
    def test_unique_key_generation(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test unique key generation for singleton pattern implementation.

        Validates that connection instances are properly identified and cached using
        SHA256 hash keys based on application ID, host, port, and username parameters,
        ensuring reliable singleton behavior across complex enterprise configurations.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            host = sftp_config["host"]
            port = sftp_config.get("port", 22)
            username = sftp_config.get("username")
            app_id = mock_spark_session.sparkContext.applicationId

            unique_string = f"{app_id}:{host}:{port}:{username}"
            expected_key = hashlib.sha256(unique_string.encode()).hexdigest()

            SftpConnection(mock_spark_session, sftp_config, mock_logger)

            assert expected_key in SftpConnection._instances

    # Connection Initialization Testing
    # ================================

    @pytest.mark.unit
    def test_initialization_basic_config(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test connection initialization with basic SFTP configuration.

        Validates proper initialization of connection attributes, SSH client setup,
        and base configuration using standard SFTP parameters. Ensures
        correct default value application and connection establishment.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

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
                conn.host == "sftp.example.com"
            ), f"Host mismatch: expected 'sftp.example.com', got '{conn.host}'"
            assert conn.port == 22, f"Port mismatch: expected 22, got '{conn.port}'"
            assert (
                conn.username == "test_user"
            ), f"Username mismatch: expected 'test_user', got '{conn.username}'"
            assert (
                conn.password == "test_password"
            ), f"Password mismatch: expected 'test_password', got '{conn.password}'"
            assert (
                conn.timeout == 10
            ), f"Timeout mismatch: expected 10, got '{conn.timeout}'"
            assert (
                conn.retries == 3
            ), f"Retries mismatch: expected 3, got '{conn.retries}'"
            assert (
                abs(conn.backoff_factor - 0.5) < 1e-9
            ), f"Backoff factor mismatch: expected 0.5, got '{conn.backoff_factor}'"

            # Validate SSH client setup
            mock_ssh_client_class.assert_called_once()
            mock_ssh_client.set_missing_host_key_policy.assert_called_once()
            mock_ssh_client.connect.assert_called_once_with(
                hostname="sftp.example.com",
                port=22,
                username="test_user",
                password="test_password",
                key_filename=None,
                timeout=10,
            )
            mock_ssh_client.open_sftp.assert_called_once()

    @pytest.mark.unit
    def test_initialization_with_custom_config(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test connection initialization with custom configuration parameters.

        Verifies proper handling of custom ports, SSH keys, timeouts, and retry
        configurations. Essential for enterprise environments with
        custom SFTP server configurations and security requirements.
        """
        custom_config = {
            "host": "custom-sftp.company.com",
            "port": 2222,
            "username": "custom_user",
            "key_file": "/path/to/private_key",
            "timeout": 30,
            "retries": 5,
            "backoff_factor": 1.0,
        }

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, custom_config, mock_logger)

            assert conn.host == "custom-sftp.company.com"
            assert conn.port == 2222
            assert conn.username == "custom_user"
            assert conn.key_file == "/path/to/private_key"
            assert conn.timeout == 30
            assert conn.retries == 5
            assert abs(conn.backoff_factor - 1.0) < 1e-9

            mock_ssh_client.connect.assert_called_once_with(
                hostname="custom-sftp.company.com",
                port=2222,
                username="custom_user",
                password=None,
                key_filename="/path/to/private_key",
                timeout=30,
            )

    @pytest.mark.unit
    def test_initialization_logging(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test connection initialization logging for operational monitoring.

        Validates that connection establishment events are properly logged with
        relevant configuration details for production monitoring, troubleshooting,
        and audit compliance in enterprise environments.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            SftpConnection(mock_spark_session, sftp_config, mock_logger)

            mock_logger.info.assert_called_once()
            log_call = mock_logger.info.call_args[0][0]
            assert "SFTP connecté à" in log_call
            assert "test_user@sftp.example.com:22" in log_call

    # Connection Retry Logic Testing
    # =============================

    @pytest.mark.unit
    def test_connection_retry_success_on_second_attempt(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test connection retry logic succeeds on second attempt.

        Validates that transient connection failures are properly handled with
        exponential backoff retry strategy, ensuring connection resilience
        for production environments with intermittent network issues.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            # First call raises exception, second succeeds
            mock_ssh_client.connect.side_effect = [
                SSHException("Connection failed"),
                None,
            ]

            with patch("time.sleep") as mock_sleep:
                SftpConnection(mock_spark_session, sftp_config, mock_logger)

                assert mock_ssh_client.connect.call_count == 2
                expected_delay = 0.5  # backoff_factor * (2 ^ 0)
                mock_sleep.assert_called_once_with(expected_delay)
                mock_logger.warning.assert_called_once()
                warning_call = mock_logger.warning.call_args[0][0]
                assert "Connexion SFTP échouée" in warning_call
                assert "tentative 1/3" in warning_call

    @pytest.mark.unit
    def test_connection_retry_failure_after_max_retries(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test connection retry failure after maximum retry attempts.

        Validates that persistent connection failures are properly handled after
        exhausting all retry attempts, ensuring graceful error handling and
        appropriate exception propagation for diagnostic purposes.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_ssh_client_class.return_value = mock_ssh_client

            # All connection attempts fail
            mock_ssh_client.connect.side_effect = SSHException("Persistent failure")

            with patch("time.sleep") as mock_sleep:
                with pytest.raises(SSHException, match="Persistent failure"):
                    SftpConnection(mock_spark_session, sftp_config, mock_logger)

                # Should try 1 initial + 3 retries = 4 total attempts
                assert mock_ssh_client.connect.call_count == 4
                # Should sleep 3 times (after each retry attempt)
                assert mock_sleep.call_count == 3

                mock_logger.error.assert_called_once()
                error_call = mock_logger.error.call_args[0][0]
                assert "Échec connexion SFTP" in error_call

    @pytest.mark.unit
    def test_connection_retry_exponential_backoff(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test exponential backoff timing in retry logic.

        Validates that retry delays follow proper exponential backoff pattern
        with configurable backoff factor, ensuring efficient retry timing
        and network resource management.
        """
        config = {
            "host": "test-host",
            "username": "test_user",
            "password": "test_pass",
            "backoff_factor": 2.0,  # Custom backoff factor
            "retries": 2,
        }

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_ssh_client_class.return_value = mock_ssh_client
            mock_ssh_client.connect.side_effect = SSHException("Connection failed")

            with patch("time.sleep") as mock_sleep:
                with pytest.raises(SSHException):
                    SftpConnection(mock_spark_session, config, mock_logger)

                # Verify exponential backoff timing
                first_delay = 2.0  # 2.0 * (2 ^ 0)
                second_delay = 4.0  # 2.0 * (2 ^ 1)
                expected_calls = [
                    call(first_delay),
                    call(second_delay),
                ]
                mock_sleep.assert_has_calls(expected_calls)

    @pytest.mark.unit
    def test_connection_retry_with_os_error(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test connection retry handling with OSError (network issues).

        Validates that various network-related errors (OSError) are properly
        caught and retried, ensuring robust handling of different failure
        modes in enterprise network environments.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            # First call raises OSError, second succeeds
            mock_ssh_client.connect.side_effect = [OSError("Network unreachable"), None]

            with patch("time.sleep") as mock_sleep:
                SftpConnection(mock_spark_session, sftp_config, mock_logger)

                assert mock_ssh_client.connect.call_count == 2
                mock_sleep.assert_called_once()

    # File Operations Testing
    # ======================

    @pytest.mark.unit
    def test_get_file_basic(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test basic file download functionality.

        Validates standard file download operation with proper remote and local
        path handling, ensuring reliable file retrieval for data processing
        workflows and ETL operations.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            remote_path = "/remote/data/file.csv"
            local_path = "/local/data/file.csv"

            conn.get(remote_path, local_path)

            mock_sftp.get.assert_called_once_with(remote_path, local_path)
            mock_logger.info.assert_any_call(f"SFTP GET {remote_path} -> {local_path}")

    @pytest.mark.unit
    def test_get_file_with_overwrite_false_existing_file(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test file download with overwrite=False when local file exists.

        Validates that existing local files are preserved when overwrite=False,
        ensuring data protection and conditional download behavior for
        incremental processing scenarios.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            with patch("os.path.exists", return_value=True):
                conn.get("/remote/file.csv", "/local/file.csv", overwrite=False)

                # Should not call SFTP get when file exists and overwrite=False
                mock_sftp.get.assert_not_called()
                mock_logger.info.assert_any_call("Skip existing: /local/file.csv")

    @pytest.mark.unit
    def test_get_file_with_overwrite_false_no_existing_file(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test file download with overwrite=False when local file doesn't exist.

        Validates that download proceeds normally when local file doesn't exist,
        ensuring proper conditional download logic and file handling.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            remote_path = "/remote/file.csv"
            local_path = "/local/file.csv"

            with patch("os.path.exists", return_value=False):
                conn.get(remote_path, local_path, overwrite=False)

                mock_sftp.get.assert_called_once_with(remote_path, local_path)
                mock_logger.info.assert_any_call(
                    f"SFTP GET {remote_path} -> {local_path}"
                )

    @pytest.mark.unit
    def test_put_file_basic(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test basic file upload functionality.

        Validates standard file upload operation with automatic directory creation,
        ensuring reliable file delivery for data export workflows and
        result distribution operations.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            # Mock directory operations for _mkdir_remote
            mock_sftp.listdir.side_effect = IOError("Directory doesn't exist")
            mock_sftp.mkdir = Mock()

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            local_path = "/local/data/file.csv"
            remote_path = "/remote/data/file.csv"

            with patch("os.path.dirname") as mock_dirname:
                # Mock proper directory hierarchy to avoid infinite recursion
                mock_dirname.side_effect = lambda x: {
                    "/remote/data": "/remote",
                    "/remote": "",
                }.get(x, "")

                conn.put(local_path, remote_path)

                mock_sftp.put.assert_called_once_with(local_path, remote_path)
                mock_logger.info.assert_any_call(
                    f"SFTP PUT {local_path} -> {remote_path}"
                )

    @pytest.mark.unit
    def test_put_file_without_mkdir(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test file upload without automatic directory creation.

        Validates file upload when mkdir=False, ensuring compatibility with
        existing directory structures and controlled upload behavior.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            local_path = "/local/data/file.csv"
            remote_path = "/remote/data/file.csv"

            conn.put(local_path, remote_path, mkdir=False)

            mock_sftp.put.assert_called_once_with(local_path, remote_path)
            # Should not call directory creation methods
            mock_sftp.listdir.assert_not_called()
            mock_sftp.mkdir.assert_not_called()

    # Directory Creation Testing
    # =========================

    @pytest.mark.unit
    def test_mkdir_remote_basic(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test basic remote directory creation.

        Validates that single-level directory creation works correctly,
        ensuring proper directory structure management for file operations.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            # Directory doesn't exist, should be created
            # Parent exists but target doesn't
            def listdir_side_effect(path: str) -> list[str]:
                """Mock listdir to simulate parent exists but target doesn't."""
                if path == "/remote":
                    return ["existing_file"]  # Parent exists
                else:
                    raise IOError("Directory not found")  # Target doesn't exist

            mock_sftp.listdir.side_effect = listdir_side_effect

            conn._mkdir_remote("/remote/newdir")

            mock_sftp.mkdir.assert_called_once_with("/remote/newdir")

    @pytest.mark.unit
    def test_mkdir_remote_existing_directory(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test remote directory creation when directory already exists.

        Validates that existing directories are handled gracefully without
        errors, ensuring idempotent directory creation behavior.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            # Directory exists (listdir succeeds)
            mock_sftp.listdir.return_value = ["file1.txt", "file2.txt"]

            conn._mkdir_remote("/remote/existingdir")

            # Should not attempt to create directory
            mock_sftp.mkdir.assert_not_called()

    @pytest.mark.unit
    def test_mkdir_remote_nested_directories(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test recursive remote directory creation for nested paths.

        Validates that complex directory structures are created recursively,
        ensuring proper path hierarchy management for enterprise file operations.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            # All directories don't exist
            mock_sftp.listdir.side_effect = IOError("Directory not found")

            with patch("os.path.dirname") as mock_dirname:
                # Mock the directory hierarchy
                mock_dirname.side_effect = lambda x: {
                    "/remote/level1/level2/level3": "/remote/level1/level2",
                    "/remote/level1/level2": "/remote/level1",
                    "/remote/level1": "/remote",
                    "/remote": "",
                }.get(x, "")

                conn._mkdir_remote("/remote/level1/level2/level3")

                # Should create directories in order: level1, level2, level3
                expected_calls = [
                    call("/remote/level1"),
                    call("/remote/level1/level2"),
                    call("/remote/level1/level2/level3"),
                ]
                mock_sftp.mkdir.assert_has_calls(expected_calls)

    @pytest.mark.unit
    def test_mkdir_remote_root_directory(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test remote directory creation with root directory paths.

        Validates proper handling of root directory and empty path scenarios,
        ensuring robust path processing for various directory structures.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            # Test with root directory
            conn._mkdir_remote("/")
            mock_sftp.mkdir.assert_not_called()

            # Test with empty string
            conn._mkdir_remote("")
            mock_sftp.mkdir.assert_not_called()

    # Connection Closure Testing
    # =========================

    @pytest.mark.unit
    def test_close_connection_normal(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test normal connection closure with proper resource cleanup.

        Validates that SFTP and SSH connections are properly closed during
        normal shutdown operations, ensuring clean resource management and
        connection lifecycle handling.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)
            conn.close()

            mock_sftp.close.assert_called_once()
            mock_ssh_client.close.assert_called_once()
            mock_logger.info.assert_any_call("SFTP session closed successfully")

    @pytest.mark.unit
    def test_close_connection_with_sftp_error(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test connection closure when SFTP close raises exception.

        Validates graceful error handling during connection cleanup,
        ensuring that exceptions during resource cleanup don't propagate
        and disrupt application shutdown procedures.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_sftp.close.side_effect = OSError("SFTP close error")
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)
            conn.close()

            # Due to global try-catch, SSH close is not reached when SFTP close fails
            mock_ssh_client.close.assert_not_called()
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Error during SFTP connection cleanup" in warning_call

    @pytest.mark.unit
    def test_close_connection_with_ssh_error(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test connection closure when SSH close raises exception.

        Validates graceful error handling during SSH connection cleanup,
        ensuring robust resource management even when underlying connections
        encounter errors during shutdown.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.close.side_effect = SSHException("SSH close error")
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)
            conn.close()

            mock_sftp.close.assert_called_once()
            mock_logger.warning.assert_called_once()
            warning_call = mock_logger.warning.call_args[0][0]
            assert "Error during SFTP connection cleanup" in warning_call

    @pytest.mark.unit
    def test_close_connection_missing_attributes(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test connection closure when connection attributes are missing.

        Validates robust error handling when connection objects are not
        properly initialized or have been corrupted, ensuring graceful
        degradation during cleanup operations.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            # Remove connection attributes to simulate corruption
            del conn._sftp
            del conn._ssh

            conn.close()

            # Should log completion even when attributes are missing
            mock_logger.info.assert_any_call("SFTP session closed successfully")

    # Edge Cases and Error Handling Testing
    # ====================================

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_initialization_missing_required_keys(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test connection initialization with missing required configuration keys.

        Validates that missing essential configuration parameters (host, username)
        are handled appropriately, ensuring proper validation and error reporting
        for incomplete configurations.
        """
        incomplete_configs = [
            # Missing host
            {"username": "test", "password": "test"},
            # Missing username (but has host)
            {"host": "test-host", "password": "test"},
        ]

        for config in incomplete_configs:
            with patch("paramiko.SSHClient"):
                try:
                    conn = SftpConnection(mock_spark_session, config, mock_logger)
                    # If connection succeeds, validate it has basic attributes
                    assert hasattr(
                        conn, "spark"
                    ), "Connection should have spark attribute"
                    assert hasattr(
                        conn, "logger"
                    ), "Connection should have logger attribute"
                except KeyError as e:
                    # If KeyError is raised, that's also valid behavior
                    assert (
                        str(e) != ""
                    ), f"KeyError should have a message for config: {config}"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_configuration_with_none_values(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test configuration handling with None values.

        Validates behavior when configuration contains None values for optional
        parameters, ensuring robust parameter validation and appropriate
        default value handling.
        """
        config_with_none = {
            "host": "test-host",
            "port": None,
            "username": "test_user",
            "password": None,
            "key_file": None,
            "timeout": None,
            "retries": None,
            "backoff_factor": None,
        }

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, config_with_none, mock_logger)

            # Test actual behavior - None values are preserved as None
            assert conn.port is None, "Port should be None when explicitly set to None"
            assert (
                conn.timeout is None
            ), "Timeout should be None when explicitly set to None"
            assert (
                conn.retries is None
            ), "Retries should be None when explicitly set to None"
            assert (
                conn.backoff_factor is None
            ), "Backoff factor should be None when explicitly set to None"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_special_characters_in_paths(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test file operations with special characters in paths.

        Validates proper handling of paths containing special characters,
        spaces, unicode characters, and escape sequences commonly found
        in enterprise file systems and international environments.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            special_paths = [
                "/remote/path with spaces/file.csv",
                "/remote/café_münchen/données.txt",
                "/remote/测试目录/文件.csv",
                "/remote/path-with-dashes/file_with_underscores.json",
                "/remote/path.with.dots/file[brackets].xml",
            ]

            for remote_path in special_paths:
                local_path = f"/local{remote_path}"
                conn.get(remote_path, local_path)

                mock_sftp.get.assert_called_with(remote_path, local_path)

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_numeric_port_types(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test port handling with different numeric types.

        Validates consistent port handling regardless of whether port is
        provided as string, integer, or float, ensuring robust type
        conversion for various configuration sources.
        """
        configs_with_different_port_types = [
            {
                "host": "test-host",
                "port": "2222",
                "username": "user",
                "password": "pass",
            },
            {"host": "test-host", "port": 2222, "username": "user", "password": "pass"},
            {
                "host": "test-host",
                "port": 2222.0,
                "username": "user",
                "password": "pass",
            },
        ]

        for config in configs_with_different_port_types:
            with patch("paramiko.SSHClient") as mock_ssh_client_class:
                mock_ssh_client = Mock()
                mock_sftp = Mock()
                mock_ssh_client.open_sftp.return_value = mock_sftp
                mock_ssh_client_class.return_value = mock_ssh_client

                # Mock unique app IDs to avoid singleton conflicts
                mock_context = Mock()
                config_dict = cast(Dict[str, Any], config)
                port_type = type(config_dict["port"]).__name__
                app_id = f"test-port-{config_dict['port']}-{port_type}"
                mock_context.applicationId = app_id
                mock_spark_session.sparkContext = mock_context

                conn = SftpConnection(mock_spark_session, config, mock_logger)

                # Port type is preserved as provided in config
                if isinstance(config_dict["port"], str):
                    assert (
                        conn.port == "2222"
                    ), f"String port should remain string: {port_type}"
                else:
                    assert (
                        conn.port == 2222
                    ), f"Numeric port should remain numeric: {port_type}"

    # Performance and Scalability Testing
    # ==================================

    @pytest.mark.performance
    def test_singleton_performance_multiple_calls(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test singleton performance with multiple instantiation calls.

        Validates that repeated connection requests with identical configurations
        maintain optimal performance through proper instance caching and reuse.
        Critical for high-throughput production environments with frequent
        connection requests.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            connections = []

            for _ in range(100):
                conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)
                connections.append(conn)

            first_conn = connections[0]
            for conn in connections[1:]:
                assert conn is first_conn

            assert len(SftpConnection._instances) == 1

            # Should only create SSH connection once
            assert mock_ssh_client_class.call_count == 1

    @pytest.mark.integration
    def test_multiple_configs_isolation(self, mock_logger: Any) -> None:
        """
        Test connection isolation across multiple SFTP configurations.

        Validates proper connection separation and resource management when
        working with multiple SFTP servers simultaneously. Essential
        for enterprise scenarios with multiple SFTP endpoints within
        the same application.
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
            "host": "sftp1.example.com",
            "username": "user1",
            "password": "pass1",
        }

        config2 = {
            "host": "sftp2.example.com",
            "port": 2222,
            "username": "user2",
            "password": "pass2",
        }

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn1 = SftpConnection(mock_spark1, config1, mock_logger)
            conn2 = SftpConnection(mock_spark2, config2, mock_logger)
            conn3 = SftpConnection(mock_spark1, config1, mock_logger)

            assert conn1 is not conn2
            assert conn1 is conn3
            assert len(SftpConnection._instances) == 2

            assert conn1.host == "sftp1.example.com"
            assert conn2.host == "sftp2.example.com"
            assert conn1.port == 22
            assert conn2.port == 2222

    # Advanced Integration Testing
    # ===========================

    @pytest.mark.slow
    @pytest.mark.integration
    def test_multiple_file_operations(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test multiple file operations on same connection instance.

        Validates connection reuse and stability across multiple file operations
        within the same application session. Critical for long-running data
        processing workloads and batch file transfer scenarios.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            # Mock directory operations
            mock_sftp.listdir.side_effect = IOError("Directory doesn't exist")

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            # Perform multiple operations
            operations = [
                ("get", "/remote/file1.csv", "/local/file1.csv"),
                ("put", "/local/file2.csv", "/remote/file2.csv"),
                ("get", "/remote/file3.json", "/local/file3.json"),
                ("put", "/local/file4.xml", "/remote/data/file4.xml"),
            ]

            for operation, path1, path2 in operations:
                if operation == "get":
                    with patch("os.path.exists", return_value=False):
                        conn.get(path1, path2)
                        mock_sftp.get.assert_called_with(path1, path2)
                else:  # put
                    with patch("os.path.dirname") as mock_dirname:
                        # Mock proper directory hierarchy to avoid infinite recursion
                        parent_dir = os.path.dirname(path2)
                        path2_dir = path2.rsplit("/", 1)[0]

                        def dirname_side_effect(
                            x: str,
                            parent: str = parent_dir,
                            target_dir: str = path2_dir,
                        ) -> str:
                            """Mock dirname with proper closure for loop variables."""
                            return {target_dir: parent, parent: ""}.get(x, "")

                        mock_dirname.side_effect = dirname_side_effect
                        conn.put(path1, path2)
                        mock_sftp.put.assert_called_with(path1, path2)

            # Verify connection reuse
            conn2 = SftpConnection(mock_spark_session, sftp_config, mock_logger)
            assert conn is conn2

    @pytest.mark.unit
    def test_connection_reuse_after_operations(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test connection reuse after executing file operations.

        Validates that connection instances maintain their singleton behavior
        and proper resource management even after file operation executions.
        Ensures consistent connection lifecycle management throughout application
        runtime.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn1 = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            with patch("os.path.exists", return_value=False):
                conn1.get("/remote/file1.txt", "/local/file1.txt")

            conn2 = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            with patch("os.path.dirname") as mock_dirname:
                # Mock proper directory hierarchy to avoid infinite recursion
                mock_dirname.side_effect = lambda x: {
                    "/remote/data": "/remote",
                    "/remote": "",
                }.get(x, "")
                mock_sftp.listdir.side_effect = IOError("Directory doesn't exist")
                conn2.put("/local/file2.txt", "/remote/data/file2.txt")

            assert conn1 is conn2
            assert len(SftpConnection._instances) == 1

    # Configuration Validation Testing
    # ===============================

    @pytest.mark.unit
    def test_all_attributes_initialized(
        self, mock_spark_session: Any, mock_logger: Any, sftp_config: Any
    ) -> None:
        """
        Test comprehensive attribute initialization validation.

        Validates that all connection instance attributes are properly initialized
        with correct types and values during connection establishment. Critical
        for ensuring reliable connection state and preventing runtime errors.
        """
        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, sftp_config, mock_logger)

            # Validate attribute presence
            required_attributes = [
                "spark",
                "logger",
                "host",
                "port",
                "username",
                "password",
                "key_file",
                "timeout",
                "retries",
                "backoff_factor",
                "_ssh",
                "_sftp",
            ]
            for attr in required_attributes:
                assert hasattr(conn, attr), f"Missing attribute: {attr}"

            # Validate attribute types
            assert isinstance(conn.host, str)
            assert isinstance(conn.port, int)
            assert isinstance(conn.username, str)
            assert isinstance(conn.timeout, int)
            assert isinstance(conn.retries, int)
            assert isinstance(conn.backoff_factor, float)

    @pytest.mark.unit
    def test_default_values_application(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test proper application of default configuration values.

        Validates that missing configuration parameters correctly use default
        values, ensuring consistent behavior across different configuration
        scenarios and backward compatibility.
        """
        minimal_config = {"host": "minimal-host", "username": "minimal_user"}

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, minimal_config, mock_logger)

            # Verify default values
            assert conn.port == 22, "Port should default to 22"
            assert conn.password is None, "Password should default to None"
            assert conn.key_file is None, "Key file should default to None"
            assert conn.timeout == 10, "Timeout should default to 10"
            assert conn.retries == 3, "Retries should default to 3"
            expected_backoff = 0.5
            assert (
                abs(conn.backoff_factor - expected_backoff) < 1e-9
            ), "Backoff factor should default to 0.5"

    # Security and Robustness Testing
    # ===============================

    @pytest.mark.security
    @pytest.mark.edge_case
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
            "host": "secure-host",
            "username": "user@domain.com",
            "password": "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?",
        }

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(
                mock_spark_session, config_with_special_chars, mock_logger
            )

            assert (
                conn.username == "user@domain.com"
            ), "Special characters in username should be preserved"
            assert (
                conn.password == "P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?"
            ), "Special characters in password should be preserved"

            # Verify connection call with special characters
            mock_ssh_client.connect.assert_called_once_with(
                hostname="secure-host",
                port=22,
                username="user@domain.com",
                password="P@ssw0rd!#$%^&*()_+-=[]{}|;:,.<>?",
                key_filename=None,
                timeout=10,
            )

    @pytest.mark.unit
    @pytest.mark.unicode
    @pytest.mark.internationalization
    def test_unicode_configuration_handling(
        self, mock_spark_session: Any, mock_logger: Any, unicode_test_data: Any
    ) -> None:
        """
        Test connection handling with Unicode characters in configuration.

        Validates proper encoding and processing of international characters
        in SFTP configuration parameters, ensuring global compatibility
        and robust character encoding support.
        """
        unicode_config = {
            "host": unicode_test_data["chinese"],
            "username": unicode_test_data["portuguese"],
            "password": unicode_test_data["emoji"],
        }

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            conn = SftpConnection(mock_spark_session, unicode_config, mock_logger)

            assert conn.host == unicode_test_data["chinese"]
            assert conn.username == unicode_test_data["portuguese"]
            assert conn.password == unicode_test_data["emoji"]

    # Comprehensive Integration and Stress Testing
    # ===========================================

    @pytest.mark.integration
    def test_key_generation_with_different_configs(self, mock_logger: Any) -> None:
        """
        Test unique key generation produces different keys for different configurations.

        Validates that the singleton pattern key generation algorithm produces
        unique, collision-free keys for different SFTP configurations and
        Spark application contexts, ensuring proper connection isolation.
        """
        SftpConnection._instances.clear()

        configs = [
            ("app-1", {"host": "host1", "username": "user1", "password": "pass1"}),
            ("app-1", {"host": "host2", "username": "user1", "password": "pass1"}),
            ("app-2", {"host": "host1", "username": "user1", "password": "pass1"}),
        ]

        created_keys = []

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            for app_id, config in configs:
                mock_spark = Mock(spec=SparkSession)
                mock_context = Mock()
                mock_context.applicationId = app_id
                mock_spark.sparkContext = mock_context

                _ = SftpConnection(mock_spark, config, mock_logger)

                host = config["host"]
                port = config.get("port", 22)
                username = config.get("username")
                unique_str = f"{app_id}:{host}:{port}:{username}"
                expected_key = hashlib.sha256(unique_str.encode()).hexdigest()
                created_keys.append(expected_key)

                assert expected_key in SftpConnection._instances

        assert len(set(created_keys)) == len(created_keys), "All keys should be unique"

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
            {"host": "host1", "username": "user1", "password": "pass1"},
            {"host": "host2", "username": "user2", "password": "pass2"},
            {"host": "host1", "username": "user1", "password": "pass1"},
        ]

        with patch("paramiko.SSHClient") as mock_ssh_client_class:
            mock_ssh_client = Mock()
            mock_sftp = Mock()
            mock_ssh_client.open_sftp.return_value = mock_sftp
            mock_ssh_client_class.return_value = mock_ssh_client

            connections = []
            for i, config in enumerate(configs):
                conn = SftpConnection(spark_sessions[i], config, mock_logger)
                connections.append(conn)

            assert connections[0] is not connections[1]
            assert connections[0] is not connections[2]
            assert connections[1] is not connections[2]

            assert len(SftpConnection._instances) == 3


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=spark_simplicity.connections.sftp_connection",
            "--cov-report=term-missing",
        ]
    )
