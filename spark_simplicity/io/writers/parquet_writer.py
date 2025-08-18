"""
Spark Simplicity - Parquet Writers
==================================

High-performance Apache Parquet writers for Spark DataFrames with intelligent
strategy selection and production-ready optimizations. This module provides
multiple writing strategies optimized for different use cases, from simple ETL
workflows to large-scale data lake operations.

Key Features:
    - Multiple optimized writing strategies (coalesce, distributed, pandas)
    - Intelligent fallback mechanisms for maximum compatibility
    - Advanced compression options (snappy, gzip, brotli, zstd, lz4, lzo)
    - Hive-style partitioning support for data lake architectures
    - Automatic temporary file management and cleanup
    - Comprehensive error handling and logging
    - Production-ready performance optimizations

Supported Strategies:
    - **Coalesce**: Single-file output optimal for ETL and moderate datasets
    - **Distributed**: Multi-file parallel output for maximum throughput
    - **Pandas**: Compatibility fallback for edge cases and debugging

Storage Optimization:
    - Columnar storage with excellent compression ratios
    - Predicate pushdown for query performance optimization
    - Schema evolution support for data warehouse scenarios
    - Automatic statistics collection for cost-based optimization

Usage:
    from spark_simplicity.io.writers.parquet_writer import write_parquet

    # Simple ETL usage
    write_parquet(df, "output.parquet", shared_mount="/shared/storage")

    # Data lake with partitioning
    write_parquet(large_df, "data_lake/table",
                  strategy="distributed",
                  partition_by=["year", "month"],
                  compression="zstd")
"""

import shutil
from pathlib import Path
from typing import Any, List, Optional, Union

import pandas as pd
from pyspark.sql import DataFrame

from ...logger import get_logger
from .base_writer import (
    _cleanup_temp_directory,
    _create_temp_directory,
    _rename_and_move_files,
)

# Logger for Parquet writer
_parquet_logger = get_logger("spark_simplicity.io.writers.parquet")


def _write_parquet_spark_coalesced(
    df: DataFrame,
    output_path: Path,
    shared_mount: Union[str, Path],
    mode: str,
    compression: str,
    partition_by: Optional[List[str]],
    options: dict,
) -> None:
    """
    Write Parquet using Spark coalesce(1) strategy optimized for single-file output.

    This strategy forces all data through a single executor to produce exactly one
    output file, making it ideal for ETL workflows, data archival, and systems that
    expect single-file input. The coalesce operation may become a bottleneck for
    very large datasets due to single-executor processing.

    Args:
        df: Spark DataFrame to write to Parquet format
        output_path: Target file path for the single Parquet output file
        shared_mount: Shared filesystem path accessible by all cluster nodes
        mode: Write mode ('overwrite', 'append', 'ignore', 'error')
        compression: Parquet compression codec (snappy, gzip, brotli, etc.)
        partition_by: Column names for partitioning (ignored with warning in coalesce
                     mode)
        options: Additional Spark DataFrameWriter options to apply

    Raises:
        ValueError: If write mode is not supported
        RuntimeError: If no part files are found after Spark write operation

    Note:
        Partitioning is not supported with coalesce(1) strategy as it produces
        a single file. A warning will be logged if partition_by is specified.
    """
    tmp_dir = _create_temp_directory(shared_mount, "spark_parquet")

    # Validate write mode
    valid_modes = {"overwrite", "append", "ignore", "error"}
    if mode not in valid_modes:
        raise ValueError(f"Invalid write mode '{mode}'. Valid modes: {valid_modes}")

    # Log warning about partitioning in coalesce mode
    if partition_by:
        _parquet_logger.warning(
            "Partitioning ignored in coalesce(1) mode for small datasets"
        )

    try:
        _parquet_logger.info("Created temporary directory: %s", tmp_dir)

        # Build writer with options
        writer = df.coalesce(1).write.mode(mode).option("compression", compression)

        # Add additional options
        for key, value in options.items():
            writer = writer.option(key, value)

        # Write using coalesce(1)
        writer.parquet(str(tmp_dir))

        # Find and move the single part file
        part_files = list(tmp_dir.glob("part-*.parquet"))
        if not part_files:
            part_files = [
                f
                for f in tmp_dir.glob("part-*")
                if f.is_file() and not f.name.endswith((".crc", "_SUCCESS"))
            ]

        if not part_files:
            raise RuntimeError("No part files found after Spark write operation")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file directly to final location
        shutil.move(str(part_files[0]), str(output_path))

        _parquet_logger.info(
            "Parquet written successfully (Spark coalesced): %s", output_path
        )

    finally:
        _cleanup_temp_directory(tmp_dir)


