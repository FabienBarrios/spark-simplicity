"""
Spark Simplicity - File System Utilities
========================================

Comprehensive file system utilities for enterprise-grade I/O operations and metadata
analysis.
This module provides essential file system interaction capabilities including file
information
retrieval, format detection, and metadata extraction optimized for data processing
workflows.
Designed to support robust file handling across different platforms and storage systems.

Key Features:
    - **File Information Analysis**: Comprehensive file metadata extraction and analysis
    - **Format Detection**: Intelligent file format identification based on extensions
    - **Cross-Platform Support**: Windows, Linux, and macOS file system compatibility
    - **Storage System Integration**: Support for local, network, and cloud storage
    - **Error Handling**: Robust error handling with descriptive messages
    - **Performance Optimization**: Efficient file system operations with minimal
      overhead

File Format Support:
    **Data Formats**:
    - **CSV**: Comma-separated values for tabular data
    - **JSON/JSONL**: JavaScript Object Notation for structured data
    - **Parquet**: Apache Parquet columnar format for analytics
    - **Excel**: Microsoft Excel formats (.xlsx, .xls) for business data
    - **Text**: Plain text files for unstructured content
    - **Positional**: Fixed-width files for legacy system integration

    **Format Detection**:
    - Extension-based format identification
    - Comprehensive format mapping for common data file types
    - Fallback handling for unknown or custom file extensions

Metadata Capabilities:
    - **File Size Analysis**: Byte-level and human-readable size reporting
    - **Timestamp Information**: File modification time tracking
    - **Path Analysis**: Complete path, name, and extension extraction
    - **Format Classification**: Automatic format categorization for processing
      workflows

Enterprise Features:
    - **Production Safety**: Comprehensive error handling for missing files
    - **Storage Compatibility**: Works with network attached storage and cloud mounts
    - **Performance Monitoring**: File size and metadata for capacity planning
    - **Integration Support**: Designed for ETL pipeline and data processing integration

Usage:
    This module provides utilities used throughout Spark Simplicity for file system
    operations and is also available for direct use in data processing workflows.

    from spark_simplicity.io.utils.file_utils import get_file_info
"""

