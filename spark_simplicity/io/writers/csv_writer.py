"""
Spark Simplicity - CSV Writers
==============================

High-performance CSV writers for Spark DataFrames with intelligent strategy selection
and comprehensive formatting options. This module provides enterprise-grade CSV export
capabilities supporting both single-file and distributed output strategies with full
control over encoding, delimiters, quoting, and data formatting.

Key Features:
    - Multiple optimized writing strategies (coalesce, distributed, pandas)
    - Comprehensive CSV formatting control (separators, quotes, escaping)
    - International character support with flexible encoding options
    - Intelligent append mode with existing data merging
    - Production-ready error handling and logging
    - Cross-platform compatibility and standards compliance

CSV Standards & Compatibility:
    - **RFC 4180** compliant CSV output format
    - **UTF-8** default encoding with international character support
    - **Flexible delimiters** supporting comma, semicolon, tab, pipe, and custom
      separators
    - **Configurable quoting** for handling special characters and embedded delimiters
    - **Escape sequences** for complex data scenarios

Strategy Selection:
    - **Coalesce**: Single CSV file optimal for ETL workflows and data exchange
    - **Distributed**: Multiple CSV files for maximum throughput on large datasets
    - **Pandas**: Advanced compatibility with sophisticated append operations

Usage:
    from spark_simplicity.io.writers.csv_writer import write_csv

    # Standard ETL export
    write_csv(df, "data_export.csv")

    # European format with semicolon delimiter
    write_csv(df, "european_data.csv", sep=";", encoding="utf-8")

    # High-performance distributed export
    write_csv(large_df, "big_data_export",
              strategy="distributed", shared_mount="/shared/storage")

    # Tab-separated values for database import
    write_csv(df, "database_import.tsv", sep="\t")
"""

import shutil
from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd
from pyspark.sql import DataFrame

from ...logger import get_logger
from .base_writer import (
    _cleanup_temp_directory,
    _create_temp_directory,
    _rename_and_move_files,
)

# Logger for CSV writer
_csv_logger = get_logger("spark_simplicity.io.writers.csv")


def _write_csv_spark_coalesced(
    df: DataFrame,
    output_path: Path,
    shared_mount: Union[str, Path],
    header: bool,
    sep: str,
    mode: str,
    encoding: str,
    quote: str,
    escape: str,
    options: dict,
) -> None:
    """
    Write CSV using Spark coalesce(1) strategy optimized for single-file output.

    This strategy forces all data through a single executor to produce exactly one
    CSV file, making it ideal for ETL workflows, data exchange scenarios, and systems
    expecting single-file input. Provides complete control over CSV formatting including
    delimiters, quoting, encoding, and escaping for maximum compatibility.

    Args:
        df: Spark DataFrame to export as CSV file
        output_path: Target file path for the single CSV output file
        shared_mount: Shared filesystem path accessible by all cluster nodes
        header: Whether to include column headers in first row
        sep: Field delimiter character (comma, semicolon, tab, pipe, etc.)
        mode: Write mode ('overwrite', 'append', 'ignore', 'error')
        encoding: Character encoding (UTF-8, latin-1, cp1252, etc.)
        quote: Quote character for fields containing special characters
        escape: Escape character for handling quotes within quoted fields
        options: Additional Spark DataFrameWriter options (dateFormat, timestampFormat,
                etc.)

    Raises:
        ValueError: If write mode is not supported
        RuntimeError: If no part files are found after Spark write operation

    Note:
        The coalesce(1) operation may become a bottleneck for very large datasets
        due to single-executor processing. Consider distributed strategy for optimal
        performance with datasets larger than a few GB.
    """
    tmp_dir = _create_temp_directory(shared_mount, "spark_csv")

    # Validate write mode
    valid_modes = {"overwrite", "append", "ignore", "error"}
    if mode not in valid_modes:
        raise ValueError(f"Invalid write mode '{mode}'. Valid modes: {valid_modes}")

    try:
        _csv_logger.info("Created temporary directory: %s", tmp_dir)

        # Build writer with options
        writer = (
            df.coalesce(1)
            .write.mode(mode)
            .option("header", header)
            .option("sep", sep)
            .option("encoding", encoding)
            .option("quote", quote)
            .option("escape", escape)
        )

        # Add additional options
        for key, value in options.items():
            writer = writer.option(key, value)

        # Write using coalesce(1)
        writer.csv(str(tmp_dir))

        # Find and move the single part file
        part_files = list(tmp_dir.glob("part-*.csv"))
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

        _csv_logger.info("CSV written successfully (Spark coalesced): %s", output_path)

    finally:
        _cleanup_temp_directory(tmp_dir)