def _write_parquet_spark_distributed(
    df: DataFrame,
    output_path: Path,
    shared_mount: Union[str, Path],
    mode: str,
    compression: str,
    partition_by: Optional[List[str]],
    options: dict,
) -> None:
    """
    Write Parquet using Spark distributed strategy for maximum parallel throughput.

    This strategy preserves Spark's natural parallelism by allowing each executor
    to write its partition data independently, resulting in multiple part files.
    Optimal for large datasets, data lake scenarios, and when downstream systems
    can handle multiple files. Supports Hive-style partitioning for query optimization.

    Args:
        df: Spark DataFrame to write in distributed fashion
        output_path: Base directory path for distributed Parquet output. For
                    non-partitioned
                    data, becomes the base name for numbered part files. For
                    partitioned data,
                    becomes the root directory containing partition subdirectories.
        shared_mount: Shared filesystem path accessible by all cluster nodes for
                     temporary files
        mode: Write mode determining behavior with existing data:
              - 'overwrite': Replace existing files/directories
              - 'append': Add new files to existing directory structure
              - 'ignore': Skip operation if output exists
              - 'error': Fail if output exists
        compression: Parquet compression codec for storage optimization
        partition_by: List of column names for Hive-style partitioning. Creates
                     directory
                     structure like /year=2023/month=01/ enabling partition pruning.
                     None for non-partitioned output.
        options: Additional Spark DataFrameWriter options (maxRecordsPerFile, etc.)

    Raises:
        ValueError: If write mode is not in supported modes
        RuntimeError: If no part files are produced by Spark write operation

    Output Structure:
        - Non-partitioned: Multiple files like output_path_000.parquet,
          output_path_001.parquet
        - Partitioned: Directory tree like
          output_path/year=2023/month=01/part-00000.parquet
    """
    tmp_dir = _create_temp_directory(shared_mount, "spark_parquet")

    # Validate write mode
    valid_modes = {"overwrite", "append", "ignore", "error"}
    if mode not in valid_modes:
        raise ValueError(f"Invalid write mode '{mode}'. Valid modes: {valid_modes}")

    try:
        _parquet_logger.info("Created temporary directory: %s", tmp_dir)

        # Build writer with options
        writer = df.write.mode(mode).option("compression", compression)

        # Add partitioning if specified
        if partition_by:
            writer = writer.partitionBy(*partition_by)

        # Add additional options
        for key, value in options.items():
            writer = writer.option(key, value)

        # Distributed Spark write
        writer.parquet(str(tmp_dir))

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle partitioned vs non-partitioned output
        if partition_by:
            # Partitioned output - copy directory structure
            if output_path.exists():
                shutil.rmtree(output_path)
            shutil.copytree(tmp_dir, output_path)
            _parquet_logger.info(
                "Parquet written successfully (Spark distributed, partitioned): %s",
                output_path,
            )
        else:
            # Non-partitioned output
            part_files = list(tmp_dir.glob("part-*.parquet"))
            if not part_files:
                part_files = [
                    f
                    for f in tmp_dir.glob("part-*")
                    if f.is_file() and not f.name.endswith((".crc", "_SUCCESS"))
                ]

            if not part_files:
                raise RuntimeError("No part files found after Spark write operation")

            _parquet_logger.info("Found %d Spark output files", len(part_files))

            # Distributed strategy keeps separate files for maximum performance
            _rename_and_move_files(part_files, output_path, "Parquet")
            _parquet_logger.info(
                "Parquet files written successfully (Spark distributed, multiple "
                "files): %s_*",
                output_path.stem,
            )

    finally:
        _cleanup_temp_directory(tmp_dir)


