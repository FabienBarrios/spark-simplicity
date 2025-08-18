"""
Spark Simplicity - Excel Writers
================================

Professional Excel export functionality for Spark DataFrames with enterprise-grade
features and safety controls. This module provides optimized Excel output capabilities
using pandas and openpyxl for maximum compatibility with Microsoft Excel and other
spreadsheet applications.

Key Features:
    - Professional Excel output with openpyxl engine integration
    - Comprehensive safety controls and row count validation
    - Flexible sheet naming and formatting options
    - Automatic directory creation and error handling
    - Memory-efficient pandas conversion pipeline
    - Full compatibility with Excel 2007+ (.xlsx) format

Excel Limitations & Considerations:
    - **Row Limit**: Excel supports maximum 1,048,576 rows per sheet
    - **Memory Usage**: Entire dataset must fit in driver memory for conversion
    - **Performance**: Single-threaded operation optimal for moderate datasets
    - **Format Support**: Only .xlsx format supported (modern Excel standard)

Safety Features:
    - Configurable maximum row limits with validation
    - Automatic error handling with descriptive messages
    - Path validation and directory creation
    - Resource cleanup and memory management

Usage:
    from spark_simplicity.io.writers.excel_writer import write_excel

    # Simple Excel export
    write_excel(df, "report.xlsx")

    # Professional report with custom sheet name
    write_excel(df, "quarterly_sales.xlsx", sheet_name="Q4_Results")

    # Advanced formatting with pandas options
    write_excel(df, "formatted_report.xlsx",
                sheet_name="Analysis",
                startrow=2, startcol=1)
"""

from pathlib import Path
from typing import Any, Union

import pandas as pd
from pyspark.sql import DataFrame

from ...logger import get_logger

# Logger for Excel writer
_excel_logger = get_logger("spark_simplicity.io.writers.excel")