def _write_csv_spark_distributed(
    df: DataFrame,
    output_path: Path,
    shared_mount: Union[str, Path],
    header: bool,
    sep: str,
    mode: str,
    encoding: str,
    quote: str,
    escape: str,
    options: dict,
) -> None:
    """
    Write CSV using Spark distributed strategy for maximum parallel throughput.

    This strategy preserves Spark's natural parallelism by allowing each executor
    to write its partition data independently, resulting in multiple CSV files.
    Optimal for very large datasets, high-throughput data processing scenarios,
    and when downstream systems can process multiple files in parallel.

    Args:
        df: Spark DataFrame to write in distributed fashion
        output_path: Base name for distributed CSV output files. Becomes the prefix
                    for numbered files like output_000.csv, output_001.csv, etc.
        shared_mount: Shared filesystem path accessible by all cluster nodes for
                     temporary files
        header: Whether to include column headers in each output file
        sep: Field delimiter character applied consistently across all files
        mode: Write mode determining behavior with existing data:
              - 'overwrite': Replace existing files
              - 'append': Add new files alongside existing ones
              - 'ignore': Skip operation if output files exist
              - 'error': Fail if any output files exist
        encoding: Character encoding applied to all output files
        quote: Quote character for fields containing delimiters or special characters
        escape: Escape character for handling quotes within quoted fields
        options: Additional Spark DataFrameWriter options applied to all files

    Raises:
        ValueError: If write mode is not in supported modes
        RuntimeError: If no part files are produced by Spark write operation

    Output Structure:
        Multiple CSV files: output_000.csv, output_001.csv, etc.
        Each file contains complete CSV with headers (if enabled) and subset of total
        data.

    Performance Benefits:
        - Full cluster parallelism during write operation
        - No single-executor bottleneck like coalesce strategy
        - Optimal for datasets larger than single-node processing capacity
        - Enables downstream parallel processing of individual files

    Note:
        Each output file is a complete, valid CSV with headers. Header duplication
        across files is intentional to maintain file independence and validity.
    """
    tmp_dir = _create_temp_directory(shared_mount, "spark_csv")

    # Validate write mode
    valid_modes = {"overwrite", "append", "ignore", "error"}
    if mode not in valid_modes:
        raise ValueError(f"Invalid write mode '{mode}'. Valid modes: {valid_modes}")

    try:
        _csv_logger.info("Created temporary directory: %s", tmp_dir)

        # Build writer with options
        writer = (
            df.write.mode(mode)
            .option("header", header)
            .option("sep", sep)
            .option("encoding", encoding)
            .option("quote", quote)
            .option("escape", escape)
        )

        # Add additional options
        for key, value in options.items():
            writer = writer.option(key, value)

        # Distributed Spark write
        writer.csv(str(tmp_dir))

        # Find all part files
        part_files = list(tmp_dir.glob("part-*.csv"))
        if not part_files:
            part_files = [
                f
                for f in tmp_dir.glob("part-*")
                if f.is_file() and not f.name.endswith((".crc", "_SUCCESS"))
            ]

        if not part_files:
            raise RuntimeError("No part files found after Spark write operation")

        _csv_logger.info("Found %d Spark output files", len(part_files))

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Distributed strategy keeps separate files for maximum performance
        _csv_logger.info("Creating separate CSV files for maximum performance")
        _rename_and_move_files(part_files, output_path, "CSV")
        _csv_logger.info(
            "CSV files written successfully (Spark distributed, multiple files): %s_*",
            output_path.stem,
        )

    finally:
        _cleanup_temp_directory(tmp_dir)