def _write_parquet_pandas_fallback(
    df: DataFrame, output_path: Path, mode: str, compression: str
) -> None:
    """
    Write Parquet using pandas fallback strategy for maximum compatibility.

    This fallback strategy converts the entire Spark DataFrame to pandas and writes
    using pandas' native Parquet support. Provides maximum compatibility with edge
    cases, complex data types, and environments where Spark's Parquet writer may
    have issues. Limited by driver node memory capacity.

    This strategy is automatically selected when:
    - Shared storage is not available for other strategies
    - Explicitly requested for debugging or compatibility
    - Other strategies fail and fallback is enabled

    Args:
        df: Spark DataFrame to collect and write via pandas
        output_path: Target file path for single Parquet output file
        mode: Write mode - only 'overwrite' is supported for pandas strategy
        compression: Parquet compression codec (snappy, gzip, brotli, etc.)

    Raises:
        ValueError: If mode is not 'overwrite' (only supported mode for pandas)
        RuntimeError: If pandas write operation fails due to I/O issues
        MemoryError: If DataFrame is too large to collect on driver node

    Performance Characteristics:
        - Single-threaded write operation on driver node
        - Memory usage: Entire dataset must fit in driver memory
        - Network overhead: All data transferred to driver
        - Compatibility: Highest, handles edge cases other strategies may not

    Warning:
        This strategy collects all data to the driver node, which can cause
        out-of-memory errors for large datasets. Monitor driver memory usage
        and consider filtering data before using this strategy.
    """
    # Validate write mode
    valid_modes = {"overwrite"}
    if mode not in valid_modes:
        raise ValueError(
            f"Pandas fallback mode only supports {valid_modes} for Parquet, got "
            f"'{mode}'"
        )

    try:
        _parquet_logger.info("Converting Spark DataFrame to pandas...")

        # Collect all data to driver node
        pandas_df: pd.DataFrame = df.toPandas()
        _parquet_logger.info("Collected %d records to driver node", len(pandas_df))

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write Parquet using pandas
        pandas_df.to_parquet(output_path, compression=compression, index=False)

        _parquet_logger.info(
            "Parquet written successfully (pandas fallback): %s (%d records)",
            output_path,
            len(pandas_df),
        )

    except Exception as e:
        raise RuntimeError(
            f"Could not save the file (please verify the path, write permissions, and "
            f"available "
            f"disk space) : Parquet via pandas fallback: {str(e)}"
        ) from e


