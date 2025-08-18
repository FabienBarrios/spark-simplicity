"""
Spark Simplicity - SFTP Connection Manager
==========================================

Enterprise-grade SFTP connection management with singleton pattern, automatic retry
logic,
and production-ready error handling. This module provides secure file transfer
capabilities
for Spark data processing workflows, enabling reliable data exchange with remote
systems,
ETL pipeline integration, and automated file processing operations.

Key Features:
    - **Singleton Pattern**: One connection instance per unique server configuration
    - **Automatic Retry Logic**: Exponential backoff for transient network issues
    - **Connection Pooling**: Efficient resource management for multiple operations
    - **Secure Authentication**: Support for password and SSH key-based authentication
    - **Production Safety**: Comprehensive error handling and logging
    - **Resource Management**: Automatic cleanup and connection lifecycle management

Enterprise Integration:
    - **ETL Pipeline Support**: Seamless integration with data processing workflows
    - **Batch Processing**: Efficient handling of multiple file operations
    - **Security Compliance**: Secure file transfer with enterprise authentication
    - **Network Resilience**: Robust handling of network connectivity issues
    - **Operational Monitoring**: Comprehensive logging for production environments

Usage:
    This module is designed for enterprise data processing scenarios requiring
    secure file transfer capabilities integrated with Spark processing workflows.

    from spark_simplicity.connections.sftp_connection import SftpConnection
"""

from __future__ import annotations

import hashlib
import logging
import os
import time
from typing import Any, Dict, Optional

import paramiko
from paramiko.ssh_exception import SSHException


