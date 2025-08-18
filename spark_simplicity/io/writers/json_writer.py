"""
Spark Simplicity - JSON Writers
===============================

High-performance JSON writers for Spark DataFrames with flexible formatting options
and intelligent strategy selection. This module provides optimized JSON export
capabilities
supporting both single-file and distributed output strategies with proper JSON array
formatting.

Key Features:
    - Multiple optimized writing strategies (coalesce, distributed, pandas)
    - JSON array formatting with pretty-print support
    - Intelligent fallback mechanisms for maximum compatibility
    - JSONL to JSON array conversion for proper format compliance
    - Comprehensive append mode support with existing data merging
    - UTF-8 encoding support for international character sets

Supported Output Formats:
    - **Compact JSON Arrays**: Single-line format for production systems
    - **Pretty JSON Arrays**: Indented format for human readability
    - **Multiple Files**: Distributed JSON files for parallel processing

Strategy Selection:
    - **Coalesce**: Single JSON file optimal for ETL and moderate datasets
    - **Distributed**: Multiple JSON files for maximum throughput
    - **Pandas**: Compatibility fallback with advanced append functionality

Usage:
    from spark_simplicity.io.writers.json_writer import write_json

    # Simple JSON export
    write_json(df, "output.json")

    # Pretty formatted JSON
    write_json(df, "data.json", pretty=True)

    # High-performance distributed export
    write_json(large_df, "distributed_data",
               strategy="distributed", shared_mount="/shared/storage")
"""

import json
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd
from pyspark.sql import DataFrame

from ...logger import get_logger
from ..utils.format_utils import (
    convert_jsonl_to_json_array,
    process_and_move_json_files,
)
from .base_writer import _cleanup_temp_directory, _create_temp_directory

# Logger for JSON writer
_json_logger = get_logger("spark_simplicity.io.writers.json")


def _write_json_spark_coalesced(
    df: DataFrame,
    output_path: Path,
    shared_mount: Union[str, Path],
    mode: str,
    pretty: bool,
    options: dict,
) -> None:
    """
    Write JSON using Spark coalesce(1) strategy optimized for single-file output.

    This strategy forces all data through a single executor to produce exactly one
    JSON file with proper JSON array formatting. Ideal for ETL workflows, data exchange
    scenarios, and systems expecting single-file input. Converts Spark's native JSONL
    output to standard JSON array format with optional pretty-printing.

    Args:
        df: Spark DataFrame to export as JSON array
        output_path: Target file path for the single JSON output file
        shared_mount: Shared filesystem path accessible by all cluster nodes
        mode: Write mode ('overwrite', 'append', 'ignore', 'error')
        pretty: If True, formats output with indentation and line breaks for readability
        options: Additional Spark DataFrameWriter options (dateFormat, timestampFormat,
                etc.)

    Raises:
        ValueError: If write mode is not supported
        RuntimeError: If no part files are found after Spark write operation

    Output Format:
        - pretty=False: Compact JSON array on single line: [{"id":1,"name":"Alice"},...]
        - pretty=True: Indented JSON array with line breaks for human readability

    Note:
        Spark natively outputs JSONL (one JSON object per line). This function converts
        the JSONL output to a proper JSON array format for standards compliance.
    """
    tmp_dir = _create_temp_directory(shared_mount, "spark_json")

    # Validate write mode
    valid_modes = {"overwrite", "append", "ignore", "error"}
    if mode not in valid_modes:
        raise ValueError(f"Invalid write mode '{mode}'. Valid modes: {valid_modes}")

    try:
        _json_logger.info("Created temporary directory: %s", tmp_dir)

        # Write using coalesce(1) without pretty option (we'll handle formatting later)
        (df.coalesce(1).write.mode(mode).options(**options).json(str(tmp_dir)))

        # Find the single part file
        part_files = list(tmp_dir.glob("part-*.json"))
        if not part_files:
            raise RuntimeError("No part files found after Spark write operation")

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert JSONL to JSON array format (pretty or compact)
        convert_jsonl_to_json_array(part_files[0], output_path, pretty)

        _json_logger.info(
            "JSON written successfully (Spark coalesced): %s", output_path
        )

    finally:
        _cleanup_temp_directory(tmp_dir)


