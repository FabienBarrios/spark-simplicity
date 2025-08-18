"""
Spark Simplicity - I/O Readers Package
======================================

Comprehensive data ingestion library for enterprise-grade Spark DataFrame processing.
This package provides high-performance, production-ready readers for all major data
formats with intelligent format detection, automatic schema inference, and robust error
handling. Optimized for diverse data sources, cross-system integration, and large-scale
analytics workflows.

**Supported Data Formats:**
    - **CSV**: Comma-separated values with RFC 4180 compliance and flexible delimiter
      support
    - **JSON**: JavaScript Object Notation with automatic format detection
      (JSONL, arrays, pretty)
    - **Parquet**: Apache Parquet columnar format optimized for analytics and data lake
      processing
    - **Excel**: Microsoft Excel (.xlsx/.xls) for business data integration and
      reporting workflows
    - **Text**: Plain text files for log processing and unstructured data analysis
    - **Positional**: Fixed-width files for mainframe and legacy system integration

**Core Reader Capabilities:**
    **Performance Optimization:**
    - Distributed processing across Spark cluster for maximum throughput
    - Intelligent schema inference with configurable precision and performance
      trade-offs
    - Predicate pushdown optimization for selective data loading (Parquet, CSV)
    - Memory-efficient processing with streaming support for large datasets
    - Automatic partitioning and load balancing across cluster resources

    **Format Intelligence:**
    - Automatic format detection eliminating manual configuration requirements
    - Intelligent fallback strategies for robust data ingestion from diverse sources
    - Multi-strategy parsing with cascading error recovery for maximum compatibility
    - Schema evolution support for changing data structures in production environments

    **Production Safety:**
    - Comprehensive error handling with detailed diagnostic information
    - Cluster-wide validation for shared storage accessibility in distributed
      environments
    - Data quality validation and corruption detection with automated recovery
    - Resource management and cleanup for reliable production operation

**Enterprise Integration Features:**
    **Business System Compatibility:**
    - Excel integration for business reporting and departmental data processing
    - CSV support for ERP, CRM, and database system exports with flexible formatting
    - JSON processing for API integration, web services, and modern application data
    - Legacy system support through positional file processing for mainframe integration

    **Data Lake & Analytics:**
    - Parquet optimization for columnar analytics and data warehouse processing
    - Multi-format ingestion for heterogeneous data source consolidation
    - Schema consistency validation across different data sources and formats
    - Performance tuning for large-scale data lake ingestion and processing workflows

    **Cross-Platform Support:**
    - Windows, Linux, and macOS compatibility with platform-specific optimizations
    - Network storage support (NFS, SMB, cloud mounts) with cluster validation
    - International character encoding support for global data processing requirements
    - Timezone and locale handling for multinational data integration scenarios

**Advanced Processing Capabilities:**
    **Intelligent Data Handling:**
    - Automatic data type inference with business-friendly type selection
    - Null value standardization and missing data handling across formats
    - Character encoding detection and international text processing
    - Date/time format recognition and standardization for temporal data analysis

    **Error Recovery & Validation:**
    - Multi-level error recovery with graceful degradation for partial data corruption
    - Comprehensive data validation with quality assessment and reporting
    - Malformed record isolation and processing continuation for resilient workflows
    - Detailed error reporting with actionable troubleshooting information

    **Performance Optimization:**
    - Column selection optimization for reduced I/O and memory usage
    - Distributed file processing with optimal cluster resource utilization
    - Caching strategies for repeated access to same data sources
    - Resource monitoring and automatic scaling for varying workload demands

**Reader Selection Guide:**
    **CSV Reader** (``load_csv``):
    - **Best for**: Structured tabular data, database exports, ETL pipelines
    - **Performance**: Excellent with distributed processing and schema inference
    - **Use cases**: Data warehouse loading, cross-system integration, reporting data
    - **Formats**: Standard CSV, TSV, European CSV (semicolon), custom delimiters

    **JSON Reader** (``load_json``):
    - **Best for**: Semi-structured data, API responses, modern application integration
    - **Performance**: Good with automatic format detection and error recovery
    - **Use cases**: Web service integration, log analysis, configuration processing
    - **Formats**: JSONL, JSON arrays, Spark pretty format with auto-detection

    **Parquet Reader** (``load_parquet``):
    - **Best for**: Analytics workloads, data lake processing, columnar analysis
    - **Performance**: Optimal for analytical queries with predicate pushdown
    - **Use cases**: Business intelligence, data science, large-scale analytics
    - **Features**: Schema evolution, compression, efficient column access

    **Excel Reader** (``load_excel``):
    - **Best for**: Business data integration, financial reporting, departmental data
    - **Performance**: Good for moderate datasets, limited by Excel format constraints
    - **Use cases**: Financial analysis, business reporting, executive dashboards
    - **Features**: Multi-sheet processing, header intelligence, business formatting

    **Text Reader** (``load_text``):
    - **Best for**: Unstructured data, log files, plain text processing
    - **Performance**: Excellent with line-by-line processing optimization
    - **Use cases**: Log analysis, configuration files, document processing
    - **Features**: Encoding detection, cluster validation, streaming processing

    **Positional Reader** (``load_positional``):
    - **Best for**: Legacy system integration, mainframe data, fixed-width formats
    - **Performance**: Good with intelligent encoding fallback and data cleaning
    - **Use cases**: Mainframe integration, government data, financial systems
    - **Features**: Precise column positioning, encoding resilience, data cleaning

**Usage Patterns:**
    Standard data ingestion with automatic optimization:

     from spark_simplicity.io.readers import load_csv, load_json, load_parquet

     # High-performance CSV with intelligent defaults
     df = load_csv(spark, "data.csv")

     # JSON with automatic format detection
     json_df = load_json(spark, "api_data.json")

     # Optimized Parquet for analytics
     analytics_df = load_parquet(spark, "warehouse/table.parquet",
                                columns=["id", "value", "date"])

    Multi-format data integration workflow:

     # Process diverse data sources with consistent interface
     csv_data = load_csv(spark, "exports/sales.csv")
     json_logs = load_json(spark, "logs/events.json")
     excel_reports = load_excel(spark, "reports/monthly.xlsx")

     # Combine for comprehensive analysis
     combined = csv_data.union(json_logs).union(excel_reports)

    Enterprise data lake ingestion:

     from pathlib import Path

     # Process multiple data sources efficiently
     data_sources = [
    ...     ("customers.csv", load_csv),
    ...     ("transactions.parquet", load_parquet),
    ...     ("logs.json", load_json)
    ... ]

     datasets = {}
     for filename, reader_func in data_sources:
    ...     df = reader_func(spark, f"data_lake/{filename}")
    ...     datasets[filename] = df
    ...     print(f"Loaded {filename}: {df.count()} records")

**Performance Optimization Guidelines:**
    **Small Datasets (< 100MB)**:
    - All readers provide excellent performance with minimal configuration
    - Schema inference and validation have negligible overhead
    - Use default settings for optimal balance of features and performance

    **Medium Datasets (100MB - 10GB)**:
    - Consider column selection for Parquet and CSV readers to reduce I/O
    - Enable distributed processing strategies for improved throughput
    - Monitor memory usage for Excel and JSON readers with complex structures

    **Large Datasets (> 10GB)**:
    - Prioritize Parquet format for optimal analytics performance
    - Use distributed strategies and disable unnecessary schema inference
    - Implement partitioning strategies for improved query performance
    - Consider data preprocessing for very large Excel or complex JSON files

**Error Handling & Monitoring:**
    All readers provide comprehensive error handling with:
    - Detailed error messages with troubleshooting guidance
    - Structured logging for operational monitoring and debugging
    - Graceful degradation with partial data recovery where possible
    - Performance metrics and resource utilization reporting

**Integration Patterns:**
    **ETL Pipeline Integration**: Standardized readers for consistent data ingestion
    **Data Quality Workflows**: Built-in validation and quality assessment capabilities
    **Business Intelligence**: Optimized readers for BI tool integration and reporting
    **Real-time Processing**: Streaming-compatible readers for continuous data ingestion
    **Cross-System Integration**: Format-agnostic processing for diverse data sources

See Also:
    - Writers package: ``spark_simplicity.io.writers`` for complementary output
      capabilities
    - Validation package: ``spark_simplicity.io.validation`` for path and mount
      validation
    - Utilities package: ``spark_simplicity.io.utils`` for format conversion and
      processing
    - Session management: ``spark_simplicity.session`` for optimized Spark configuration

Note:
    This readers package provides the foundation for all data ingestion in Spark
    Simplicity, with each reader optimized for its specific format while maintaining
    consistent interfaces and enterprise-grade reliability. The intelligent defaults and
    comprehensive error handling make it suitable for both development and production
    environments.
"""

from .csv_reader import load_csv
from .excel_reader import load_excel
from .json_reader import load_json
from .parquet_reader import load_parquet
from .text_reader import load_positional, load_text

__all__ = [
    "load_csv",
    "load_json",
    "load_parquet",
    "load_excel",
    "load_text",
    "load_positional",
]
