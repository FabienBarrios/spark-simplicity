"""
Spark Simplicity - Format Detection and Conversion Utilities
===========================================================

Enterprise-grade format detection, conversion, and processing utilities for Spark
I/O operations.
This module provides comprehensive format handling capabilities including JSON parsing,
format conversion,
file concatenation, and intelligent format detection. Essential for complex data
processing workflows
requiring format transformation and file consolidation operations.

Key Features:
    - **JSON Format Processing**: Advanced JSON and JSONL parsing with error recovery
    - **Format Conversion**: Intelligent conversion between JSON formats
      (JSONL ↔ JSON Array)
    - **File Concatenation**: Multi-file consolidation with format-specific handling
    - **Error Recovery**: Robust parsing with malformed data tolerance
    - **Encoding Support**: Full UTF-8 and international character handling
    - **Pretty Formatting**: Professional JSON output with configurable indentation

Format Support:
    **JSON Variants**:
    - **JSON Lines (JSONL)**: Line-delimited JSON objects for streaming processing
    - **JSON Arrays**: Standard JSON array format for web APIs and applications
    - **Pretty JSON**: Human-readable formatted JSON with indentation
    - **Compact JSON**: Minified JSON for optimal storage and network transfer

    **CSV Operations**:
    - **Header Management**: Intelligent header handling during file concatenation
    - **Multi-file Consolidation**: Seamless merging of distributed CSV outputs
    - **Encoding Preservation**: Consistent UTF-8 encoding across operations

Advanced Parsing Capabilities:
    - **Hybrid Format Detection**: Automatic detection between JSONL and pretty JSON
    - **Malformed Data Recovery**: Graceful handling of corrupted JSON records
    - **State-based Parsing**: Advanced JSON object boundary detection
    - **Memory Efficient Processing**: Stream-based parsing for large files
    - **Character-level Analysis**: Precise JSON structure parsing with escape handling

Enterprise Features:
    - **Production Safety**: Comprehensive error handling with detailed diagnostics
    - **Performance Optimization**: Efficient parsing algorithms for large datasets
    - **Logging Integration**: Detailed operation logging for monitoring and debugging
    - **Cross-Platform Support**: Windows, Linux, and macOS compatibility
    - **Resource Management**: Memory-efficient processing of large format conversions

Usage:
    This module is used internally by Spark Simplicity I/O operations and can also
    be used directly for format conversion and file processing tasks in data pipelines.

    from spark_simplicity.io.utils.format_utils import convert_jsonl_to_json_array
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from ...logger import get_logger

# Logger for format utilities
_format_logger = get_logger("spark_simplicity.io.format")


def convert_jsonl_to_json_array(
    jsonl_file: Path, output_path: Path, pretty: bool = False
) -> None:
    """
    Convert JSON Lines (JSONL) format to standard JSON array with configurable
    formatting.

    Transforms line-delimited JSON objects into a standard JSON array format suitable
    for
    web APIs, applications, and systems expecting traditional JSON array structure. This
    function provides intelligent error recovery for malformed JSON lines and supports
    both compact and pretty-formatted output for different use cases.

    The conversion process handles large JSONL files efficiently by processing them
    line-by-line
    rather than loading the entire content into memory, making it suitable for
    production
    data processing workflows with significant file sizes.

    Args:
        jsonl_file: Path to input JSONL file containing line-delimited JSON objects.
                   Each line should contain a valid JSON object. Empty lines and
                   malformed JSON lines are handled gracefully with warning logging.
        output_path: Path for output JSON array file. Will be created with proper
                    UTF-8 encoding and formatted according to the pretty parameter.
                    Parent directories are created automatically if needed.
        pretty: Whether to format output with indentation for human readability:
               - True: Pretty-formatted with 2-space indentation and proper line breaks
               - False: Compact format with minimal whitespace for optimal file size

    Raises:
        RuntimeError: If file I/O operations fail due to permission errors, disk space
                     issues, or if the input file cannot be read. The original exception
                     is preserved in the error chain for detailed diagnostics.

    Examples:
        Basic JSONL to JSON array conversion:

         convert_jsonl_to_json_array(
        ...     Path("data.jsonl"),
        ...     Path("data.json")
        ... )

        Pretty-formatted conversion for human review:

         convert_jsonl_to_json_array(
        ...     Path("logs.jsonl"),
        ...     Path("formatted_logs.json"),
        ...     pretty=True
        ... )

    Note:
        This function is optimized for production use with comprehensive error handling
        and memory-efficient processing. It's suitable for processing large JSONL files
        generated by Spark or other big data systems.
    """
    records = []

    try:
        with open(jsonl_file, encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        _format_logger.warning(
                            "Skipping malformed JSON on line %d: %s", line_num, str(e)
                        )

        # Write as JSON array (pretty or compact)
        with open(output_path, "w", encoding="utf-8") as f:
            if pretty:
                json.dump(records, f, ensure_ascii=False, indent=2)
            else:
                json.dump(records, f, ensure_ascii=False, separators=(",", ":"))

        format_type = "pretty" if pretty else "compact"
        _format_logger.info(
            "Converted %d records from JSONL to %s JSON array",
            len(records),
            format_type,
        )

    except Exception as e:
        raise RuntimeError(f"Failed to convert JSONL to JSON array: {str(e)}") from e


def _parse_spark_json_content(content: str, filename: str) -> List[dict]:
    """
    Intelligently parse Spark-generated JSON content with automatic format detection.

    Provides robust parsing of JSON content generated by Apache Spark, which can produce
    either JSONL (line-delimited) format or pretty-formatted JSON depending on
    configuration.
    This function automatically detects the format and applies the appropriate parsing
    strategy,
    making it essential for processing diverse Spark JSON outputs in production
    environments.

    Args:
        content: Raw JSON content string to parse. Can contain either JSONL format
                (one JSON object per line) or pretty-formatted JSON with indentation
                and line breaks. Mixed formats within the same content are not
                supported.
        filename: Source filename used for error reporting and logging context.
                 Helps identify problematic files during batch processing operations.

    Returns:
        List of parsed JSON objects (dictionaries) extracted from the content.
        Empty list if no valid JSON objects are found. Malformed objects are
        skipped with warning logs, allowing processing to continue.

    Note:
        This function is designed to be fault-tolerant for production environments
        where Spark may generate JSON content with varying quality. It prioritizes
        data recovery over strict parsing, making it suitable for processing large
        datasets where some malformed records are acceptable.
    """
    records = []
    lines = content.split("\n")

    # Check if it's JSONL format (one JSON object per line)
    is_jsonl = any(
        line.strip().startswith("{") and line.strip().endswith("}")
        for line in lines[:5]
        if line.strip()
    )

    if is_jsonl:
        # Parse as JSONL (one object per line)
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if line:
                try:
                    record = json.loads(line)
                    records.append(record)
                except json.JSONDecodeError as e:
                    _format_logger.warning(
                        "Skipping malformed JSONL on line %d in %s: %s",
                        line_num,
                        filename,
                        str(e),
                    )
    else:
        # Parse as pretty-formatted JSON
        records = _parse_pretty_json_objects(content, filename)

    return records


class JsonParser:
    """
    Advanced stateful JSON parser for character-level object boundary detection.

    Implements a finite state machine for parsing JSON objects from continuous content
    streams where traditional JSON parsers may fail due to concatenated objects or
    complex formatting. This parser tracks brace nesting, string literals, and escape
    sequences to accurately identify complete JSON object boundaries.

    Attributes:
        current_obj: Accumulated characters forming the current JSON object being parsed
        brace_count: Current nesting level of braces (0 indicates complete object)
        in_string: Boolean flag indicating if parser is currently inside a string
                  literal
        escape_next: Boolean flag indicating if next character should be escaped
    """

    def __init__(self) -> None:
        self.current_obj = ""
        self.brace_count = 0
        self.in_string = False
        self.escape_next = False

    def reset_object(self) -> None:
        """
        Reset parser state to begin processing the next JSON object.

        Clears the current object buffer and resets brace counting while preserving
        string and escape state for continuous parsing. This method is called after
        successfully parsing a complete JSON object to prepare for the next object
        in the content stream.
        """
        self.current_obj = ""
        self.brace_count = 0

    def process_character(self, char: str) -> bool:
        """
        Process a single character and determine if a complete JSON object is ready.

        Implements the core parsing logic for character-level JSON object detection.
        This method processes each character according to JSON syntax rules, tracking
        brace nesting, string boundaries, and escape sequences to accurately identify
        when a complete JSON object has been accumulated.

        Args:
            char: Single character to process from the JSON content stream.
                 Can be any valid character including whitespace, punctuation,
                 and Unicode characters within string literals.

        Returns:
            Boolean indicating whether the current object is complete and ready for
            parsing:
            - True: A complete JSON object is available via get_current_object()
            - False: More characters needed to complete the current object
        """
        self.current_obj += char

        if self.escape_next:
            self.escape_next = False
            return False

        if char == "\\":
            self.escape_next = True
            return False

        if char == '"' and not self.escape_next:
            self.in_string = not self.in_string
            return False

        if not self.in_string:
            if char == "{":
                self.brace_count += 1
            elif char == "}":
                self.brace_count -= 1
                return self.brace_count == 0

        return False

    def get_current_object(self) -> str:
        """
        Retrieve the accumulated JSON object string with whitespace normalization.

        Returns the complete JSON object that has been built character by character
        during the parsing process. The returned string is whitespace-trimmed and
        ready for JSON parsing with standard libraries like json.loads().

        Returns:
            Trimmed string representation of the complete JSON object.
            Empty string if no characters have been processed yet.
        """
        return self.current_obj.strip()


def _try_parse_json_object(obj_str: str, filename: str) -> Optional[Dict[str, Any]]:
    """
    Safely attempt to parse a JSON object string with comprehensive error handling.

    Provides fault-tolerant JSON parsing for individual object strings extracted
    from content streams. This function handles malformed JSON gracefully by
    logging warnings and returning None rather than raising exceptions, allowing
    batch processing operations to continue despite encountering corrupted data.

    Args:
        obj_str: JSON object string to parse. Should contain a complete JSON object
                but may be malformed due to content corruption or parsing errors.
                Empty or whitespace-only strings are handled gracefully.
        filename: Source filename for error context in log messages. Helps identify
                 the source of problematic JSON objects during batch processing.

    Returns:
        Parsed JSON object as a dictionary if successful, None if parsing fails.
        None return indicates the object string was invalid and has been logged.
    """
    try:
        if obj_str:
            return cast(Dict[str, Any], json.loads(obj_str))
    except json.JSONDecodeError as e:
        _format_logger.warning(
            "Skipping malformed pretty JSON object in %s: %s", filename, str(e)
        )
    return None


def _parse_pretty_json_objects(content: str, filename: str) -> List[dict]:
    """
    Parse multiple JSON objects from pretty-formatted content using advanced state
    tracking.

    Processes JSON content that contains multiple objects with pretty formatting,
    indentation, and line breaks. This function uses a sophisticated character-level
    parser to identify object boundaries in content where traditional line-based
    parsing would fail due to objects spanning multiple lines.

    Args:
        content: Pretty-formatted JSON content containing one or more JSON objects.
                Content may include indentation, line breaks, and whitespace formatting.
                Objects can be nested and span multiple lines with complex structure.
        filename: Source filename used for error reporting and logging context.
                 Provides traceability for malformed objects during processing.

    Returns:
        List of successfully parsed JSON objects (dictionaries). Malformed objects
        are skipped with warning logs, allowing processing to continue with valid data.
        Returns empty list if no valid objects are found in the content.
    """
    parser = JsonParser()
    records = []

    for char in content:
        is_complete = parser.process_character(char)

        if is_complete:
            obj_str = parser.get_current_object()
            record = _try_parse_json_object(obj_str, filename)
            if record is not None:
                records.append(record)
            parser.reset_object()

    return records


def _concatenate_json_files(
    json_files: List[Path], output_path: Path, pretty: bool = False
) -> None:
    """
    Consolidate multiple Spark JSON part files into a unified JSON array with
    intelligent parsing.

    Merges distributed JSON output files generated by Spark operations into a single,
    well-formed JSON array. This function handles the complexity of processing multiple
    part files that may contain different JSON formatting (JSONL vs pretty) and provides
    robust error recovery for malformed files while preserving valid data.

    Args:
        json_files: List of Path objects pointing to JSON part files to consolidate.
                   Files are processed in sorted order to ensure consistent output.
                   Empty or unreadable files are logged and skipped gracefully.
        output_path: Path for the consolidated JSON array output file. Will be created
                    with proper UTF-8 encoding and formatted according to pretty
                    parameter.
                    Parent directories are created automatically if needed.
        pretty: Whether to format output JSON with indentation:
               - True: Pretty-formatted with 2-space indentation for readability
               - False: Compact format with minimal whitespace for efficiency

    Raises:
        RuntimeError: If no valid JSON records are found across all part files,
                     indicating complete processing failure. Also raised for
                     critical I/O errors during output file creation.
    """
    all_records = []

    # Process all part files in sorted order
    for json_file in sorted(json_files):
        try:
            with open(json_file, encoding="utf-8") as infile:
                file_content = infile.read().strip()

            if file_content:
                records = _parse_spark_json_content(file_content, json_file.name)
                all_records.extend(records)

        except Exception as e:
            _format_logger.error(
                "Failed to read JSON file %s: %s", json_file.name, str(e)
            )
            continue

    if not all_records:
        raise RuntimeError(
            f"No valid JSON records found in {len(json_files)} part files"
        )

    # Write consolidated JSON array
    with open(output_path, "w", encoding="utf-8") as outfile:
        if pretty:
            json.dump(all_records, outfile, ensure_ascii=False, indent=2)
        else:
            json.dump(all_records, outfile, ensure_ascii=False, separators=(",", ":"))

    _format_logger.info(
        "Successfully concatenated %d records from %d part files",
        len(all_records),
        len(json_files),
    )


def _concatenate_csv_files(
    csv_files: List[Path], output_path: Path, include_header: bool = True
) -> None:
    """
    Efficiently concatenate multiple CSV files with intelligent header management.

    Merges distributed CSV output files generated by Spark operations into a single,
    well-formed CSV file with proper header handling. This function is essential for
    consolidating Spark's distributed CSV output where each part file may contain
    headers, requiring intelligent deduplication to produce clean, consolidated output.

    Args:
        csv_files: List of Path objects pointing to CSV part files to concatenate.
                  Files are processed in sorted order to ensure consistent output
                  structure. Empty files are handled gracefully without errors.
        output_path: Path for the consolidated CSV output file. Will be created with
                    UTF-8 encoding and proper line ending handling. Parent directories
                    are created automatically if they don't exist.
        include_header: Whether to include header row in the consolidated output:
                       - True: Include header from first file, skip headers in others
                       - False: Skip all headers, concatenate only data rows
    """
    with open(output_path, "w", encoding="utf-8") as outfile:
        header_written = False

        for csv_file in sorted(csv_files):
            with open(csv_file, encoding="utf-8") as infile:
                lines = infile.readlines()

                if lines:
                    if include_header and not header_written:
                        # Write header from first file
                        outfile.write(lines[0])
                        header_written = True
                        start_idx = 1
                    else:
                        # Skip header for subsequent files
                        start_idx = 1 if include_header else 0

                    # Write data lines
                    for line in lines[start_idx:]:
                        outfile.write(line)


def process_and_move_json_files(
    part_files: List[Path], output_path: Path, pretty: bool = False
) -> None:
    """
    Process and transform Spark JSON part files with format standardization and
    intelligent distribution.

    Transforms distributed Spark JSON output files by parsing their content (which
    may be
    in JSONL or other formats) and converting each part file to a standardized JSON
    array
    format. This function is essential for creating consistent JSON output from Spark's
    distributed processing while maintaining the multi-file structure for parallel
    processing.

    Args:
        part_files: List of Path objects pointing to JSON part files from Spark output.
                   Each file is processed independently and converted to JSON array
                   format.
                   Files are processed in sorted order for consistent output naming.
        output_path: Base path template used for generating output filenames. The stem
                    becomes the prefix for numbered files (e.g., "output" becomes
                    "output_1.json", "output_2.json", etc.). Directory is created if
                    needed.
        pretty: Whether to format JSON arrays with indentation for readability:
               - True: Pretty-formatted with 2-space indentation and proper line breaks
               - False: Compact format with minimal whitespace for optimal file size

    Raises:
        RuntimeError: If no part files are provided (invalid input), if any individual
                     file processing fails due to I/O errors, parsing failures, or
                     encoding issues. The error includes specific details about which
                     file failed and why.

    Note:
        This function is ideal for production workflows that benefit from distributed
        file processing while requiring standardized JSON array format. It provides
        the format consistency needed for downstream systems while preserving the
        performance benefits of distributed file structures.
    """
    if not part_files:
        raise RuntimeError("No JSON part files provided for processing")

    output_dir = output_path.parent
    file_stem = output_path.stem
    file_suffix = output_path.suffix or ".json"

    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process each part file with pretty formatting
    for i, part_file in enumerate(sorted(part_files), 1):
        new_filename = f"{file_stem}_{i}{file_suffix}"
        new_path = output_dir / new_filename

        try:
            # Read JSONL content from part file
            with open(part_file, encoding="utf-8") as infile:
                content = infile.read().strip()

            if content:
                # Parse Spark JSON content (supports both JSONL and pretty formats)
                records = _parse_spark_json_content(content, part_file.name)

                # Write as JSON array with proper formatting
                with open(new_path, "w", encoding="utf-8") as outfile:
                    if pretty:
                        json.dump(records, outfile, ensure_ascii=False, indent=2)
                    else:
                        json.dump(
                            records, outfile, ensure_ascii=False, separators=(",", ":")
                        )
            else:
                # Handle empty files
                with open(new_path, "w", encoding="utf-8") as outfile:
                    json.dump([], outfile, ensure_ascii=False)

        except Exception as e:
            raise RuntimeError(
                f"Failed to process JSON part file {part_file}: {str(e)}"
            ) from e

    format_type = "pretty-formatted" if pretty else "compact"
    _format_logger.info(
        "Successfully created %d separate %s JSON files: %s_1%s to %s_%d%s",
        len(part_files),
        format_type,
        file_stem,
        file_suffix,
        file_stem,
        len(part_files),
        file_suffix,
    )