def _write_json_spark_distributed(
    df: DataFrame,
    output_path: Path,
    shared_mount: Union[str, Path],
    mode: str,
    pretty: bool,
    options: dict,
) -> None:
    """
    Write JSON using Spark distributed strategy for maximum parallel throughput.

    This strategy preserves Spark's natural parallelism by allowing each executor
    to write its partition data independently, resulting in multiple JSON files.
    Optimal for large datasets, high-throughput scenarios, and when downstream
    systems can process multiple JSON files. Each file contains a properly formatted
    JSON array with consistent formatting.

    Args:
        df: Spark DataFrame to write in distributed fashion
        output_path: Base name for distributed JSON output files. Becomes the prefix
                    for numbered files like output_path_000.json, output_path_001.json,
                    etc.
        shared_mount: Shared filesystem path accessible by all cluster nodes for
                     temporary files
        mode: Write mode determining behavior with existing data:
              - 'overwrite': Replace existing files
              - 'append': Add new files alongside existing ones
              - 'ignore': Skip operation if output files exist
              - 'error': Fail if any output files exist
        pretty: If True, formats each JSON file with indentation and line breaks
        options: Additional Spark DataFrameWriter options (dateFormat, timestampFormat,
                etc.)

    Raises:
        ValueError: If write mode is not in supported modes
        RuntimeError: If no part files are produced by Spark write operation

    Output Structure:
        Multiple JSON array files: output_path_000.json, output_path_001.json, etc.
        Each file contains a complete JSON array with subset of the total data.

    Performance Benefits:
        - Full cluster parallelism during write operation
        - No single-executor bottleneck like coalesce strategy
        - Optimal for datasets larger than single-node memory capacity
        - Enables downstream parallel processing of individual files

    Note:
        Each output file is a complete, valid JSON array. Downstream systems
        can process files individually or merge arrays as needed.
    """
    tmp_dir = _create_temp_directory(shared_mount, "spark_json")

    # Validate write mode
    valid_modes = {"overwrite", "append", "ignore", "error"}
    if mode not in valid_modes:
        raise ValueError(f"Invalid write mode '{mode}'. Valid modes: {valid_modes}")

    try:
        _json_logger.info("Created temporary directory: %s", tmp_dir)

        # Distributed Spark write (without pretty option, we'll handle formatting later)
        (df.write.mode(mode).options(**options).json(str(tmp_dir)))

        # Find all part files
        part_files = list(tmp_dir.glob("part-*.json"))
        if not part_files:
            raise RuntimeError("No part files found after Spark write operation")

        _json_logger.info("Found %d Spark output files", len(part_files))

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Distributed strategy keeps separate files for maximum performance with proper
        # JSON formatting
        process_and_move_json_files(part_files, output_path, pretty)
        _json_logger.info(
            "JSON files written successfully (Spark distributed, multiple files): %s_*",
            output_path.stem,
        )

    finally:
        _cleanup_temp_directory(tmp_dir)


def _write_json_pandas_fallback(
    df: DataFrame, output_path: Path, mode: str, pretty: bool
) -> None:
    """
    Write JSON using pandas fallback strategy for maximum compatibility and append
    support.

    This fallback strategy converts the entire Spark DataFrame to pandas and writes
    using Python's native JSON library with advanced append functionality. Provides
    maximum compatibility with edge cases, complex data types, and sophisticated
    append mode that can merge with existing JSON arrays. Limited by driver node
    memory capacity but offers the most flexible write operations.

    Key Features:
        - Intelligent append mode with existing JSON array merging
        - Automatic fallback from malformed existing files to overwrite mode
        - UTF-8 encoding with international character support
        - Both compact and pretty-print formatting options
        - Robust error handling for file system issues

    Args:
        df: Spark DataFrame to collect and write via pandas conversion
        output_path: Target file path for single JSON output file
        mode: Write mode - supports 'overwrite' and 'append'
              - 'overwrite': Replace existing file completely
              - 'append': Merge new records with existing JSON array
        pretty: If True, formats output with indentation and line breaks

    Raises:
        ValueError: If mode is not in ['overwrite', 'append']
        RuntimeError: If pandas write operation fails due to I/O issues
        MemoryError: If DataFrame is too large to collect on driver node

    Append Mode Behavior:
        - Loads existing JSON file and parses as array
        - Converts non-array JSON to single-element array automatically
        - Appends new records to existing data
        - Falls back to overwrite mode if existing file is malformed
        - Preserves formatting consistency (pretty/compact) for entire file

    Performance Characteristics:
        - Single-threaded operation on driver node
        - Memory usage: Entire dataset + existing file must fit in driver memory
        - Network overhead: All data transferred to driver for processing
        - Compatibility: Highest, handles complex nested structures and edge cases

    Warning:
        This strategy collects all data to the driver node and loads existing
        files into memory. Monitor driver memory usage for large datasets or
        files with extensive existing data.
    """
    # Validate write mode
    valid_modes = {"overwrite", "append"}
    if mode not in valid_modes:
        raise ValueError(
            f"Pandas fallback mode only supports {valid_modes}, got '{mode}'"
        )

    try:
        _json_logger.info("Converting Spark DataFrame to pandas...")

        # Collect all data to driver node
        pandas_df: pd.DataFrame = df.toPandas()
        new_data = pandas_df.to_dict("records")

        _json_logger.info("Collected %d records to driver node", len(new_data))

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle different write modes
        if mode == "append" and output_path.exists():
            # Load existing data and append
            try:
                with open(output_path, encoding="utf-8") as f:
                    existing_data = json.load(f)
                # Ensure existing data is a list
                if not isinstance(existing_data, list):
                    existing_data = [existing_data] if existing_data else []

                combined_data = existing_data + new_data
                _json_logger.info(
                    "Appending %d new records to %d existing records",
                    len(new_data),
                    len(existing_data),
                )
            except (json.JSONDecodeError, FileNotFoundError) as e:
                _json_logger.warning(
                    "Could not read existing file, treating as overwrite: %s", str(e)
                )
                combined_data = new_data
        else:
            combined_data = new_data

        # Write JSON format
        with open(output_path, "w", encoding="utf-8") as f:
            if pretty:
                # Pretty JSON array format: proper JSON array with indentation
                json.dump(combined_data, f, ensure_ascii=False, indent=2)
            else:
                # Compact JSON array format: all data on single line
                json.dump(combined_data, f, ensure_ascii=False, separators=(",", ":"))

        _json_logger.info(
            "JSON written successfully (pandas fallback): %s (%d total records)",
            output_path,
            len(combined_data),
        )

    except Exception as e:
        raise RuntimeError(
            f"Could not save the file (please verify the path, write permissions, and "
            f"available "
            f"disk space) : JSON via pandas fallback: {str(e)}"
        ) from e


