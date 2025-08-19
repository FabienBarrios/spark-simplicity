# -*- coding: utf-8 -*-
"""
Spark Simplicity
================

A Python package that simplifies Apache Spark operations with an intuitive API.
Perfect for data engineers and analysts who want to focus on data logic rather
than boilerplate code.

Quick Start:
    >>> from spark_simplicity import get_spark_session, load_csv
    >>>
    >>> spark = get_spark_session("my_app")
    >>> df1 = load_csv(spark, "data1.csv")
    >>> df2 = load_csv(spark, "data2.csv")

Key Features:
    - Simplified join operations with intuitive function names
    - Enhanced I/O operations with shared mount validation
    - Optimized Spark session management
    - Production-ready configurations out of the box
    - Extensive error handling and logging
"""

import os

__author__ = "F. Barrios"
__email__ = "fabienbarrios@gmail.com"
__license__ = "MIT"
__description__ = "Simplify Apache Spark operations with an intuitive Python API"

from .connections.database_connection import JdbcSqlServerConnection

# Connection utilities
from .connections.email_connection import EmailSender
from .connections.rest_api_connection import RestApiConnection
from .connections.sftp_connection import SftpConnection
from .io import (  # Read operations; Write operations; Utilities
    get_file_info,
    load_csv,
    load_excel,
    load_json,
    load_parquet,
    load_positional,
    load_text,
    write_csv,
    write_excel,
    write_json,
    write_parquet,
    write_positional,
)

# Logging and notifications
from .logger import get_logger
from .notification_service import create_email_sender, send_error_email

# Core functionality imports
from .session import SparkConfig, get_simple_spark_session, get_spark_session

# Join operations
from .joins import sql_join, sql_union, sql_union_flexible

# Utility functions
from .utils import (
    clean_nulls_and_empty,
    analyze_data_quality,
    profile_dataframe_performance,
    compare_dataframes,
)

# All public exports
__all__ = [
    # Version and metadata
    "__author__",
    "__email__",
    "__license__",
    "__description__",
    # Session management
    "get_spark_session",
    "get_simple_spark_session",
    "SparkConfig",
    # I/O operations
    "load_csv",
    "load_parquet",
    "load_json",
    "load_excel",
    "load_positional",
    "load_text",
    "write_csv",
    "write_parquet",
    "write_json",
    "write_excel",
    "write_positional",
    "get_file_info",
    # Join operations
    "sql_join",
    "sql_union",
    "sql_union_flexible",
    # Utility functions
    "clean_nulls_and_empty",
    "analyze_data_quality",
    "profile_dataframe_performance",
    "compare_dataframes",
    # Logging and notifications
    "get_logger",
    "create_email_sender",
    "send_error_email",
    # Connection utilities
    "EmailSender",
    "JdbcSqlServerConnection",
    "RestApiConnection",
    "SftpConnection",
]


def _check_pyspark_version() -> None:
    """Check if PySpark is available and meets minimum version requirements"""
    try:
        import pyspark

        min_version = "3.5.0"
        current_version = pyspark.__version__

        # Simple version comparison (avoiding packaging dependency)
        current_parts = [int(x) for x in current_version.split(".")]
        min_parts = [int(x) for x in min_version.split(".")]

        if current_parts < min_parts:
            raise ImportError(
                f"PySpark {min_version}+ is required, but {current_version} "
                f"is installed. "
                f"Please upgrade with: pip install pyspark>={min_version}"
            )

    except ImportError as e:
        if "pyspark" in str(e).lower():
            raise ImportError(
                "PySpark is required but not installed. "
                "Install it with: pip install pyspark>=3.5.0"
            ) from e
        raise


def _check_dependencies() -> None:
    """Check all required dependencies are available"""
    _check_pyspark_version()

    import importlib

    required_packages = ["openpyxl", "pandas", "paramiko", "requests"]

    for package in required_packages:
        try:
            importlib.import_module(package)
        except ImportError as e:
            raise ImportError(
                f"Required dependency '{package}' is not installed. "
                f"Install it with: pip install {package}"
            ) from e


# Perform dependency checks on import
_check_dependencies()

# Optional: Show version information (can be disabled with environment variable)
if os.getenv("SPARK_SIMPLICITY_VERBOSE", "").lower() in ("1", "true", "yes"):
    _init_logger = get_logger("spark_simplicity.init")
    _init_logger.info("Spark Simplicity loaded successfully!")
    _init_logger.info("   %d functions available", len(__all__))
    _init_logger.info("   Ready to simplify your Spark workflows!")
