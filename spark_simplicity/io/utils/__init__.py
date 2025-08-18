"""
Spark Simplicity - I/O Utilities Package
========================================

Comprehensive utility library for advanced I/O operations, file system management,
and format
processing in enterprise Spark environments. This package provides essential tools
for file
analysis, format conversion, data transformation, and file system operations
optimized for
production data processing workflows.

**Core Utility Categories:**
    - **File System Utilities**: Advanced file metadata analysis and path operations
    - **Format Processing**: Intelligent format detection, conversion, and parsing
      utilities
    - **Data Transformation**: Format-specific data processing and conversion tools
    - **Error Recovery**: Robust error handling and data recovery mechanisms
    - **Performance Optimization**: Efficient algorithms for large-scale file operations

**File System Operations:**
    **File Analysis & Metadata:**
    - Comprehensive file information extraction and analysis
    - Format detection based on extensions and content analysis
    - File size metrics and storage utilization reporting
    - Timestamp tracking for modification and access patterns
    - Cross-platform path resolution and normalization

    **Storage System Integration:**
    - Local filesystem operations with high performance
    - Network attached storage (NFS, SMB/CIFS) compatibility
    - Cloud storage mount support (S3, Azure, GCS)
    - Distributed filesystem integration (HDFS, GlusterFS)

**Format Processing Capabilities:**
    **JSON Processing:**
    - Advanced JSON and JSONL parsing with error recovery
    - Format conversion between JSON variants (JSONL ↔ JSON Array)
    - Pretty formatting and compact output options
    - Multi-file JSON consolidation and processing
    - Character-level parsing for complex JSON structures

    **CSV Operations:**
    - Multi-file CSV concatenation with header management
    - Intelligent header deduplication across distributed files
    - Encoding preservation and character set handling
    - Large file processing with memory efficiency

    **Universal Format Support:**
    - Automatic format detection and processing routing
    - Extensible format mapping for custom file types
    - Error tolerance for malformed or corrupted data
    - Batch processing capabilities for large datasets

**Enterprise Features:**
    **Production Safety:**
    - Comprehensive error handling with detailed diagnostics
    - Graceful degradation for partial data corruption
    - Atomic operations with rollback capabilities
    - Resource cleanup and memory management

    **Performance Optimization:**
    - Memory-efficient streaming operations for large files
    - Parallel processing support for multi-file operations
    - Optimized algorithms for character-level parsing
    - Caching mechanisms for repeated operations

    **Monitoring & Observability:**
    - Detailed operation logging for audit trails
    - Performance metrics and operation timing
    - Error categorization for systematic troubleshooting
    - Integration with enterprise monitoring systems

**Data Processing Workflows:**
    **ETL Pipeline Integration:**
    - Pre-processing file analysis for strategy selection
    - Format standardization for downstream processing
    - Data quality validation and error reporting
    - Incremental processing support with change detection

    **Batch Processing:**
    - Multi-file consolidation for distributed outputs
    - Format transformation for system integration
    - Large-scale data conversion with progress tracking
    - Parallel processing coordination

**Advanced Parsing Technologies:**
    **State-Based JSON Parser:**
    - Character-level JSON object boundary detection
    - Escape sequence handling and string literal processing
    - Nested structure parsing with brace counting
    - Recovery from malformed JSON content

    **Intelligent Format Detection:**
    - Heuristic analysis for format identification
    - Content-based detection beyond file extensions
    - Hybrid format support (JSONL vs Pretty JSON)
    - Extensible detection algorithms

**Storage & Platform Compatibility:**
    **Cross-Platform Support:**
    - Windows, Linux, and macOS filesystem operations
    - Unicode and international character handling
    - Platform-specific optimizations and workarounds
    - Consistent behavior across different environments

    **Enterprise Storage:**
    - Network filesystem compatibility and optimization
    - Cloud storage integration with mount points
    - Distributed storage system support
    - High-availability storage configurations

**Usage Examples:**
    File system analysis and metadata extraction:

     from spark_simplicity.io.utils import get_file_info

     info = get_file_info("large_dataset.parquet")
     if info['size_mb'] > 1000:
    ...     print(f"Large file: {info['size_mb']} MB - use distributed processing")

    JSON format conversion and processing:

     from spark_simplicity.io.utils.format_utils import convert_jsonl_to_json_array

     convert_jsonl_to_json_array(
    ...     Path("spark_output.jsonl"),
    ...     Path("api_ready.json"),
    ...     pretty=True
    ... )

    Multi-file consolidation for distributed outputs:

     from spark_simplicity.io.utils.format_utils import _concatenate_json_files

     part_files = list(Path("output").glob("part-*.json"))
     _concatenate_json_files(part_files, Path("consolidated.json"))

**Integration Patterns:**
    **Data Pipeline Integration:**
    - File preprocessing and analysis in ETL workflows
    - Format standardization for downstream systems
    - Data quality validation and error handling
    - Capacity planning and resource optimization

    **Monitoring Integration:**
    - File system monitoring for operational dashboards
    - Data processing metrics and performance tracking
    - Error analysis and troubleshooting support
    - Integration with enterprise monitoring platforms

    **Automation Support:**
    - Automated file processing and conversion workflows
    - Event-driven processing based on file characteristics
    - Integration with workflow orchestration systems
    - Scheduled processing and maintenance operations

**Performance Characteristics:**
    **Scalability Features:**
    - Linear scaling with file count for batch operations
    - Memory-efficient processing of large individual files
    - Parallel processing support for multi-file workflows
    - Optimized algorithms for character-level operations

    **Resource Efficiency:**
    - Minimal memory footprint for file system operations
    - Streaming processing to avoid memory limitations
    - Efficient I/O patterns for network storage
    - Automatic resource cleanup and management

**Quality Assurance:**
    **Error Handling Strategy:**
    - Comprehensive error detection and reporting
    - Graceful handling of malformed or corrupted data
    - Detailed diagnostic information for troubleshooting
    - Recovery mechanisms for partial processing failures

    **Data Integrity:**
    - Validation of processing results and outputs
    - Checksums and integrity verification where applicable
    - Atomic operations to prevent partial corruption
    - Rollback capabilities for failed operations

See Also:
    - Main I/O package: ``spark_simplicity.io`` for core reading/writing operations
    - Writers package: ``spark_simplicity.io.writers`` for format-specific output
    - Validation package: ``spark_simplicity.io.validation`` for path and mount
      validation
    - Session management: ``spark_simplicity.session`` for Spark cluster configuration

Note:
    This utilities package provides the foundational tools for robust file system
    operations and format processing in production Spark environments. It emphasizes
    reliability, performance, and comprehensive error handling for enterprise-grade
    data processing workflows.
"""

from .file_utils import get_file_info
from .format_utils import (
    JsonParser,
    convert_jsonl_to_json_array,
    process_and_move_json_files,
)

__all__ = [
    "get_file_info",
    "convert_jsonl_to_json_array",
    "process_and_move_json_files",
    "JsonParser",
]