def write_parquet(
    df: DataFrame,
    output_path: Union[str, Path],
    *,
    shared_mount: Optional[Union[str, Path]] = None,
    mode: str = "overwrite",
    compression: str = "snappy",
    partition_by: Optional[List[str]] = None,
    strategy: str = "coalesce",
    **options: Any,
) -> None:
    """
    Export Spark DataFrame to Apache Parquet format with intelligent strategy selection.

    Provides multiple optimized writing strategies for different use cases, from simple
    ETL
    scenarios to high-performance data lakes. This function automatically handles
    temporary
    file management, compression optimization, and partitioning schemes while ensuring
    consistent output regardless of cluster configuration.

    The function supports three distinct strategies optimized for different scenarios:
    - **Coalesce**: Produces single files optimal for ETL workflows and
      small-to-medium datasets
    - **Distributed**: Leverages full cluster parallelism for maximum throughput on
      large datasets
    - **Pandas**: Provides maximum compatibility fallback for edge cases and small data

    Args:
        df: Spark DataFrame containing the data to export. All Spark SQL data types
            are supported and will be mapped to appropriate Parquet equivalents.
        output_path: Target file path or directory for Parquet output. For single-file
                    strategies ('coalesce', 'pandas'), this should include the .parquet
                    extension. For distributed strategy, this becomes the base directory
                    name for multiple part files or partitioned structure.
        shared_mount: Path to shared filesystem accessible by all cluster nodes (driver
                     and executors). Required for 'coalesce' and 'distributed'
                     strategies.
                     Common examples: NFS mounts, shared network drives, or distributed
                     filesystems like HDFS. If None, automatically falls back to pandas.
        mode: Write mode determining behavior when output already exists:
              - 'overwrite': Replace existing files/directories (default, safest for
                ETL)
              - 'append': Add new data to existing Parquet files (schema must match)
              - 'ignore': Skip write operation if output exists (idempotent behavior)
              - 'error': Fail with exception if output exists (strict safety mode)
        compression: Parquet compression codec for optimal storage and query
                    performance:
                    - 'snappy': Fast compression/decompression, good for frequent reads
                      (default)
                    - 'gzip': Higher compression ratio, slower processing, good for
                      archival
                    - 'lzo': Fast compression similar to snappy, good for write-heavy
                      workloads
                    - 'brotli': Excellent compression ratio, moderate speed, good for
                      analytics
                    - 'lz4': Extremely fast, lower compression, good for temporary
                      storage
                    - 'zstd': Balanced speed/compression, good all-around choice
        partition_by: List of column names for Hive-style partitioning (distributed
                     strategy only).
                     Creates directory structure like /year=2023/month=01/ enabling
                     partition
                     pruning for query optimization. Columns should have reasonable
                     cardinality
                     (typically < 1000 unique values per column). Ignored in other
                     strategies.
        strategy: Write strategy selection based on performance requirements:
                 - 'coalesce': Single output file via coalesce(1). Optimal for ETL
                   pipelines,
                   data archival, and when downstream systems expect single files.
                   Slower for
                   very large datasets due to single-executor bottleneck.
                 - 'distributed': Multiple part files preserving natural Spark
                   parallelism.
                   Optimal for data lake scenarios, large datasets (>1GB), and when
                   downstream
                   systems can handle multiple files. Enables partitioning and maximum
                   throughput.
                 - 'pandas': Single file via pandas conversion. Compatibility fallback
                   for edge
                   cases, debugging, or when cluster shared storage is unavailable.
                   Limited by
                   driver memory capacity.
        **options: Additional Spark DataFrameWriter options passed directly to the
                  underlying
                  Parquet writer. Common options include:
                  - 'maxRecordsPerFile': Limit records per output file for size control
                  - 'bucketBy': Enable bucketing for join optimization
                  - 'sortBy': Sort data within buckets for query performance
                  - 'option("parquet.block.size", "134217728")': Control Parquet block
                    size

    Raises:
        ValueError: If strategy is not in ['coalesce', 'distributed', 'pandas'], if mode
                   is not valid for the selected strategy, or if partition_by columns
                   don't exist in the DataFrame schema.
        RuntimeError: If write operation fails due to insufficient disk space,
                     permission
                     errors, network connectivity issues with shared_mount, or if no
                     output
                     files are produced by Spark (indicating internal Spark issues).
        MemoryError: If using pandas strategy with datasets too large for driver memory,
                    or if shared_mount is unavailable and fallback to pandas fails.
        PermissionError: If output_path or shared_mount directories are not writable
                        by the Spark processes.

    Performance Guidelines:
        **Small datasets (< 100MB)**:
        - Use 'coalesce' strategy with snappy compression
        - Single file simplifies downstream processing
        - Memory overhead is minimal

        **Medium datasets (100MB - 10GB)**:
        - Use 'coalesce' for single-file requirements
        - Use 'distributed' for maximum write performance
        - Consider partitioning by date columns for time-series data

        **Large datasets (> 10GB)**:
        - Use 'distributed' strategy exclusively
        - Implement partitioning on frequently-filtered columns
        - Use 'zstd' or 'brotli' compression for storage optimization
        - Set appropriate 'maxRecordsPerFile' to control file sizes

    Examples:
        Simple ETL export to single Parquet file:

         write_parquet(df, "monthly_report.parquet",
        ...               shared_mount="/shared/etl")

        High-performance data lake export with partitioning:

         write_parquet(sales_df, "data_lake/sales",
        ...               shared_mount="/data/lake",
        ...               strategy="distributed",
        ...               partition_by=["year", "region"],
        ...               compression="zstd")

        Compatibility export when shared storage is unavailable:

         write_parquet(small_df, "local_export.parquet",
        ...               strategy="pandas",
        ...               compression="gzip")

        Advanced configuration for large-scale analytics:

         write_parquet(transactions_df, "analytics/transactions",
        ...               shared_mount="/analytics/storage",
        ...               strategy="distributed",
        ...               mode="append",
        ...               partition_by=["date", "country"],
        ...               maxRecordsPerFile=1000000,
        ...               compression="brotli")

    Output Structure:
        **Coalesce Strategy**: Single .parquet file at exact output_path location
        ```
        output_path.parquet
        ```

        **Distributed Strategy (non-partitioned)**: Multiple numbered part files
        ```
        output_path_000.parquet
        output_path_001.parquet
        output_path_002.parquet
        ```

        **Distributed Strategy (partitioned)**: Hive-style directory structure
        ```
        output_path/
        ├── year=2023/month=01/part-00000.parquet
        ├── year=2023/month=02/part-00000.parquet
        └── year=2024/month=01/part-00000.parquet
        ```

    Storage Optimization:
        - Parquet's columnar format provides excellent compression and query performance
        - Predicate pushdown automatically filters data at the file level
        - Schema evolution is supported for adding new columns over time
        - Statistics are automatically collected for query optimization
        - Consider column ordering: frequently-filtered columns first for better pruning

    See Also:
        - CSV export: ``write_csv()`` for delimited text output
        - JSON export: ``write_json()`` for schema-flexible exports
        - Delta Lake: Consider Delta format for ACID transactions and time travel
        - Iceberg: Modern table format with advanced features for data lakes

    Warning:
        The 'distributed' strategy creates multiple files which some downstream systems
        may not handle correctly. Ensure your data pipeline can process multiple Parquet
        files or use 'coalesce' strategy for single-file output.

    Note:
        Shared storage performance significantly impacts write speed. Network-attached
        storage may become a bottleneck with distributed strategy. Consider local SSD
        storage for temporary files when possible.
    """
    output_path = Path(output_path)

    # Validate strategy parameter
    valid_strategies = {"coalesce", "distributed", "pandas"}
    if strategy not in valid_strategies:
        raise ValueError(
            f"Invalid strategy '{strategy}'. Valid strategies: {valid_strategies}"
        )

    # Execute selected strategy
    if strategy == "distributed":
        if shared_mount is None:
            _parquet_logger.warning(
                "Distributed strategy requires shared_mount, falling back to pandas"
            )
            _write_parquet_pandas_fallback(df, output_path, mode, compression)
        else:
            _parquet_logger.info(
                "Using distributed strategy - parallel write with multiple files"
            )
            _write_parquet_spark_distributed(
                df, output_path, shared_mount, mode, compression, partition_by, options
            )
    elif strategy == "pandas":
        _parquet_logger.info("Using pandas strategy - maximum compatibility")
        _write_parquet_pandas_fallback(df, output_path, mode, compression)
    else:  # strategy == "coalesce" (default)
        if shared_mount is None:
            _parquet_logger.info(
                "Coalesce strategy without shared_mount - using pandas fallback"
            )
            _write_parquet_pandas_fallback(df, output_path, mode, compression)
        else:
            _parquet_logger.info(
                "Using coalesce strategy - single file via coalesce(1)"
            )
            _write_parquet_spark_coalesced(
                df, output_path, shared_mount, mode, compression, partition_by, options
            )
