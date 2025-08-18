"""
Spark Simplicity - Text Writers
===============================

Advanced text and positional file writers for Apache Spark DataFrames.
This module provides high-performance, production-ready text output capabilities
with precise formatting control for fixed-width files and structured text exports.

Key Features:
    - Fixed-width positional file generation
    - Flexible alignment options (left, right, center)
    - Customizable padding characters and line endings
    - Automatic column width validation and formatting
    - Memory-efficient pandas integration for text processing
    - Comprehensive error handling and logging

Supported Formats:
    - Fixed-width positional files (.dat, .txt)
    - Custom delimited text formats
    - Legacy mainframe-compatible outputs

Usage:
    from spark_simplicity.io.writers.text_writer import write_positional

    column_specs = [('id', 10), ('name', 25), ('amount', 15)]
    write_positional(df, 'output.dat', column_specs, alignment='right')
"""

from pathlib import Path
from typing import List, Tuple, Union

import pandas as pd
from pyspark.sql import DataFrame

from ...logger import get_logger

# Logger for text writers
_text_logger = get_logger("spark_simplicity.io.writers.text")


def _validate_alignment(alignment: str) -> None:
    """
    Validate text alignment parameter against supported options.

    Args:
        alignment: Text alignment option to validate

    Raises:
        ValueError: If alignment is not in supported options (left, right, center)
    """
    valid_alignments = {"left", "right", "center"}
    if alignment not in valid_alignments:
        raise ValueError(
            f"Invalid alignment '{alignment}'. Valid alignments: {valid_alignments}"
        )


def _validate_column_specs(df: DataFrame, column_specs: List[Tuple[str, int]]) -> None:
    """
    Validate column specifications against DataFrame schema.

    Ensures all specified columns exist in the DataFrame and that
    the column specifications list is not empty.

    Args:
        df: Spark DataFrame to validate against
        column_specs: List of (column_name, width) tuples to validate

    Raises:
        ValueError: If column_specs is empty or contains non-existent columns
    """
    if not column_specs:
        raise ValueError("column_specs cannot be empty")

    column_names = [spec[0] for spec in column_specs]
    missing_cols = set(column_names) - set(df.columns)
    if missing_cols:
        raise ValueError(f"Columns not found in DataFrame: {missing_cols}")


def _format_field_value(
    value: str, width: int, alignment: str, padding_char: str
) -> str:
    """
    Format a single field value with specified width, alignment, and padding.

    Applies the specified alignment and padding to ensure the field matches
    the exact width requirement. Values exceeding the width are truncated.

    Args:
        value: String value to format
        width: Target field width in characters
        alignment: Text alignment ('left', 'right', 'center')
        padding_char: Character used for padding

    Returns:
        Formatted string with exact specified width
    """
    if alignment == "left":
        formatted_value = value.ljust(width, padding_char)
    elif alignment == "right":
        formatted_value = value.rjust(width, padding_char)
    else:  # center
        formatted_value = value.center(width, padding_char)

    # Truncate if too long
    if len(formatted_value) > width:
        formatted_value = formatted_value[:width]

    return formatted_value


def _format_row_as_positional(
    row: pd.Series,
    column_specs: List[Tuple[str, int]],
    alignment: str,
    padding_char: str,
) -> str:
    """
    Format a pandas Series row into a fixed-width positional text line.

    Transforms each field in the row according to the column specifications,
    applying consistent formatting rules to create a fixed-width output line.

    Args:
        row: Pandas Series containing the row data
        column_specs: List of (column_name, width) specifications
        alignment: Text alignment to apply to all fields
        padding_char: Character used for field padding

    Returns:
        Formatted fixed-width text line as string
    """
    line_parts = []

    for col_name, width in column_specs:
        value = str(row[col_name]) if pd.notna(row[col_name]) else ""
        formatted_value = _format_field_value(value, width, alignment, padding_char)
        line_parts.append(formatted_value)

    return "".join(line_parts)


