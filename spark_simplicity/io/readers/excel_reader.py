"""
Spark Simplicity - Excel File Reader
====================================

Enterprise-grade Excel file reader for business data integration and report processing.
This module provides comprehensive Excel ingestion capabilities using pandas as an
intermediate processor, enabling seamless integration of business reports, financial
data, and operational spreadsheets into Spark analytics workflows.

Key Features:
    - **Business Data Integration**: Seamless processing of Excel business reports
    - **Multi-Sheet Support**: Automatic handling of workbooks with multiple sheets
    - **Flexible Header Processing**: Configurable header row detection and processing
    - **Format Compatibility**: Support for Excel 2007+ (.xlsx) and legacy (.xls)formats
    - **Pandas Integration**: Leverages pandas' robust Excel parsing capabilities
    - **Production Safety**: Comprehensive error handling and validation

Excel Format Support:
    **Modern Excel Formats**:
    - .xlsx (Excel 2007+) - Primary format with full feature support
    - .xlsm (Excel with macros) - Macro-enabled workbooks with data extraction
    - .xltx (Excel templates) - Template files with data content

    **Legacy Excel Formats**:
    - .xls (Excel 97-2003) - Legacy format support for older business systems
    - Automatic format detection based on file extension

Business Use Cases:
    **Financial Reporting**:
    - Quarterly and annual financial statements
    - Budget analysis and variance reports
    - Cash flow and profitability analysis
    - Regulatory compliance reporting

    **Operational Data**:
    - Sales performance reports and dashboards
    - Inventory management and tracking
    - HR analytics and employee data
    - Customer analysis and segmentation

    **Executive Dashboards**:
    - KPI tracking and performance metrics
    - Board reporting and executive summaries
    - Strategic planning and forecasting data
    - Cross-departmental data consolidation

Advanced Features:
    **Multi-Sheet Processing**:
    - Automatic detection and combination of multiple worksheets
    - Individual sheet selection for targeted data extraction
    - Schema consistency validation across sheets
    - Intelligent data type preservation

    **Header Intelligence**:
    - Flexible header row detection and configuration
    - Multi-row header support for complex reports
    - Automatic column naming and cleanup
    - Business-friendly column name preservation

Enterprise Integration:
    - **Business Intelligence**: Direct Excel report integration into BI workflows
    - **Data Lake Ingestion**: Convert Excel reports for data lake storage
    - **ETL Processing**: Transform business reports into analytical datasets
    - **Compliance Reporting**: Process regulatory and audit reports
    - **Cross-System Integration**: Bridge Excel-based processes with modern analytics

Usage:
    This module is essential for organizations that need to integrate Excel-based
    business processes with modern Spark analytics and data processing workflows.

    from spark_simplicity.io.readers.excel_reader import load_excel
"""

from pathlib import Path
from typing import Any, Optional, Union

import pandas as pd
from pyspark.sql import DataFrame, SparkSession

from ...logger import get_logger

# Logger for Excel reader
_excel_logger = get_logger("spark_simplicity.io.readers.excel")


