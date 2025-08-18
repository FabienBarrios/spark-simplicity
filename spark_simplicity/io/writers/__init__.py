"""
Spark Simplicity - I/O Writers Package
======================================

High-performance, production-ready writers for exporting Spark DataFrames to various
formats with intelligent strategy selection and comprehensive formatting control.
This package provides enterprise-grade export capabilities supporting multiple output
strategies optimized for different use cases and data processing scenarios.

**Supported Output Formats:**
    - **CSV**: Comma-separated values with full RFC 4180 compliance and international
      support
    - **JSON**: JavaScript Object Notation with proper array formatting and
      pretty-print options
    - **Parquet**: Apache Parquet columnar format with advanced compression and
      partitioning
    - **Excel**: Microsoft Excel .xlsx format with professional formatting and business
      features
    - **Positional**: Fixed-width text files for mainframe and legacy system integration

**Writing Strategies:**
    All format writers support multiple optimized strategies:

    - **Coalesce Strategy**: Single output file via coalesce(1), optimal for ETL
      workflows
      and data exchange scenarios where downstream systems expect single files.

    - **Distributed Strategy**: Multiple output files preserving Spark's natural
      parallelism,
      optimal for big data scenarios and maximum write throughput.

    - **Pandas Strategy**: Single file via pandas conversion with advanced compatibility
      features and sophisticated append operations.

**Key Features:**
    - **Intelligent Fallback**: Automatic strategy selection based on available
      resources
    - **Cross-Platform Support**: Windows, Linux, and macOS compatibility with native
      optimizations
    - **International Support**: Full Unicode and regional formatting support for
      global deployments
    - **Production Safety**: Comprehensive error handling, validation, and resource
      cleanup
    - **Performance Optimization**: Memory-efficient processing with configurable
      resource limits
    - **Shared Storage Support**: NFS, HDFS, and cloud storage compatibility for
      cluster environments

**Enterprise Features:**
    - **Atomic Operations**: File operations with rollback capability on failures
    - **Comprehensive Logging**: Detailed operation logging for monitoring and debugging
    - **Resource Management**: Automatic temporary file cleanup and memory management
    - **Format Validation**: Input validation and format compliance checking
    - **Append Operations**: Intelligent data merging for incremental processing
      workflows

**Usage Examples:**

    Basic CSV export for ETL workflows:

     from spark_simplicity.io.writers import write_csv
     write_csv(df, "output.csv")

    High-performance distributed Parquet export:

     from spark_simplicity.io.writers import write_parquet
     write_parquet(large_df, "data_lake/table",
    ...               strategy="distributed",
    ...               partition_by=["year", "month"],
    ...               compression="zstd")

    Professional Excel reports for business users:

     from spark_simplicity.io.writers import write_excel
     write_excel(report_df, "quarterly_report.xlsx",
    ...             sheet_name="Q4_Results")

    Legacy mainframe integration with fixed-width format:

     from spark_simplicity.io.writers import write_positional
     column_specs = [('id', 8), ('name', 25), ('amount', 12)]
     write_positional(df, "mainframe.dat", column_specs)

**Performance Guidelines:**
    - **Small datasets (< 100MB)**: Use coalesce or pandas strategies
    - **Medium datasets (100MB - 10GB)**: Choose strategy based on downstream
      requirements
    - **Large datasets (> 10GB)**: Use distributed strategy with appropriate
      partitioning

**Format Selection Guide:**
    - **CSV**: Universal compatibility, data exchange, database imports
    - **Parquet**: Analytics, data lakes, columnar analysis, long-term storage
    - **JSON**: APIs, web applications, configuration data, semi-structured data
    - **Excel**: Business reports, executive dashboards, manual analysis
    - **Positional**: Legacy systems, mainframe integration, fixed-format requirements

Note:
    All writers in this package are designed for production use with comprehensive
    error handling, resource management, and performance optimization. They provide
    consistent interfaces while leveraging format-specific optimizations for
    maximum efficiency and reliability.
"""

from .csv_writer import write_csv
from .excel_writer import write_excel
from .json_writer import write_json
from .parquet_writer import write_parquet
from .text_writer import write_positional

__all__ = [
    "write_csv",
    "write_json",
    "write_parquet",
    "write_excel",
    "write_positional",
]