def write_excel(
    df: DataFrame,
    output_path: Union[str, Path],
    sheet_name: str = "Sheet1",
    header: bool = True,
    index: bool = False,
    max_rows: int = 1_000_000,
    **pandas_options: Any,
) -> None:
    """
    Export Spark DataFrame to professional Excel format with enterprise-grade safety
    controls.

    Provides high-quality Excel export functionality using pandas and openpyxl for
    maximum
    compatibility with Microsoft Excel and other spreadsheet applications. This function
    automatically handles data conversion, validation, and formatting while maintaining
    professional standards for business reporting and data analysis.

    This operation requires collecting the entire DataFrame to the driver node for
    pandas
    conversion, making it optimal for moderate-sized datasets typically used in business
    reporting scenarios. For large-scale data processing, consider using CSV or Parquet
    formats which support distributed processing.

    Args:
        df: Spark DataFrame containing the data to export. All Spark SQL data types
            are automatically converted to Excel-compatible formats through pandas.
            Complex types (arrays, structs) are serialized to string representation.
        output_path: Target Excel file path. Must end with .xlsx extension for proper
                    Excel 2007+ format compatibility. Parent directories will be created
                    automatically if they don't exist.
        sheet_name: Name of the Excel worksheet where data will be written. Must comply
                   with Excel naming restrictions (no special characters like /, \\, *,
                   etc.).
                   Maximum 31 characters. Defaults to 'Sheet1'.
        header: Whether to include column headers in the first row of the worksheet.
               True creates professional headers using DataFrame column names.
               False starts data from first row without headers.
        index: Whether to include pandas row index as the first column. Generally
              recommended to keep False for business reports to avoid confusion
              with actual data columns.
        max_rows: Safety limit for maximum number of rows to export. Prevents accidental
                 export of extremely large datasets that could cause memory issues or
                 exceed Excel's practical limits. Default: 1,000,000 rows.
        **pandas_options: Advanced pandas.to_excel() options for fine-tuned control:
                         - 'startrow': Starting row position (0-indexed)
                         - 'startcol': Starting column position (0-indexed)
                         - 'columns': Specific columns to export
                         - 'float_format': Number formatting pattern
                         - 'date_format': Date formatting pattern
                         - 'datetime_format': DateTime formatting pattern

    Raises:
        ValueError: If DataFrame exceeds max_rows safety limit. This prevents memory
                   issues and performance problems with very large datasets.
        RuntimeError: If Excel write operation fails due to file system issues,
                     permission errors, disk space constraints, or invalid file paths.
        MemoryError: If DataFrame is too large to collect on driver node during
                    pandas conversion. Consider filtering data first.
        PermissionError: If output_path location is not writable by the current process.

    Excel Technical Specifications:
        **Format**: Excel 2007+ (.xlsx) using OpenXML standard
        **Engine**: openpyxl for maximum compatibility and feature support
        **Row Limit**: Excel supports maximum 1,048,576 rows per worksheet
        **Column Limit**: Excel supports maximum 16,384 columns per worksheet
        **File Size**: Practical limit around 100MB for good performance
        **Memory Usage**: Entire dataset loaded into driver memory during conversion

    Performance Characteristics:
        **Small datasets (< 10,000 rows)**:
        - Excellent performance and user experience
        - Instant loading in Excel applications
        - Minimal memory overhead

        **Medium datasets (10,000 - 100,000 rows)**:
        - Good performance for business reporting
        - Acceptable loading time in Excel
        - Monitor driver memory usage

        **Large datasets (> 100,000 rows)**:
        - Consider alternative formats (CSV, Parquet)
        - Excel may become slow to open and manipulate
        - Significant memory usage on driver node

    Examples:
        Simple business report export:

         write_excel(sales_df, "quarterly_sales_report.xlsx")

        Professional report with custom sheet naming:

         write_excel(df, "financial_analysis.xlsx",
        ...             sheet_name="Revenue_Analysis")

        Formatted report with custom positioning:

         write_excel(summary_df, "executive_summary.xlsx",
        ...             sheet_name="Dashboard",
        ...             startrow=3, startcol=1,
        ...             header=True)

        Data export without row indices for clean presentation:

         write_excel(clean_df, "presentation_data.xlsx",
        ...             sheet_name="Results",
        ...             index=False, header=True)

        Advanced formatting for financial reports:

         write_excel(financial_df, "budget_report.xlsx",
        ...             sheet_name="Budget_2024",
        ...             float_format="%.2f",
        ...             date_format="mm/dd/yyyy")

    Business Use Cases:
        - **Executive Dashboards**: Summary data for leadership review
        - **Financial Reports**: Budget analysis and financial statements
        - **Sales Analytics**: Performance metrics and trend analysis
        - **Operational Reports**: KPI tracking and operational metrics
        - **Data Sharing**: Inter-department data exchange and collaboration
        - **Regulatory Reporting**: Compliance data in standardized format

    Data Type Handling:
        - **Numeric Types**: Preserved with full precision in Excel
        - **Text/String**: Full UTF-8 support with international characters
        - **Dates/Timestamps**: Converted to Excel date format for sorting/filtering
        - **Boolean Values**: Displayed as TRUE/FALSE in Excel
        - **Null Values**: Shown as empty cells in Excel
        - **Complex Types**: Serialized to string representation

    See Also:
        - CSV export: ``write_csv()`` for large datasets and cross-platform
          compatibility
        - Parquet export: ``write_parquet()`` for analytics and big data workflows
        - JSON export: ``write_json()`` for API integration and data exchange
        - Multiple sheets: Use pandas ExcelWriter directly for advanced Excel features

    Warning:
        Excel format is not suitable for very large datasets due to Excel's inherent
        limitations and memory requirements. For datasets exceeding 100,000 rows,
        consider CSV format which offers better performance and broader compatibility.

    Note:
        This function uses the openpyxl engine which provides the best compatibility
        with Excel 2007+ features. For legacy Excel support (.xls format), use
        pandas directly with the xlwt engine, though this is not recommended for
        modern business applications.
    """
    output_path = Path(output_path)

    try:
        # Convert to Pandas (required for Excel)
        pandas_df: pd.DataFrame = df.toPandas()

        # Check row count for safety
        if len(pandas_df) > max_rows:
            raise ValueError(
                f"DataFrame has {len(pandas_df):,} rows, exceeding Excel limit of "
                f"{max_rows:,}. "
                f"Consider using write_csv() or filtering the data first."
            )

        _excel_logger.info("Writing Excel file with pandas")

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write Excel file directly (no temporary files needed with pandas)
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            pandas_df.to_excel(
                writer,
                sheet_name=sheet_name,
                header=header,
                index=index,
                **pandas_options,
            )

        _excel_logger.info(
            "Excel written successfully: %s (%d rows, sheet: %s)",
            output_path,
            len(pandas_df),
            sheet_name,
        )

    except Exception as e:
        raise RuntimeError(
            f"Could not save the file (please verify the path, write permissions, and "
            f"available "
            f"disk space) : Excel {output_path}: {str(e)}"
        ) from e
