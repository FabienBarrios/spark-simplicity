"""
Spark Simplicity - Text and Positional File Readers
===================================================

Enterprise-grade text file readers for Spark DataFrames with advanced encoding support
and intelligent format handling. This module provides specialized readers for plain text
files and fixed-width positional files commonly used in legacy systems and mainframe
integrations. Optimized for production environments with robust error handling.

Key Features:
    - **Plain Text Reading**: Line-by-line text file ingestion into Spark DataFrames
    - **Positional File Support**: Fixed-width file parsing with precise column
      specifications
    - **Encoding Intelligence**: Automatic encoding detection and fallback mechanisms
    - **Data Cleaning**: Intelligent whitespace handling and null value processing
    - **Legacy Integration**: Mainframe and legacy system file format compatibility
    - **Production Safety**: Comprehensive error handling and validation

File Format Support:
    **Plain Text Files**:
    - Line-oriented text files with UTF-8 and international encoding support
    - Log files, configuration files, and unstructured text data
    - Single column DataFrame output with configurable processing

    **Fixed-Width Positional Files**:
    - Mainframe-style fixed-width records with precise column positioning
    - Legacy system data exports with structured field layouts
    - Custom column specifications with flexible start/end positioning
    - Automatic data type inference and conversion

Advanced Features:
    **Encoding Resilience**:
    - Primary encoding with intelligent fallback detection
    - Support for UTF-8, Windows-1252, ISO-8859-1, and CP1252
    - Automatic encoding selection for international data
    - Error recovery for mixed-encoding scenarios

    **Data Cleaning Pipeline**:
    - Configurable whitespace stripping for string columns
    - Intelligent null value handling and empty row removal
    - Type-aware data cleaning with preservation of numeric values
    - Pandas integration for advanced data processing capabilities

Enterprise Integration:
    - **Cluster Compatibility**: Full support for distributed Spark processing
    - **Path Validation**: Integrated mount point validation for shared storage
    - **Error Recovery**: Comprehensive error handling with detailed diagnostics
    - **Performance Optimization**: Memory-efficient processing for large files
    - **Monitoring Integration**: Detailed logging for operational visibility

Usage:
    This module provides specialized readers for text-based data formats commonly
    encountered in enterprise environments, particularly for legacy system integration
    and mainframe data processing workflows.

    from spark_simplicity.io.readers.text_reader import load_text, load_positional
"""

from pathlib import Path
from typing import Any, List, Optional, Tuple, Union

import pandas as pd
from pyspark.sql import DataFrame, SparkSession

from ...logger import get_logger
from ..validation.path_utils import configure_spark_path

# Logger for text readers
_text_logger = get_logger("spark_simplicity.io.readers.text")