def write_positional(
    df: DataFrame,
    output_path: Union[str, Path],
    column_specs: List[Tuple[str, int]],
    padding_char: str = " ",
    alignment: str = "left",
    line_ending: str = "\n",
    encoding: str = "utf-8",
) -> None:
    """
    Export Spark DataFrame to fixed-width positional text format.

    Generates fixed-width positional files commonly used in mainframe systems,
    legacy applications, and data interchange scenarios. Each column is allocated
    a specific character width with consistent alignment and padding throughout
    the entire file.

    This function leverages pandas for efficient text processing while maintaining
    Spark's distributed computing benefits for data preparation and transformation.
    The output format ensures consistent field positioning, making it ideal for
    systems that require precise column alignment.

    Args:
        df: Spark DataFrame containing the data to export. All selected columns
            will be converted to string representation for positional formatting.
        output_path: Target file path for the positional output. Parent directories
                    will be created automatically if they don't exist.
        column_specs: List of (column_name, width) tuples defining the field layout.
                     Each tuple specifies a column name (must exist in DataFrame)
                     and its allocated character width in the output file.
        padding_char: Character used for padding fields to their specified width.
                     Defaults to space (' '). Common alternatives include '0' for
                     zero-padding numeric fields or '_' for visual separation.
        alignment: Text alignment strategy applied to all fields:
                  - 'left': Left-align text with right padding (default)
                  - 'right': Right-align text with left padding (ideal for numbers)
                  - 'center': Center text with balanced left/right padding
        line_ending: Line terminator character sequence. Defaults to Unix-style '\\n'.
                    Use '\\r\\n' for Windows compatibility or '\\r' for legacy Mac
                    systems.
        encoding: Character encoding for the output file. Defaults to 'utf-8' for
                 Unicode support. Use 'ascii', 'latin-1', or 'cp1252' for legacy
                 system compatibility.

    Raises:
        ValueError: If column_specs is empty, contains non-existent column names,
                   or if alignment parameter is not in ['left', 'right', 'center'].
        RuntimeError: If file write operation fails due to insufficient permissions,
                     disk space constraints, file system errors, or if the target
                     file is locked by another process.
        MemoryError: If the DataFrame is too large for pandas conversion. Consider
                    filtering or sampling large datasets before export.
        UnicodeEncodeError: If data contains characters incompatible with the
                           specified encoding.

    Performance Considerations:
        - Converts entire Spark DataFrame to pandas for text processing
        - Memory usage scales linearly with DataFrame size
        - Processing time increases with number of columns and total width
        - Consider using DataFrame.limit() for large datasets
        - Parent directory creation may add I/O overhead on network filesystems

    Examples:
        Basic positional file export with default settings:

         column_specs = [('customer_id', 10), ('name', 25), ('balance', 15)]
         write_positional(df, 'customers.dat', column_specs)

        Right-aligned numeric data with zero padding:

         financial_specs = [('account', 8), ('amount', 12), ('currency', 3)]
         write_positional(transactions_df, 'accounts.txt', financial_specs,
        ...                  padding_char='0', alignment='right')

        Legacy mainframe format with specific encoding and line endings:

         mainframe_specs = [('record_type', 2), ('data', 78)]
         write_positional(legacy_df, 'mainframe.dat', mainframe_specs,
        ...                  line_ending='\\r\\n', encoding='cp1252')

        Mixed alignment with custom padding for visual clarity:

         report_specs = [('code', 6), ('description', 40), ('status', 1)]
         write_positional(status_df, 'report.txt', report_specs,
        ...                  padding_char='_', alignment='center')

    Output Format:
        The generated file contains one line per DataFrame row, with each field
        positioned at fixed character locations. Fields are formatted according
        to their specifications and concatenated without delimiters.

        Example output with specs [('id', 5), ('name', 10), ('amount', 8)]:
        ```
        00001Alice     $1234.56
        00002Bob       $987.65
        00003Charlie   $5432.10
        ```

    See Also:
        - Standard Spark text writers: ``DataFrame.write.text()``
        - CSV export with delimiters: ``DataFrame.write.csv()``
        - Custom format writers in ``spark_simplicity.io.writers``
        - Data validation utilities in ``spark_simplicity.utils``

    Note:
        This function is optimized for moderate-sized datasets that fit comfortably
        in memory after pandas conversion. For very large datasets, consider using
        Spark's native text output capabilities with post-processing formatting.
    """
    output_path = Path(output_path)

    # Validate inputs
    _validate_alignment(alignment)
    _validate_column_specs(df, column_specs)

    try:
        _text_logger.info("Writing positional file with pandas")

        # Convert to pandas for positional formatting
        column_names = [spec[0] for spec in column_specs]
        pandas_df: pd.DataFrame = df.select(*column_names).toPandas()

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write positional file
        with open(output_path, "w", encoding=encoding) as f:
            for _, row in pandas_df.iterrows():
                formatted_line = _format_row_as_positional(
                    row, column_specs, alignment, padding_char
                )
                f.write(formatted_line + line_ending)

        # Log success information
        total_width = sum(spec[1] for spec in column_specs)
        _text_logger.info(
            "Positional file written successfully: %s (%d rows, %d chars width)",
            output_path,
            len(pandas_df),
            total_width,
        )

    except Exception as e:
        _text_logger.error(
            "Failed to write positional file %s: %s", output_path, str(e)
        )
        raise RuntimeError(
            f"Failed to write positional file '{output_path}'. "
            f"Please verify: (1) Path exists and is writable, "
            f"(2) Sufficient disk space available, "
            f"(3) File is not locked by another process. "
            f"Original error: {str(e)}"
        ) from e