def _write_csv_pandas_fallback(
    df: DataFrame,
    output_path: Path,
    header: bool,
    sep: str,
    mode: str,
    encoding: str,
    quote: str,
    escape: str,
) -> None:
    """
    Write CSV using pandas fallback strategy for maximum compatibility and append
    support.

    This fallback strategy converts the entire Spark DataFrame to pandas and writes
    using pandas' native CSV capabilities with advanced append functionality. Provides
    maximum compatibility with edge cases, complex formatting scenarios, and
    sophisticated
    append mode that can merge with existing CSV files. Limited by driver node memory
    capacity but offers the most flexible CSV operations.

    Key Features:
        - Intelligent append mode with existing CSV data merging
        - Automatic fallback from malformed existing files to overwrite mode
        - Full CSV formatting control (delimiters, quotes, escaping, encoding)
        - Robust error handling for file system and data issues
        - Cross-platform encoding support for international data

    Args:
        df: Spark DataFrame to collect and write via pandas conversion
        output_path: Target file path for single CSV output file
        header: Whether to include column headers in output file
        sep: Field delimiter character (comma, semicolon, tab, etc.)
        mode: Write mode - supports 'overwrite' and 'append'
              - 'overwrite': Replace existing file completely
              - 'append': Merge new records with existing CSV data
        encoding: Character encoding for output file (UTF-8, latin-1, cp1252, etc.)
        quote: Quote character for fields containing delimiters or special characters
        escape: Escape character for handling quotes within quoted fields

    Raises:
        ValueError: If mode is not in ['overwrite', 'append']
        RuntimeError: If pandas write operation fails due to I/O issues
        MemoryError: If DataFrame is too large to collect on driver node

    Append Mode Behavior:
        - Loads existing CSV file and parses with matching format parameters
        - Appends new DataFrame records to existing data maintaining column structure
        - Falls back to overwrite mode if existing file is malformed or unreadable
        - Preserves formatting consistency (delimiter, encoding) across all records

    Performance Characteristics:
        - Single-threaded operation on driver node
        - Memory usage: Entire dataset + existing file must fit in driver memory
        - Network overhead: All data transferred to driver for processing
        - Compatibility: Highest, handles complex CSV scenarios and edge cases

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
        _csv_logger.info("Converting Spark DataFrame to pandas...")

        # Collect all data to driver node
        pandas_df = df.toPandas()
        _csv_logger.info("Collected %d records to driver node", len(pandas_df))

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Handle different write modes
        if mode == "append" and output_path.exists():
            # Load existing data and append
            try:
                existing_df = pd.read_csv(output_path, encoding=encoding, sep=sep)
                combined_df = pd.concat([existing_df, pandas_df], ignore_index=True)
                _csv_logger.info(
                    "Appending %d new records to %d existing records",
                    len(pandas_df),
                    len(existing_df),
                )
            except (pd.errors.EmptyDataError, FileNotFoundError) as e:
                _csv_logger.warning(
                    "Could not read existing file, treating as overwrite: %s", str(e)
                )
                combined_df = pandas_df
        else:
            combined_df = pandas_df

        # Write CSV using pandas
        combined_df.to_csv(
            output_path,
            index=False,
            header=header,
            sep=sep,
            encoding=encoding,
            quotechar=quote,
            escapechar=escape if escape != quote else None,
        )

        _csv_logger.info(
            "CSV written successfully (pandas fallback): %s (%d total records)",
            output_path,
            len(combined_df),
        )

    except Exception as e:
        raise RuntimeError(
            f"Could not save the file (please verify the path, write permissions, and "
            f"available "
            f"disk space) : CSV via pandas fallback: {str(e)}"
        ) from e


def write_csv(
    df: DataFrame,
    output_path: Union[str, Path],
    *,
    shared_mount: Optional[Union[str, Path]] = None,
    header: bool = True,
    sep: str = ",",
    mode: str = "overwrite",
    strategy: str = "coalesce",
    encoding: str = "UTF-8",
    quote: str = '"',
    escape: str = '"',
    **options: Any,
) -> None:
    """
    Export Spark DataFrame to CSV format with intelligent strategy selection and
    comprehensive formatting control.

    Provides enterprise-grade CSV export functionality with multiple optimized writing
    strategies
    for different use cases, from standard ETL workflows to high-performance data
    processing
    pipelines. This function offers complete control over CSV formatting including
    delimiters,
    encoding, quoting, and escaping while ensuring RFC 4180 compliance and
    cross-platform
    compatibility.

    The function supports three distinct strategies optimized for different scenarios:
    - **Coalesce**: Single CSV file optimal for ETL workflows and data exchange
    - **Distributed**: Multiple CSV files leveraging full cluster parallelism for big
      data
    - **Pandas**: Maximum compatibility with sophisticated append operations and edge
      case handling

    Args:
        df: Spark DataFrame containing the data to export. All Spark SQL data types
            are automatically converted to appropriate CSV string representations with
            proper escaping and formatting.
        output_path: Target file path or base name for CSV output. For single-file
                    strategies ('coalesce', 'pandas'), should include the .csv
                    extension.
                    For distributed strategy, becomes the base name for numbered files.
        shared_mount: Path to shared filesystem accessible by all cluster nodes (driver
                     and executors). Required for 'coalesce' and 'distributed'
                     strategies.
                     Common examples: NFS mounts, shared network drives, HDFS, cloud
                     storage.
                     If None, automatically falls back to pandas strategy.
        header: Whether to include column names as first row in CSV output. Enables
               proper column identification for downstream processing and analysis
               tools.
        sep: Field delimiter character separating values in each row:
             - ',' (default): Standard comma-separated values
             - ';': European standard, common in locales where comma is decimal
               separator
             - '\t': Tab-separated values (TSV) for database imports
             - '|': Pipe-separated for systems requiring comma preservation
             - Custom characters for specialized formats
        mode: Write mode determining behavior when output already exists:
              - 'overwrite': Replace existing files completely (default, safest for ETL)
              - 'append': Add new data to existing CSV files (pandas strategy only)
              - 'ignore': Skip write operation if output exists (idempotent behavior)
              - 'error': Fail with exception if output exists (strict safety mode)
        strategy: Write strategy selection based on performance and compatibility
                 requirements:
                 - 'coalesce': Single CSV file via coalesce(1). Optimal for data
                   exchange,
                   ETL pipelines, and when downstream systems expect single files. May
                   become
                   bottleneck for very large datasets due to single-executor processing.
                 - 'distributed': Multiple CSV files preserving natural Spark
                   parallelism.
                   Optimal for big data scenarios, high-throughput processing, and when
                   downstream systems can handle multiple files. Enables maximum write
                   performance.
                 - 'pandas': Single file via pandas conversion with advanced append
                   support.
                   Compatibility fallback for edge cases, complex append operations, or
                   when
                   cluster shared storage is unavailable. Limited by driver memory
                   capacity.
        encoding: Character encoding for CSV output files:
                 - 'UTF-8' (default): Universal encoding supporting international
                   characters
                 - 'latin-1': Western European encoding for legacy system compatibility
                 - 'cp1252': Windows encoding for Microsoft Excel compatibility
                 - 'ascii': Basic ASCII encoding for maximum system compatibility
        quote: Quote character for enclosing fields containing special characters:
              - '"' (default): Standard CSV double-quote character
              - "'": Single quote for specialized formats
              - Custom characters for specific requirements
        escape: Escape character for handling quotes within quoted fields:
               - '"' (default): Double-quote escaping (standard CSV behavior)
               - '\\': Backslash escaping for programmatic processing
               - Custom characters for specialized escape sequences
        **options: Additional Spark DataFrameWriter options passed directly to
                  underlying
                  CSV writer. Common options include:
                  - 'dateFormat': Date formatting pattern (default: 'yyyy-MM-dd')
                  - 'timestampFormat': Timestamp formatting pattern (default:
                    'yyyy-MM-dd HH:mm:ss')
                  - 'nullValue': String representation for null values (default: empty
                    string)
                  - 'compression': Enable compression ('gzip', 'bzip2', 'xz', 'lz4')

    Raises:
        ValueError: If strategy is not in ['coalesce', 'distributed', 'pandas'], if mode
                   is not valid for the selected strategy, or if delimiter/quote
                   characters
                   create formatting conflicts.
        RuntimeError: If write operation fails due to insufficient disk space,
                     permission
                     errors, network connectivity issues with shared_mount, or if no
                     output
                     files are produced by Spark operations.
        MemoryError: If using pandas strategy with datasets too large for driver memory,
                    or if shared_mount is unavailable and fallback to pandas fails.
        PermissionError: If output_path or shared_mount directories are not writable
                        by the Spark processes.

    Performance Guidelines:
        **Small datasets (< 100MB)**:
        - Use 'coalesce' or 'pandas' strategy with standard formatting
        - Single file simplifies downstream CSV processing
        - Memory and network overhead is minimal

        **Medium datasets (100MB - 10GB)**:
        - Use 'coalesce' for single-file requirements
        - Use 'distributed' for maximum write performance
        - Consider compression options for network-attached storage

        **Large datasets (> 10GB)**:
        - Use 'distributed' strategy exclusively
        - Implement partitioning in upstream processing for optimal file sizes
        - Use efficient encodings and disable headers for space optimization

        **International data**:
        - Always use UTF-8 encoding for international character support
        - Test delimiter choice with actual data to avoid conflicts
        - Consider locale-specific formatting patterns for dates/numbers

    Examples:
        Standard ETL data export with default settings:

         write_csv(df, "monthly_sales.csv")

        European format with semicolon delimiter for Excel compatibility:

         write_csv(df, "european_data.csv", sep=";", encoding="utf-8")

        High-performance distributed export for big data processing:

         write_csv(large_df, "distributed_export",
        ...            shared_mount="/data/shared",
        ...            strategy="distributed")

        Tab-separated values for database import with custom null handling:

         write_csv(df, "database_import.tsv",
        ...            sep="\t", nullValue="NULL", header=True)

        Incremental data loading with intelligent append mode:

         write_csv(new_records_df, "incremental_data.csv",
        ...            strategy="pandas", mode="append")

        Legacy system compatibility with custom encoding and formatting:

         write_csv(df, "legacy_export.csv",
        ...            encoding="cp1252", quote="'", escape="\\")

        Compressed output for network transfer optimization:

         write_csv(df, "compressed_data.csv",
        ...            compression="gzip",
        ...            dateFormat="MM/dd/yyyy")

    CSV Format Standards:
        **RFC 4180 Compliance**: Ensures maximum compatibility with CSV parsers
        **Field Structure**: Each record on separate line, fields separated by delimiter
        **Quoting Rules**: Fields containing delimiter, quote, or newline are quoted
        **Escape Handling**: Quote characters within fields are escaped appropriately
        **Header Format**: Column names in first row when header=True
        **Encoding Standards**: Proper character encoding with BOM handling when needed

    Regional Format Support:
        **US/International**: Comma delimiter with period decimal separator
        **European**: Semicolon delimiter accommodating comma decimal separator
        **Nordic**: Tab delimiter for multilingual character preservation
        **Database**: Pipe delimiter avoiding conflicts with text data
        **Custom**: Configurable delimiters for specialized formats

    See Also:
        - Parquet export: ``write_parquet()`` for columnar analytics format
        - Excel export: ``write_excel()`` for business reporting and presentations
        - JSON export: ``write_json()`` for API integration and web applications
        - Text export: ``write_positional()`` for fixed-width legacy system integration

    Warning:
        The 'distributed' strategy creates multiple CSV files which some downstream
        systems may not handle automatically. Each file includes headers when enabled,
        requiring header deduplication in downstream processing if needed.

    Note:
        CSV format is universally supported but can be less efficient than columnar
        formats like Parquet for analytical workloads. Consider Parquet for large-scale
        analytics and CSV for data exchange, reporting, and system integration
        scenarios.
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
            _csv_logger.warning(
                "Distributed strategy requires shared_mount, falling back to pandas"
            )
            _write_csv_pandas_fallback(
                df, output_path, header, sep, mode, encoding, quote, escape
            )
        else:
            _csv_logger.info(
                "Using distributed strategy - parallel write with multiple files"
            )
            _write_csv_spark_distributed(
                df,
                output_path,
                shared_mount,
                header,
                sep,
                mode,
                encoding,
                quote,
                escape,
                options,
            )
    elif strategy == "pandas":
        _csv_logger.info("Using pandas strategy - maximum compatibility")
        _write_csv_pandas_fallback(
            df, output_path, header, sep, mode, encoding, quote, escape
        )
    else:  # strategy == "coalesce" (default)
        if shared_mount is None:
            _csv_logger.info(
                "Coalesce strategy without shared_mount - using pandas fallback"
            )
            _write_csv_pandas_fallback(
                df, output_path, header, sep, mode, encoding, quote, escape
            )
        else:
            _csv_logger.info("Using coalesce strategy - single file via coalesce(1)")
            _write_csv_spark_coalesced(
                df,
                output_path,
                shared_mount,
                header,
                sep,
                mode,
                encoding,
                quote,
                escape,
                options,
            )