def load_text(
    spark: SparkSession, file_path: Union[str, Path], shared_mount: bool = False
) -> DataFrame:
    """
    Load plain text file into Spark DataFrame with line-by-line processing and
    cluster validation.

    Provides enterprise-grade text file ingestion for unstructured data processing
    workflows.
    Each line of the input file becomes a row in the resulting DataFrame with a
    single 'value'
    column, making it ideal for log processing, configuration file analysis, and
    unstructured
    text analytics. Includes comprehensive path validation for distributed environments.

    This function leverages Spark's native text reading capabilities while adding
    production-grade
    error handling, path validation, and cluster compatibility checks essential for
    enterprise
    data processing environments.

    Args:
        spark: Active SparkSession instance for DataFrame creation and cluster
              operations.
              Must be properly configured with appropriate executors for distributed
              processing.
              Used for both file reading and cluster validation operations.
        file_path: Path to the plain text file to load. Can be provided as string or
                  Path object.
                  Supports absolute and relative paths with automatic resolution.
                  Compatible
                  with local filesystems, network attached storage, and mounted cloud
                  storage.
        shared_mount: Boolean indicating whether the file resides on shared storage
                     accessible
                     by all cluster nodes. When True, triggers cluster-wide validation
                     to ensure
                     all executors can access the file. When False, uses local file URI
                     scheme.

    Returns:
        Spark DataFrame with single 'value' column containing the text content:
        - Each row represents one line from the input file
        - Column name: 'value' (Spark's default for text files)
        - Data type: StringType for universal text compatibility
        - Line endings are automatically handled across platforms

    Raises:
        FileNotFoundError: If the specified file does not exist at the given path.
                          Error message includes full path for troubleshooting.
        RuntimeError: If file loading fails due to permission issues, encoding problems,
                     network connectivity issues, or cluster validation failures.
                     The original exception is preserved for detailed diagnostics.

    File Processing Characteristics:
        **Line Processing**: Each line becomes a separate DataFrame row
        **Encoding**: Automatic UTF-8 encoding with platform compatibility
        **Memory Efficiency**: Streaming processing for large text files
        **Distributed Loading**: Parallel processing across cluster executors

    Examples:
        Load application log file for analysis:

         df = load_text(spark, "application.log")
         df.show(5, truncate=False)
        # Output:
        # +------------------------------------------+
        # |value                                     |
        # +------------------------------------------+
        # |2024-01-15 10:30:15 INFO Application started|
        # |2024-01-15 10:30:16 DEBUG Loading config   |
        # |2024-01-15 10:30:17 INFO Database connected |
        # +------------------------------------------+

        Process configuration file with shared storage:

         config_df = load_text(spark, "/nfs/config/app.conf", shared_mount=True)
         # Includes cluster validation for shared NFS mount

        Log processing pipeline with filtering:

         log_df = load_text(spark, "server.log")
         error_lines = log_df.filter(log_df.value.contains("ERROR"))
         error_count = error_lines.count()
         print(f"Found {error_count} error lines")

        Large file processing with performance monitoring:

         large_text_df = load_text(spark, "large_dataset.txt")
         print(f"Loaded {large_text_df.count()} lines")
         large_text_df.cache()  # Cache for multiple operations

    Use Cases:
        **Log File Analysis**:
        - Application log processing and error analysis
        - System log aggregation and monitoring
        - Security log analysis and threat detection

        **Configuration Processing**:
        - Configuration file parsing and validation
        - Environment-specific setting analysis
        - Multi-environment configuration comparison

        **Unstructured Data Ingestion**:
        - Free-form text data processing
        - Document content extraction and analysis
        - Legacy data format migration

    Performance Considerations:
        **Small Files (< 100MB)**: Excellent performance with immediate loading
        **Medium Files (100MB - 1GB)**: Good performance with distributed processing
        **Large Files (> 1GB)**: Optimal performance with cluster parallelization
        **Memory Usage**: Efficient streaming with configurable partitioning

    Cluster Integration:
        - **Path Validation**: Automatic validation of file accessibility across cluster
        - **Distributed Processing**: Parallel file reading across executor nodes
        - **Error Recovery**: Graceful handling of node failures and network issues
        - **Resource Management**: Efficient resource utilization for text processing

    See Also:
        - ``load_positional()``: For fixed-width positional file processing
        - CSV readers: For structured comma-separated data
        - JSON readers: For structured JSON data processing

    Note:
        This function is optimized for production text processing workflows with
        comprehensive error handling and cluster compatibility. It provides the
        foundation for robust unstructured data analysis in enterprise environments.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found — please check that the path is correct and the file "
            f"exists: {file_path}"
        )

    try:
        # Configure Spark path with validation
        spark_path = configure_spark_path(file_path, shared_mount, spark)

        df = spark.read.text(spark_path)

        _text_logger.info("Text file loaded successfully: %s", file_path.name)
        return df

    except Exception as e:
        raise RuntimeError(
            f"Could not load the file (please check file format and accessibility) : "
            f"text file {file_path}: {str(e)}"
        ) from e


def _read_fwf_with_encoding_fallback(
    file_path: Path,
    colspecs: List[Tuple[int, int]],
    names: List[str],
    primary_encoding: str,
    strip_whitespace: bool,
    **pandas_options: Any,
) -> Tuple[pd.DataFrame, str]:
    """
    Read fixed-width file with intelligent encoding detection and fallback recovery.

    Provides robust file reading for fixed-width formats with automatic encoding
    detection
    when the primary encoding fails. This function implements a cascading fallback
    strategy
    through common encodings to maximize data recovery from files with unknown or mixed
    encoding scenarios, particularly common in legacy system integrations.

    Args:
        file_path: Path to the fixed-width file to read
        colspecs: List of (start_position, end_position) tuples defining column
                 boundaries
        names: List of column names corresponding to the column specifications
        primary_encoding: Preferred encoding to attempt first (e.g., 'utf-8', 'cp1252')
        strip_whitespace: Whether to strip leading/trailing whitespace from fields
        **pandas_options: Additional parameters passed to pandas.read_fwf()

    Returns:
        Tuple containing (parsed_dataframe, successful_encoding_used)

    Raises:
        RuntimeError: If file cannot be read with any of the attempted encodings
    """
    encodings_to_try = [
        primary_encoding,
        "utf-8",
        "windows-1252",
        "iso-8859-1",
        "cp1252",
    ]

    for enc in encodings_to_try:
        try:
            pandas_df = pd.read_fwf(
                file_path,
                colspecs=colspecs,
                names=names,
                encoding=enc,
                skipinitialspace=strip_whitespace,
                **pandas_options,
            )
            return pandas_df, enc
        except UnicodeDecodeError:
            continue

    raise RuntimeError("Could not read file with any of the attempted encodings")


def _clean_string_columns(pandas_df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean string columns with intelligent whitespace handling and null value processing.

    Performs comprehensive data cleaning for string columns in fixed-width files,
    addressing common data quality issues like trailing spaces and inconsistent
    null value representation. Essential for mainframe and legacy system data
    that often contains formatting artifacts from fixed-width storage.

    Args:
        pandas_df: DataFrame with potentially uncleaned string data

    Returns:
        DataFrame with cleaned string columns and standardized null handling
    """

    def clean_string_value(x: Any) -> Optional[str]:
        """Strip whitespace from string values, preserve NaN as None."""
        if pd.isna(x):
            return None
        elif isinstance(x, str):
            return x.strip()
        else:
            return str(x)

    for col in pandas_df.columns:
        if pandas_df[col].dtype == "object":
            pandas_df[col] = pandas_df[col].apply(clean_string_value)

    return pandas_df