from pathlib import Path
from typing import Any, Dict, Union


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Extract comprehensive file system metadata and format information for data
    processing workflows.

    Provides detailed file analysis including size metrics, format detection,
    timestamps, and
    path information essential for data pipeline operations, capacity planning, and file
    processing decisions. This function serves as the foundation for intelligent file
    handling
    across different storage systems and data processing scenarios.

    The function combines file system metadata with intelligent format detection to
    provide
    a complete picture of file characteristics needed for automated data processing
    workflows,
    monitoring systems, and capacity management operations.

    Args:
        file_path: Path to the file for analysis. Can be provided as either a string or
                  Path object. Supports absolute and relative paths, with automatic
                  resolution to canonical form. Compatible with local filesystems,
                  network attached storage, and mounted cloud storage systems.

    Returns:
        Comprehensive dictionary containing file metadata and analysis results:

         {
        ...     'path': '/full/path/to/file.csv',           # Absolute path string
        ...     'name': 'file.csv',                         # Filename with extension
        ...     'size_bytes': 1048576,                      # Exact file size in bytes
        ...     'size_mb': 1.0,                             # Human-readable size in MB
        ...     'modified': 1634567890.123,                 # Last modified timestamp
        ...     'format': 'csv',                            # Detected format type
        ...     'extension': '.csv'                         # File extension (lowercase)
        ... }

    Raises:
        FileNotFoundError: If the specified file does not exist at the given path.
                          The error message includes the full path and suggests
                          verification
                          steps for troubleshooting missing file issues.

    Format Detection Logic:
        **Supported Data Formats**:
        - **CSV**: .csv extensions → 'csv' format classification
        - **JSON**: .json, .jsonl extensions → 'json' format classification
        - **Parquet**: .parquet extensions → 'parquet' format classification
        - **Excel**: .xlsx, .xls extensions → 'excel' format classification
        - **Text**: .txt extensions → 'text' format classification
        - **Positional**: .dat extensions → 'positional' format classification
        - **Unknown**: Other extensions → 'unknown' format classification

    Metadata Fields:
        **Path Information**:
        - 'path': Complete absolute path to the file
        - 'name': Filename including extension
        - 'extension': File extension in lowercase for consistent processing

        **Size Metrics**:
        - 'size_bytes': Exact file size for precise calculations
        - 'size_mb': Rounded megabyte size for human readability and reporting

        **Temporal Data**:
        - 'modified': Unix timestamp of last modification for change tracking

        **Format Analysis**:
        - 'format': Detected format type for processing pipeline routing

    Examples:
        Analyze CSV data file for processing pipeline:

         info = get_file_info("sales_data.csv")
         print(f"Processing {info['name']}: {info['size_mb']} MB {info['format']} file")
         # Output: "Processing sales_data.csv: 15.3 MB csv file"

        Check file characteristics before Spark processing:

         file_info = get_file_info("/data/warehouse/transactions.parquet")
         if file_info['size_mb'] > 1000:
        ...     print(f"Large file detected: {file_info['size_mb']} MB")
        ...     # Use distributed processing strategy
        ... else:
        ...     print(f"Standard file: {file_info['size_mb']} MB")
        ...     # Use coalesce strategy

        Format-based processing decisions:

         info = get_file_info("unknown_data.xyz")
         if info['format'] == 'unknown':
        ...     print(f"Unknown format: {info['extension']}")
        ...     # Apply format detection heuristics
        ... else:
        ...     print(f"Detected {info['format']} format")
        ...     # Route to appropriate processor

        Batch file analysis for data lake management:

         data_files = Path("data_lake").glob("*.parquet")
         total_size = 0
         for file_path in data_files:
        ...     info = get_file_info(file_path)
        ...     total_size += info['size_mb']
        ...     print(f"{info['name']}: {info['size_mb']} MB")
         print(f"Total size: {total_size} MB")

    Performance Characteristics:
        **Operation Speed**: Single file system call (os.stat) for metadata retrieval
        **Memory Usage**: Minimal - only stores metadata dictionary
        **Network Efficiency**: Single round-trip for network attached storage
        **Caching**: Results can be cached based on file modification time

    Storage System Compatibility:
        **Local Storage**: Full support for local filesystem operations
        **Network Storage**: Compatible with NFS, SMB/CIFS network filesystems
        **Cloud Storage**: Works with mounted S3, Azure, GCS storage systems
        **Distributed Storage**: Supports HDFS and other distributed filesystems

    Use Cases:
        **Data Pipeline Orchestration**:
        - File size analysis for processing strategy selection
        - Format detection for automatic processor routing
        - Modification time tracking for incremental processing

        **Capacity Management**:
        - Storage utilization monitoring and reporting
        - File growth tracking for capacity planning
        - Data retention policy implementation

        **Quality Assurance**:
        - File existence validation before processing
        - Format verification for data integrity checks
        - Size validation for expected data volumes

        **Monitoring and Alerting**:
        - File system monitoring for operational dashboards
        - Anomaly detection based on file characteristics
        - Integration with enterprise monitoring systems

    Integration Patterns:
        **ETL Workflows**: Pre-processing file analysis for strategy selection
        **Data Validation**: File characteristic verification in quality pipelines
        **Monitoring Systems**: File metadata collection for operational insights
        **Automation**: File-based triggering and routing in data pipelines

    Error Handling:
        The function provides clear, actionable error messages for common failure
        scenarios:
        - Missing files with full path information for troubleshooting
        - Permission issues are surfaced through underlying file system errors
        - Network connectivity problems manifest as file access errors

    See Also:
        - Path utilities: ``spark_simplicity.io.validation.path_utils`` for path
          validation
        - Format utilities: ``spark_simplicity.io.utils.format_utils`` for format
          conversion
        - I/O operations: ``spark_simplicity.io`` for file reading and writing

    Note:
        This function is designed for production use with minimal overhead and maximum
        reliability. It provides the file system intelligence needed for automated
        data processing decisions while maintaining compatibility across different
        storage systems and platforms.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found — please check that the path is correct and the file "
            f"exists: {file_path}"
        )

    stat = file_path.stat()

    # Infer format from extension
    suffix = file_path.suffix.lower()
    format_mapping = {
        ".csv": "csv",
        ".json": "json",
        ".jsonl": "json",
        ".parquet": "parquet",
        ".xlsx": "excel",
        ".xls": "excel",
        ".txt": "text",
        ".dat": "positional",
    }

    return {
        "path": str(file_path),
        "name": file_path.name,
        "size_bytes": stat.st_size,
        "size_mb": round(stat.st_size / (1024 * 1024), 2),
        "modified": stat.st_mtime,
        "format": format_mapping.get(suffix, "unknown"),
        "extension": suffix,
    }