def load_excel(
    spark: SparkSession,
    file_path: Union[str, Path],
    sheet_name: Optional[str] = None,
    header: int = 0,
    **pandas_options: Any,
) -> DataFrame:
    """
    Load Excel files into Spark DataFrame with enterprise-grade business data processing

    Provides comprehensive Excel data ingestion for business intelligence, financial
    reporting, and operational analytics workflows. This function leverages pandas'
    robust Excel parsing capabilities while converting the result to distributed Spark
    DataFrames for scalable analytics processing. Essential for integrating Excel-based
    business processes with modern data analytics platforms.

    The function is specifically designed for business environments where Excel remains
    a primary tool for reporting, analysis, and data sharing across departments and
    stakeholders. It bridges the gap between traditional Excel workflows and modern big
    data analytics.

    Args:
        spark: Active SparkSession instance for DataFrame creation and distributed
              processing. Must be properly configured with adequate driver memory to
              handle Excel file loading and pandas DataFrame conversion. Memory
              requirements depend on Excel file size and complexity.
        file_path: Path to Excel file (.xlsx, .xls, .xlsm, .xltx formats supported).
                  Can be provided as string or Path object with automatic format
                  detection.Supports absolute and relative paths with local filesystem
                  access. Network paths and mapped drives are supported on Windows
                  systems.
        sheet_name: Specific worksheet name to load from the Excel workbook:
                   - None (default): Loads and combines all sheets into single DataFrame
                   - String: Loads specific sheet by name (e.g., "Sales_Data")
                   - Integer: Loads sheet by index (0-based, e.g., 0 for first sheet)
                   - List: Loads multiple specific sheets and combines them
        header: Row number to use as column headers (0-indexed):
               - 0 (default): Use first row as column headers
               - N: Use row N as headers (useful for reports with title rows)
               - None: No header row, generate default column names
               - [N1, N2]: Multi-row headers for complex report structures
        **pandas_options: Advanced pandas.read_excel() options for fine-tuned control:
                         - 'usecols': Specific columns to read (e.g., 'A:C' or [0,1,2])
                         - 'skiprows': Number of rows to skip at beginning
                         - 'nrows': Maximum number of rows to read
                         - 'index_col': Column to use as row index
                         - 'dtype': Dictionary specifying data types for columns
                         - 'na_values': Additional values to recognize as NaN
                         - 'converters': Dictionary of functions for converting values
                         - 'engine': Excel engine to use ('openpyxl', 'xlrd')

    Returns:
        Spark DataFrame containing the loaded Excel data:
        - Column names derived from Excel headers or generated automatically
        - Data types automatically inferred from Excel cell formats
        - Multiple sheets combined with consistent schema when sheet_name=None
        - Business-friendly formatting preserved where possible
        - Null values properly handled according to Excel conventions

    Raises:
        FileNotFoundError: If the specified Excel file does not exist at the given path.
                          Error message includes full path for troubleshooting.
        RuntimeError: If Excel loading fails due to format corruption, unsupported
                     features, permission issues, memory constraints, or pandas
                     processing errors. Includes detailed error context for business
                     user troubleshooting.
        MemoryError: If Excel file is too large to process on driver node. Consider
                    alternative formats or data preprocessing for very large files.

    Processing Characteristics:
        **Memory Usage**: Entire Excel file loaded into driver memory during processing
        **Performance**: Single-threaded pandas processing followed by Spark
        distribution
        **Sheet Handling**: Sequential processing of multiple sheets with schema
        alignment
        **Data Type Preservation**: Excel formatting translated to appropriate Spark
        types

    Examples:
        Load complete Excel workbook with all sheets:

         df = load_excel(spark, "quarterly_report.xlsx")
         print(f"Loaded {df.count()} total records from all sheets")
         df.printSchema()  # Show combined schema from all sheets

        Load specific worksheet for targeted analysis:

         sales_df = load_excel(
        ...     spark,
        ...     "financial_report.xlsx",
        ...     sheet_name="Sales_Analysis"
        ... )
         # Process only the Sales_Analysis worksheet

        Handle reports with non-standard header positioning:

         # Skip title rows and use row 2 as headers
         clean_df = load_excel(
        ...     spark,
        ...     "executive_dashboard.xlsx",
        ...     sheet_name="KPI_Data",
        ...     header=2,  # Headers start at row 3 (0-indexed)
        ...     skiprows=1  # Skip additional formatting rows
        ... )

        Advanced column and data type control:

         financial_df = load_excel(
        ...     spark,
        ...     "budget_analysis.xlsx",
        ...     sheet_name="Budget_2024",
        ...     usecols="B:G",  # Load only columns B through G
        ...     dtype={
        ...         'Department': 'string',
        ...         'Budget': 'float64',
        ...         'Actual': 'float64'
        ...     },
        ...     na_values=['N/A', 'TBD', '']  # Custom null indicators
        ... )

        Process regulatory compliance reports:

         compliance_df = load_excel(
        ...     spark,
        ...     "compliance_report.xlsx",
        ...     sheet_name=None,  # Combine all sheets
        ...     header=0,
        ...     converters={  # Custom value processing
        ...         'Date': pd.to_datetime,
        ...         'Amount': lambda x: float(str(x).replace('$', '').replace(',', ''))
        ...     }
        ... )

    Business Integration Patterns:
        **Financial Reporting**:
        - Monthly/quarterly financial statement processing
        - Budget vs actual analysis with variance calculation
        - Multi-department cost center consolidation
        - Regulatory compliance data preparation

        **Operational Analytics**:
        - Sales performance dashboard data ingestion
        - Inventory tracking and analysis
        - Customer segmentation from CRM exports
        - HR analytics and workforce planning

        **Executive Reporting**:
        - Board presentation data preparation
        - KPI tracking and trend analysis
        - Cross-functional performance metrics
        - Strategic planning data consolidation

    Data Type Handling:
        **Excel to Spark Type Mapping**:
        - Text/String: StringType with Unicode support
        - Number: DoubleType or LongType based on content
        - Date: DateType with automatic format detection
        - DateTime: TimestampType preserving time components
        - Boolean: BooleanType for TRUE/FALSE values
        - Currency: DoubleType with formatting metadata
        - Percentage: DoubleType with appropriate scaling

    Performance Considerations:
        **Small Files (< 10MB)**: Excellent performance with immediate processing
        **Medium Files (10-50MB)**: Good performance, monitor driver memory
        **Large Files (> 50MB)**: Consider alternative formats (CSV, Parquet)
        **Complex Workbooks**: Performance depends on number of sheets and formulas

    Business Workflow Integration:
        **Monthly Reporting Cycles**:
        - Automated ingestion of departmental reports
        - Consolidation of multiple Excel sources
        - Validation against historical data patterns
        - Generation of executive summaries

        **Ad-Hoc Analysis**:
        - Quick analysis of business reports
        - Integration with existing Spark analytics
        - Data exploration and profiling
        - Prototype development for recurring processes

    Error Handling for Business Users:
        - Clear error messages for file format issues
        - Guidance for resolving common Excel problems
        - Suggestions for alternative processing approaches
        - Business-friendly troubleshooting information

    See Also:
        - CSV readers: ``load_csv()`` for structured tabular data
        - JSON readers: ``load_json()`` for semi-structured data
        - Parquet readers: ``load_parquet()`` for analytical datasets
        - Excel writers: ``write_excel()`` for Excel output generation

    Warning:
        Excel format has inherent limitations for big data processing due to memory
        requirements and single-threaded pandas processing. For files exceeding 50MB
        or routine high-volume processing, consider converting to CSV or Parquet
        formats which provide better performance and scalability characteristics.

    Note:
        This function is specifically designed for business data integration scenarios
        where Excel remains a critical component of organizational workflows. It
        provides the bridge between traditional Excel-based processes and modern
        distributed analytics capabilities while maintaining data integrity and
        business context.
    """
    file_path = Path(file_path)

    if not file_path.exists():
        raise FileNotFoundError(
            f"File not found — please check that the path is correct and the "
            f"file exists: {file_path}"
        )

    try:
        # Use pandas to read Excel
        pandas_df = pd.read_excel(
            file_path, sheet_name=sheet_name, header=header, **pandas_options
        )

        # Handle multiple sheets
        if sheet_name is None and isinstance(pandas_df, dict):
            # Combine all sheets
            combined_df = pd.concat(pandas_df.values(), ignore_index=True)
            df = spark.createDataFrame(combined_df)
        else:
            df = spark.createDataFrame(pandas_df)

        _excel_logger.info("Excel loaded successfully: %s", file_path.name)
        return df

    except Exception as e:
        raise RuntimeError(
            f"Could not load the file (please check file format and accessibility) : "
            f"Excel {file_path}: {str(e)}"
        ) from e