def write_json(
    df: DataFrame,
    output_path: Union[str, Path],
    *,
    shared_mount: Optional[Union[str, Path]] = None,
    mode: str = "overwrite",
    pretty: bool = False,
    strategy: str = "coalesce",
    **options: Any,
) -> None:
    """
    Export Spark DataFrame to JSON format with intelligent strategy selection and
    formatting.

    Provides multiple optimized writing strategies for different use cases, from simple
    data
    exchange scenarios to high-performance data processing pipelines. This function
    automatically
    converts Spark's native JSONL output to proper JSON array format with optional
    pretty-printing,
    ensuring standards compliance and downstream system compatibility.

    The function supports three distinct strategies optimized for different scenarios:
    - **Coalesce**: Produces single JSON files optimal for data exchange and ETL
      workflows
    - **Distributed**: Leverages full cluster parallelism for maximum throughput on
      large datasets
    - **Pandas**: Provides maximum compatibility with advanced append functionality

    Args:
        df: Spark DataFrame containing the data to export. All Spark SQL data types
            are supported and will be serialized to appropriate JSON equivalents.
        output_path: Target file path or base name for JSON output. For single-file
                    strategies ('coalesce', 'pandas'), this should include the .json
                    extension. For distributed strategy, this becomes the base name
                    for multiple numbered JSON files.
        shared_mount: Path to shared filesystem accessible by all cluster nodes (driver
                     and executors). Required for 'coalesce' and 'distributed'
                     strategies.
                     Common examples: NFS mounts, shared network drives, or distributed
                     filesystems like HDFS. If None, automatically falls back to pandas.
        mode: Write mode determining behavior when output already exists:
              - 'overwrite': Replace existing files completely (default, safest for ETL)
              - 'append': Merge new data with existing JSON arrays (pandas strategy
                only)
              - 'ignore': Skip write operation if output exists (idempotent behavior)
              - 'error': Fail with exception if output exists (strict safety mode)
        pretty: Format control for JSON output readability:
               - False: Compact single-line format for production/processing systems
                 (default)
               - True: Indented multi-line format for human readability and debugging
        strategy: Write strategy selection based on performance and compatibility
                 requirements:
                 - 'coalesce': Single JSON file via coalesce(1). Optimal for data
                   exchange,
                   ETL pipelines, and when downstream systems expect single files. May
                   become
                   bottleneck for very large datasets due to single-executor processing.
                 - 'distributed': Multiple JSON files preserving natural Spark
                   parallelism.
                   Optimal for big data scenarios, high-throughput processing, and when
                   downstream
                   systems can handle multiple files. Enables maximum write performance.
                 - 'pandas': Single file via pandas conversion with advanced append
                   support.
                   Compatibility fallback for edge cases, complex append operations,
                   or when
                   cluster shared storage is unavailable. Limited by driver memory
                   capacity.
        **options: Additional Spark DataFrameWriter options passed directly to the
                  underlying
                  JSON writer. Common options include:
                  - 'dateFormat': Date formatting pattern (default: 'yyyy-MM-dd')
                  - 'timestampFormat': Timestamp formatting pattern (default:
                    'yyyy-MM-dd HH:mm:ss')
                  - 'compression': Enable compression for temporary files ('gzip',
                    'bzip2')

    Raises:
        ValueError: If strategy is not in ['coalesce', 'distributed', 'pandas'], if mode
                   is not valid for the selected strategy, or if required parameters are
                   missing.
        RuntimeError: If write operation fails due to insufficient disk space,
                     permission
                     errors, network connectivity issues with shared_mount, or if no
                     output
                     files are produced by Spark.
        MemoryError: If using pandas strategy with datasets too large for driver memory,
                    or if shared_mount is unavailable and fallback to pandas fails.
        PermissionError: If output_path or shared_mount directories are not writable
                        by the Spark processes.

    Performance Guidelines:
        **Small datasets (< 50MB)**:
        - Use 'coalesce' or 'pandas' strategy with compact formatting
        - Single file simplifies downstream JSON parsing
        - Memory overhead is minimal for both strategies

        **Medium datasets (50MB - 5GB)**:
        - Use 'coalesce' for single-file requirements
        - Use 'distributed' for maximum write performance
        - Consider pretty=False for faster parsing in downstream systems

        **Large datasets (> 5GB)**:
        - Use 'distributed' strategy exclusively
        - Enable compression in Spark options for network efficiency
        - Use compact formatting unless human debugging is required

    Examples:
        Simple data export with compact JSON array format:

         write_json(df, "sales_data.json")

        Human-readable JSON for debugging and analysis:

         write_json(df, "debug_output.json", pretty=True)

        High-performance distributed export for big data:

         write_json(large_df, "distributed_export",
        ...            shared_mount="/data/shared",
        ...            strategy="distributed")

        Advanced append operation for incremental data loading:

         write_json(new_records_df, "incremental_data.json",
        ...            strategy="pandas", mode="append", pretty=True)

        Custom date formatting for legacy system compatibility:

         write_json(df, "legacy_format.json",
        ...            dateFormat="dd-MM-yyyy",
        ...            timestampFormat="dd-MM-yyyy HH:mm:ss")

    Output Formats:
        **Compact JSON Arrays** (pretty=False):
        ```json
        [{"id":1,"name":"Alice","age":25},{"id":2,"name":"Bob","age":30}]
        ```

        **Pretty JSON Arrays** (pretty=True):
        ```json
        [
          {
            "id": 1,
            "name": "Alice",
            "age": 25
          },
          {
            "id": 2,
            "name": "Bob",
            "age": 30
          }
        ]
        ```

        **Distributed Strategy**: Multiple files like output_000.json, output_001.json,
        etc.
        Each file contains a complete JSON array with subset of the total data.

    JSON Standards Compliance:
        - Outputs proper JSON arrays (not JSONL) for maximum compatibility
        - UTF-8 encoding with full international character support
        - Escaped special characters following JSON specification
        - Consistent date/timestamp formatting across all records
        - Proper handling of null values and nested structures

    See Also:
        - Parquet export: ``write_parquet()`` for columnar analytics format
        - CSV export: ``write_csv()`` for tabular delimited output
        - Custom text formatting: ``write_positional()`` for fixed-width formats
        - Spark native JSON: ``DataFrame.write.json()`` for JSONL output

    Warning:
        The 'distributed' strategy creates multiple JSON files which some downstream
        systems may not handle automatically. Ensure your data pipeline can process
        multiple JSON files or use 'coalesce' strategy for single-file output.

    Note:
        JSON arrays can become memory-intensive for very large datasets when parsed
        by downstream systems. Consider using JSONL format (Spark's native output)
        or chunking strategies for extremely large data exports.
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
            _json_logger.warning(
                "Distributed strategy requires shared_mount, falling back to pandas"
            )
            _write_json_pandas_fallback(df, output_path, mode, pretty)
        else:
            _json_logger.info(
                "Using distributed strategy - parallel write with multiple files"
            )
            _write_json_spark_distributed(
                df, output_path, shared_mount, mode, pretty, options
            )
    elif strategy == "pandas":
        _json_logger.info("Using pandas strategy - maximum compatibility")
        _write_json_pandas_fallback(df, output_path, mode, pretty)
    else:  # strategy == "coalesce" (default)
        if shared_mount is None:
            _json_logger.info(
                "Coalesce strategy without shared_mount - using pandas fallback"
            )
            _write_json_pandas_fallback(df, output_path, mode, pretty)
        else:
            _json_logger.info("Using coalesce strategy - single file via coalesce(1)")
            _write_json_spark_coalesced(
                df, output_path, shared_mount, mode, pretty, options
            )