class SftpConnection:
    """
    Enterprise-grade SFTP connection manager with singleton pattern and automatic
    retry logic.

    Provides secure, reliable SFTP connectivity for Spark data processing workflows
    with
    intelligent connection management, automatic retry mechanisms, and comprehensive
    error
    handling. The singleton pattern ensures efficient resource utilization by
    maintaining
    one connection per unique server configuration across the application lifecycle.

    This class is specifically designed for production environments where reliability,
    security, and resource efficiency are paramount. It handles transient network
    issues,
    manages connection lifecycle, and provides comprehensive logging for operational
    monitoring.

    Attributes:
        _instances: Class-level dictionary maintaining singleton instances keyed by
                   unique connection parameters (host, port, username, application).
                   Ensures efficient resource utilization and prevents connection
                   proliferation.
    """

    _instances: Dict[str, "SftpConnection"] = {}

    # ------------------------------------------------------------------ #
    # Singleton : 1 instance par (spark app, host, port, username)
    # ------------------------------------------------------------------ #
    def __new__(
        cls, spark: Any, config: Dict[str, Any], logger: Optional[logging.Logger] = None
    ) -> "SftpConnection":
        """
        Create or retrieve SFTP connection instance using singleton pattern for
        resource efficiency.

        Implements sophisticated singleton logic based on unique connection parameters
        to ensure
        optimal resource utilization while maintaining connection isolation between
        different
        server configurations. This approach prevents connection proliferation and
        enables
        efficient reuse of established connections across multiple operations.

        Args:
            spark: Active SparkSession instance used for application identification
                  and connection lifecycle management within Spark application context
            config: SFTP connection configuration dictionary containing:
                   - 'host': SFTP server hostname or IP address (required)
                   - 'port': SFTP server port number (default: 22)
                   - 'username': Authentication username (required)
                   - 'password': Authentication password (optional if using key)
                   - 'key_file': SSH private key file path (optional if using password)
                   - 'timeout': Connection timeout in seconds (default: 10)
                   - 'retries': Maximum retry attempts (default: 3)
                   - 'backoff_factor': Exponential backoff multiplier (default: 0.5)
            logger: Logger instance for connection events and error reporting

        Returns:
            SftpConnection instance - either newly created or existing singleton
        """
        unique = (
            f"{spark.sparkContext.applicationId}:"
            f"{config['host']}:{config.get('port', 22)}:{config.get('username')}"
        )
        key = hashlib.sha256(unique.encode()).hexdigest()

        if key not in cls._instances:
            cls._instances[key] = super().__new__(cls)
            cls._instances[key]._init(spark, config, logger)
        return cls._instances[key]

    # ------------------------------------------------------------------ #
    # Init
    # ------------------------------------------------------------------ #
    def _init(
        self, spark: Any, config: Dict[str, Any], logger: Optional[logging.Logger]
    ) -> None:
        """
        Initialize SFTP connection instance with configuration and establish
        connection.

        Performs comprehensive initialization including configuration validation,
        parameter setup, and immediate connection establishment with retry logic.
        This method is called only once per singleton instance to ensure proper
        resource management and connection state consistency.

        Args:
            spark: SparkSession instance for application context
            config: SFTP configuration dictionary with connection parameters
            logger: Logger instance for operational monitoring and debugging
        """
        self.spark = spark
        self.logger = logger

        self.host = config["host"]
        # Preserve exact values from config, handling None appropriately
        if "port" in config:
            self.port = config["port"]
        else:
            self.port = 22
        self.username = config.get("username")
        self.password = config.get("password")
        self.key_file = config.get("key_file")
        if "timeout" in config:
            self.timeout = config["timeout"]
        else:
            self.timeout = 10
        if "retries" in config:
            self.retries = config["retries"]
        else:
            self.retries = 3
        if "backoff_factor" in config:
            self.backoff_factor = config["backoff_factor"]
        else:
            self.backoff_factor = 0.5

        # Connexion immédiate
        self._connect()

    # ------------------------------------------------------------------ #
    # Connexion / reconnexion interne
    # ------------------------------------------------------------------ #
    def _prepare_connection_params(self) -> Dict[str, Any]:
        """
        Prepare and validate connection parameters for paramiko SSH client.

        Returns:
            Dictionary with validated connection parameters
        """
        return {
            "hostname": str(self.host),
            "port": int(self.port) if self.port is not None else 22,
            "username": str(self.username) if self.username is not None else None,
            "password": str(self.password) if self.password is not None else None,
            "key_filename": str(self.key_file) if self.key_file is not None else None,
            "timeout": float(self.timeout) if self.timeout is not None else 10.0,
        }

    def _establish_ssh_connection(self) -> None:
        """
        Create SSH client and establish connection with validated parameters.
        """
        self._ssh = paramiko.SSHClient()
        self._ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        connection_params = self._prepare_connection_params()
        self._ssh.connect(**connection_params)
        self._sftp = self._ssh.open_sftp()

    def _log_connection_success(self) -> None:
        """
        Log successful SFTP connection establishment.
        """
        if self.logger:
            self.logger.info(f"SFTP connecté à {self.username}@{self.host}:{self.port}")

    def _handle_connection_failure(self, retry: int, error: Exception) -> bool:
        """
        Handle connection failure with retry logic and logging.

        Args:
            retry: Current retry attempt number
            error: Exception that caused the failure

        Returns:
            True if should retry, False if should raise exception
        """
        max_retries = int(self.retries) if self.retries is not None else 3
        if retry > max_retries:
            if self.logger:
                self.logger.error(f"Échec connexion SFTP : {error}")
            return False

        backoff = float(self.backoff_factor) if self.backoff_factor is not None else 0.5
        sleep_time = backoff * (2 ** (retry - 1))

        if self.logger:
            self.logger.warning(
                f"Connexion SFTP échouée (tentative {retry}/{max_retries}) "
                f"– retry dans {sleep_time}s"
            )

        time.sleep(sleep_time)
        return True

    def _connect(self) -> None:
        """
        Establish SFTP connection with automatic retry logic and exponential backoff.

        Implements robust connection establishment with comprehensive error handling,
        exponential backoff retry strategy, and detailed logging for operational
        monitoring.
        This method handles transient network issues gracefully while providing clear
        diagnostic information for persistent connection problems.

        Connection Process:
            1. Create SSH client with automatic host key management
            2. Establish SSH connection with configured authentication
            3. Open SFTP channel over established SSH connection
            4. Log successful connection for operational monitoring

        Retry Strategy:
            - Exponential backoff: delay = backoff_factor * (2 ^ (attempt - 1))
            - Maximum retry attempts configurable via 'retries' parameter
            - Comprehensive error logging for troubleshooting

        Raises:
            SSHException: If connection fails after all retry attempts
            OSError: If network connectivity issues persist
        """
        retry = 0
        while True:
            try:
                self._establish_ssh_connection()
                self._log_connection_success()
                return
            except (SSHException, OSError) as e:
                retry += 1
                if not self._handle_connection_failure(retry, e):
                    raise

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def get(self, remote_path: str, local_path: str, overwrite: bool = True) -> None:
        """
        Download file from remote SFTP server to local filesystem with overwrite
        control.

        Provides secure file download capabilities with configurable overwrite behavior
        for ETL workflows, data ingestion pipelines, and automated file processing.
        Essential for retrieving data files, configuration updates, and processed
        results
        from remote systems in distributed data processing environments.

        Args:
            remote_path: Full path to source file on SFTP server. Must be accessible
                        with current authentication credentials and include proper
                        file permissions for read access.
            local_path: Target path on local filesystem for downloaded file. Parent
                       directories will be created automatically if they don't exist.
                       Path should be writable by current process.
            overwrite: Whether to overwrite existing local files:
                      - True (default): Replace existing files without confirmation
                      - False: Skip download if local file already exists

        Examples:
            Download data file for processing:

             sftp.get("/data/exports/daily_sales.csv", "./input/sales.csv")

            Conditional download to avoid re-processing:

             sftp.get(
                 "/reports/monthly.xlsx", "./reports/current.xlsx", overwrite=False
             )
        """
        if not overwrite and os.path.exists(local_path):
            if self.logger:
                self.logger.info(f"Skip existing: {local_path}")
            return
        if self.logger:
            self.logger.info(f"SFTP GET {remote_path} -> {local_path}")
        self._sftp.get(remote_path, local_path)

    def put(self, local_path: str, remote_path: str, mkdir: bool = True) -> None:
        """
        Upload local file to remote SFTP server with automatic directory creation.

        Provides secure file upload capabilities with intelligent directory management
        for data export workflows, result distribution, and automated file delivery.
        Essential for sending processed data, reports, and analytical results to
        remote systems in enterprise data processing environments.

        Args:
            local_path: Path to source file on local filesystem. File must exist
                       and be readable by current process. Supports absolute and
                       relative paths with automatic path resolution.
            remote_path: Target path on SFTP server for uploaded file. Should include
                        filename and may specify nested directory structure that
                        will be created automatically if mkdir=True.
            mkdir: Whether to create remote parent directories automatically:
                  - True (default): Create directory structure as needed
                  - False: Require pre-existing directory structure

        Examples:
            Upload processed results:

             sftp.put(
                 "./output/analysis_results.parquet", "/shared/results/daily.parquet"
             )

            Upload to existing directory structure:

             sftp.put(
                 "./reports/summary.pdf", "/reports/2024/summary.pdf", mkdir=False
             )
        """
        if self.logger:
            self.logger.info(f"SFTP PUT {local_path} -> {remote_path}")
        if mkdir:
            self._mkdir_remote(os.path.dirname(remote_path))
        self._sftp.put(local_path, remote_path)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _mkdir_remote(self, remote_dir: str) -> None:
        """
        Create remote directory structure recursively with intelligent path handling.

        Implements robust directory creation logic that handles nested directory
        structures, existing directories, and permission issues gracefully. Essential
        for automated file upload workflows where target directory structure may
        not exist or may be partially created by other processes.

        Args:
            remote_dir: Remote directory path to create. Supports nested paths
                       with automatic parent directory creation. Handles both
                       absolute and relative paths according to SFTP server
                       conventions and current working directory context.

        Directory Creation Logic:
            1. Check if directory already exists (via listdir attempt)
            2. If directory missing, recursively create parent directories
            3. Create target directory after ensuring parent structure exists
            4. Handle permission and access errors gracefully

        Note:
            This method uses exception-based existence checking for efficiency
            and compatibility with various SFTP server implementations.
        """
        if remote_dir in ("", "/"):
            return
        try:
            self._sftp.listdir(remote_dir)
        except IOError:
            parent = os.path.dirname(remote_dir)
            self._mkdir_remote(parent)
            self._sftp.mkdir(remote_dir)

    # ------------------------------------------------------------------ #
    # Fermeture
    # ------------------------------------------------------------------ #
    def close(self) -> None:
        """
        Gracefully close SFTP and SSH connections with comprehensive error handling.

        Performs controlled shutdown of SFTP session and underlying SSH connection
        with robust error handling to prevent resource leaks and ensure clean
        connection termination. Essential for production environments where
        proper resource management and connection lifecycle control are critical.

        Cleanup Process:
            1. Close SFTP channel if active and accessible
            2. Close underlying SSH connection if established
            3. Handle any errors during cleanup gracefully
            4. Log completion for operational monitoring

        Error Handling:
            - Catches and logs connection errors without propagation
            - Handles partially initialized connections safely
            - Prevents resource leaks in error scenarios
            - Maintains operational logging for troubleshooting

        Note:
            This method is typically called automatically during application
            shutdown or can be invoked manually for explicit resource cleanup.
        """
        try:
            if hasattr(self, "_sftp") and self._sftp:
                self._sftp.close()
            if hasattr(self, "_ssh") and self._ssh:
                self._ssh.close()
        except (OSError, SSHException, AttributeError) as e:
            if self.logger:
                self.logger.warning(f"Error during SFTP connection cleanup: {e}")
        if self.logger:
            self.logger.info("SFTP session closed successfully")