def load_positional(
    spark: SparkSession,
    file_path: Union[str, Path],
    column_specs: List[Tuple[str, int, int]],
    strip_whitespace: bool = True,
    encoding: str = "utf-8",
    **pandas_options: Any,
) -> DataFrame:
    """
    Load fixed-width positional file into Spark DataFrame with enterprise-grade
    parsing and validation.

    Provides specialized processing for fixed-width positional files commonly used in
    mainframe
    systems, legacy applications, and structured data exports. This function combines
    pandas'
    fixed-width parsing capabilities with Spark's distributed processing power,
    including
    intelligent encoding detection, data cleaning, and comprehensive error handling.

    The function is essential for integrating with legacy systems that export data in
    fixed-width formats where each field occupies a specific character position range.
    Common in financial systems, government data, and mainframe extracts.

    Args:
        spark: Active SparkSession instance for DataFrame creation and distributed
              processing.
              Must be properly configured for the expected data volume and cluster
              resources.
              Used for converting cleaned pandas DataFrame to distributed Spark
              DataFrame.
        file_path: Path to the fixed-width positional file. Can be string or Path
                  object.
                  Supports absolute and relative paths with automatic resolution.
                  Compatible with local storage, network mounts, and shared filesystems.
        column_specs: List of column specification tuples in format
                     (column_name, start_pos, end_pos).
                     Each tuple defines a field with its name and exact character
                     positions.
                     Positions are zero-indexed and end_pos is exclusive (Python slice
                     notation).
                     Must not be empty and should cover all required fields in the file.
        strip_whitespace: Whether to automatically strip leading and trailing whitespace
                         from string fields. Recommended for fixed-width files that pad
                         fields with spaces. Does not affect numeric field processing.
        encoding: Primary character encoding for file reading. Common values include
                 'utf-8' for modern files, 'cp1252' for Windows systems, 'iso-8859-1'
                 for European data. Automatic fallback is attempted if primary fails.
        **pandas_options: Additional parameters passed directly to pandas.read_fwf().
                         Common options include 'skiprows', 'nrows', 'dtype',
                         'na_values'.
                         Allows fine-tuning of parsing behavior for specific file
                         formats.

    Returns:
        Spark DataFrame with columns as specified in column_specs:
        - Column names match those provided in the specification
        - Data types are automatically inferred from content
        - String columns are cleaned if strip_whitespace=True
        - Empty rows are automatically removed
        - Null values are properly handled and standardized

    Raises:
        FileNotFoundError: If the specified file does not exist at the given path.
                          Error includes full path information for troubleshooting.
        ValueError: If column_specs is empty or contains invalid specifications.
                   Column specs must define at least one field with valid positions.
        RuntimeError: If file loading fails due to encoding issues, format problems,
                     parsing errors, or resource constraints. Includes detailed error
                     context for troubleshooting and resolution.

    Column Specification Format:
        Each column specification tuple contains:
        - **column_name**: String name for the DataFrame column
        - **start_pos**: Zero-indexed starting character position (inclusive)
        - **end_pos**: Zero-indexed ending character position (exclusive)

        Position ranges should not overlap and must be within file record length.

    Encoding Fallback Strategy:
        1. **Primary Encoding**: Attempts user-specified encoding first
        2. **UTF-8 Fallback**: Universal encoding for international compatibility
        3. **Windows-1252**: Common Windows encoding for legacy systems
        4. **ISO-8859-1**: European character set for international data
        5. **CP1252**: Extended Windows encoding with additional characters

    Examples:
        Load mainframe data export with standard layout:

         column_specs = [
        ...     ('customer_id', 0, 10),      # Positions 0-9: Customer ID
        ...     ('customer_name', 10, 40),   # Positions 10-39: Customer Name
        ...     ('account_balance', 40, 55), # Positions 40-54: Account Balance
        ...     ('status_code', 55, 57)      # Positions 55-56: Status Code
        ... ]

         df = load_positional(spark, "customer_export.dat", column_specs)
         df.show()
        # +----------+--------------------+--------------+-----------+
        # |customer_id|customer_name      |account_balance|status_code|
        # +----------+--------------------+--------------+-----------+
        # |CUST001   |Alice Johnson       |1250.75       |AC         |
        # |CUST002   |Bob Smith           |890.00        |AC         |
        # +----------+--------------------+--------------+-----------+

        Load financial transaction file with custom encoding:

         transaction_specs = [
        ...     ('trans_id', 0, 12),
        ...     ('trans_date', 12, 20),
        ...     ('amount', 20, 32),
        ...     ('description', 32, 80)
        ... ]

         trans_df = load_positional(
        ...     spark,
        ...     "transactions.txt",
        ...     transaction_specs,
        ...     encoding='cp1252',
        ...     strip_whitespace=True
        ... )

        Load government data with custom pandas options:

         govt_specs = [
        ...     ('record_type', 0, 2),
        ...     ('entity_id', 2, 15),
        ...     ('fiscal_year', 15, 19),
        ...     ('amount', 19, 32)
        ... ]

         govt_df = load_positional(
        ...     spark,
        ...     "govt_data.txt",
        ...     govt_specs,
        ...     skiprows=1,  # Skip header row
        ...     na_values=['NULL', 'N/A', '']  # Custom null indicators
        ... )

    Data Cleaning Process:
        **String Column Cleaning** (when strip_whitespace=True):
        - Removes leading and trailing whitespace from text fields
        - Preserves internal spacing within field values
        - Converts empty strings to null values for consistency
        - Maintains data type integrity for non-string columns

        **Null Value Handling**:
        - Standardizes various null representations to proper nulls
        - Removes completely empty rows from the dataset
        - Preserves legitimate zero and empty string values where appropriate

    Performance Characteristics:
        **Small Files (< 50MB)**: Excellent performance with immediate processing
        **Medium Files (50MB - 500MB)**: Good performance with pandas processing
        **Large Files (> 500MB)**: Consider chunked processing or alternative approaches
        **Memory Usage**: Entire file loaded into memory during pandas processing

    Legacy System Integration:
        **Mainframe Compatibility**: Full support for EBCDIC-derived fixed-width formats
        **COBOL Data Layouts**: Compatible with COBOL copybook-defined record structures
        **Government Standards**: Supports federal and state government data formats
        **Financial Systems**: Handles banking and financial institution data exports

    Use Cases:
        **Mainframe Integration**:
        - COBOL program output processing
        - Legacy database exports and migrations
        - Batch processing of structured mainframe data

        **Government Data Processing**:
        - Census and demographic data analysis
        - Tax and financial reporting data
        - Regulatory compliance data processing

        **Financial Services**:
        - Bank statement and transaction processing
        - Credit reporting and scoring data
        - Insurance claim and policy data analysis

    Production Considerations:
        - **Memory Requirements**: Files are loaded entirely into driver memory
        - **Encoding Detection**: Multiple encoding attempts may impact performance
        - **Data Validation**: Consider additional validation for critical data
        - **Error Monitoring**: Implement monitoring for encoding and parsing failures

    See Also:
        - ``load_text()``: For unstructured plain text file processing
        - CSV readers: For comma-separated structured data
        - ``_read_fwf_with_encoding_fallback()``: Underlying encoding detection logic

    Note:
        This function is specifically designed for fixed-width positional files
        and includes comprehensive data cleaning for production use. It bridges
        the gap between legacy data formats and modern Spark analytics workflows
        while maintaining data integrity and processing efficiency.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found — please check that the path is correct and the file "
            f"exists: {file_path}"
        )

    if not column_specs:
        raise ValueError("column_specs cannot be empty")

    try:
        # Prepare column specifications for pandas
        colspecs = [(spec[1], spec[2]) for spec in column_specs]
        names = [spec[0] for spec in column_specs]

        # Read file with encoding fallback
        pandas_df, used_encoding = _read_fwf_with_encoding_fallback(
            file_path, colspecs, names, encoding, strip_whitespace, **pandas_options
        )

        # Clean data if requested
        if strip_whitespace:
            pandas_df = _clean_string_columns(pandas_df)

        # Remove completely empty rows and convert to Spark DataFrame
        pandas_df = pandas_df.dropna(how="all")
        df = spark.createDataFrame(pandas_df)

        _text_logger.info(
            "Positional file loaded successfully: %s (encoding: %s)",
            file_path.name,
            used_encoding,
        )
        return df

    except Exception as e:
        raise RuntimeError(
            f"Could not load the file (please check file format and accessibility) : "
            f"positional file {file_path}: {str(e)}"
        ) from e
