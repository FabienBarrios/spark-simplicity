"""Spark Simplicity I/O Operations Module.

This module provides comprehensive file I/O operations for Apache Spark DataFrames
with intelligent optimization, shared mount validation, and multiple format support.

Key Features:
    - Automatic strategy selection for small vs large datasets
    - Distributed mount point validation across Spark clusters
    - Support for CSV, JSON, Parquet, Excel, and positional files
    - Adaptive write strategies (coalesced vs distributed vs pandas fallback)
    - Comprehensive error handling and performance optimizations

Supported Formats:
    - CSV: Comma-separated values with customizable options
    - JSON: JavaScript Object Notation with pretty formatting
    - Parquet: Columnar storage with compression and partitioning
    - Excel: Microsoft Excel files via pandas integration
    - Positional: Fixed-width text files with column specifications
    - Text: Plain text files (one line per DataFrame row)

Usage Examples:
    Basic file loading:
     from spark_simplicity import get_spark_session, load_csv, write_parquet
     spark = get_spark_session("my_app")
     df = load_csv(spark, "data.csv")
     write_parquet(df, "output.parquet", shared_mount="/shared/nfs")

    Shared mount validation for distributed processing:
     df = load_csv(spark, "/mnt/shared/data.csv", shared_mount=True)
     write_csv(df, "output.csv", shared_mount="/shared/nfs", strategy="distributed")

    Performance optimization for large datasets:
     write_parquet(df, "big_data", shared_mount="/shared/nfs",
    ...              auto_optimize=True, small_dataset_threshold=50_000)

Author: F. Barrios
Version: 1.0.0
"""

# Import all reader functions
from .readers import (
    load_csv,
    load_excel,
    load_json,
    load_parquet,
    load_positional,
    load_text,
)

# Import utility functions
from .utils import get_file_info

# Import all writer functions
from .writers import write_csv, write_excel, write_json, write_parquet, write_positional

__all__ = [
    # Readers
    "load_csv",
    "load_json",
    "load_parquet",
    "load_excel",
    "load_text",
    "load_positional",
    # Writers
    "write_csv",
    "write_json",
    "write_parquet",
    "write_excel",
    "write_positional",
    # Utilities
    "get_file_info",
]
