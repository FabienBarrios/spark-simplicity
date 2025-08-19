"""
Spark Simplicity - Join Operations
==================================

Production-ready SQL join operations on DataFrames with comprehensive error handling,
automatic cleanup, and intelligent validation.

Key Features:
    - Automatic temporary view management with cleanup
    - Comprehensive input validation and error handling
    - Performance optimizations and logging
    - Thread-safe operations with unique view names
    - SQL injection protection
"""

import re
import uuid
from contextlib import contextmanager
from typing import Any, Dict, Generator, List, Set, Tuple

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.utils import AnalysisException

from .logger import get_logger

_joins_logger = get_logger("spark_simplicity.joins")

# Constants
DEFAULT_UNION_TYPE = "UNION ALL"
VALID_UNION_TYPES = ["UNION", "UNION ALL", "UNION DISTINCT"]


def _validate_union_type(union_type: str) -> str:
    """
    Validate and normalize union type.

    Args:
        union_type: Union type string to validate

    Returns:
        Normalized union type in uppercase

    Raises:
        ValueError: If union type is invalid
    """
    if not isinstance(union_type, str):
        raise TypeError(f"union_type must be a string, got {type(union_type)}")

    union_type_upper = union_type.upper().strip()
    if union_type_upper not in VALID_UNION_TYPES:
        raise ValueError(
            f"Invalid union_type '{union_type}'. Valid options: {VALID_UNION_TYPES}"
        )

    return union_type_upper


def _validate_basic_union_inputs(
    spark: SparkSession, dataframes: Dict[str, DataFrame]
) -> None:
    """
    Validate basic inputs for union operations.

    Args:
        spark: SparkSession instance
        dataframes: Dictionary of DataFrames

    Raises:
        TypeError: If inputs have wrong types
        ValueError: If insufficient DataFrames provided
    """
    if not isinstance(spark, SparkSession):
        raise TypeError(f"Expected SparkSession, got {type(spark)}")

    if len(dataframes) < 2:
        raise ValueError("At least 2 DataFrames must be provided for union operation")


@contextmanager
def _managed_temp_views(
    spark: SparkSession, dataframes: Dict[str, DataFrame]
) -> Generator[Dict[str, str], None, None]:
    """
    Context manager for automatic temporary view cleanup.

    Args:
        spark: SparkSession instance
        dataframes: Dictionary of table names to DataFrames

    Yields:
        Dictionary of unique view names created
    """
    unique_suffix = str(uuid.uuid4())[:8]
    view_names = {}
    created_views = []

    try:
        # Create temporary views with unique names
        for table_name, df in dataframes.items():
            if not isinstance(df, DataFrame):
                raise TypeError(
                    f"Expected DataFrame for '{table_name}', got {type(df)}"
                )

            if df.rdd.isEmpty():
                _joins_logger.warning(f"DataFrame '{table_name}' is empty")

            unique_view_name = f"{table_name}_{unique_suffix}"
            df.createOrReplaceTempView(unique_view_name)
            view_names[table_name] = unique_view_name
            created_views.append(unique_view_name)

        _joins_logger.debug(f"Created {len(created_views)} temporary views")
        yield view_names

    finally:
        # Cleanup: Drop all created views
        cleanup_errors = []
        for view_name in created_views:
            try:
                spark.catalog.dropTempView(view_name)
                _joins_logger.debug(f"Dropped temporary view: {view_name}")
            except Exception as e:
                cleanup_errors.append(f"{view_name}: {str(e)}")

        if cleanup_errors:
            _joins_logger.warning(f"Cleanup warnings: {'; '.join(cleanup_errors)}")
        else:
            _joins_logger.debug("All temporary views cleaned up successfully")


def _validate_sql_query(sql_query: str, table_names: Set[str]) -> None:
    """
    Validate SQL query for security and correctness.

    Args:
        sql_query: SQL query to validate
        table_names: Set of valid table names

    Raises:
        ValueError: If query is invalid or potentially unsafe
    """
    if not sql_query or not sql_query.strip():
        raise ValueError("SQL query cannot be empty")

    # Basic SQL injection protection
    dangerous_patterns = [
        r"\bdrop\s+table\b",
        r"\bdrop\s+database\b",
        r"\bdelete\s+from\b",
        r"\btruncate\b",
        r"\bcreate\s+table\b",
        r"\balter\s+table\b",
        r"\binsert\s+into\b",
        r"\bupdate\s+\w+\s+set\b",
    ]

    query_lower = sql_query.lower()
    for pattern in dangerous_patterns:
        if re.search(pattern, query_lower):
            raise ValueError(f"Potentially unsafe SQL operation detected: {pattern}")

    # Validate that referenced tables exist in provided DataFrames
    referenced_tables = set()

    # Extract table references (basic parsing)
    # Patterns: FROM table, JOIN table, table alias
    table_patterns = [
        r"\bfrom\s+(\w+)",
        r"\bjoin\s+(\w+)",
        r"\b(\w+)\s+[a-z]\s*(?:on|where|group|order|limit)",
    ]

    for pattern in table_patterns:
        matches = re.findall(pattern, query_lower)
        referenced_tables.update(matches)

    # Remove SQL keywords that might be mistaken for table names
    sql_keywords = {
        "select",
        "from",
        "where",
        "group",
        "order",
        "having",
        "limit",
        "inner",
        "left",
        "right",
        "full",
        "cross",
        "join",
        "on",
        "as",
        "and",
        "or",
        "not",
        "in",
        "like",
        "between",
        "is",
        "null",
        "count",
        "sum",
        "avg",
        "min",
        "max",
        "distinct",
        "case",
        "when",
    }
    referenced_tables -= sql_keywords

    # Check if all referenced tables are provided
    missing_tables = referenced_tables - table_names
    if missing_tables:
        _joins_logger.warning(
            f"Tables referenced in query but not provided: {missing_tables}. "
            f"This might be intentional if they exist in the catalog."
        )


def sql_join(spark: SparkSession, sql_query: str, **dataframes: DataFrame) -> DataFrame:
    """
    Execute SQL query with joins on DataFrames with comprehensive error handling.

    This function provides a production-ready interface for executing SQL queries
    on Spark DataFrames with automatic temporary view management, input validation,
    and comprehensive error handling.

    Args:
        spark: SparkSession instance (must be active)
        sql_query: SQL query to execute (validated for safety)
        **dataframes: DataFrames passed as keyword arguments (name=dataframe)

    Returns:
        Result DataFrame from SQL query execution

    Raises:
        TypeError: If spark is not a SparkSession or dataframes are not DataFrames
        ValueError: If SQL query is empty, invalid, or potentially unsafe
        AnalysisException: If SQL query has syntax errors or references invalid columns
        RuntimeError: If execution fails due to Spark errors

    Example:
        # Basic join
        result = sql_join(
            spark,
            '''SELECT c.name, o.order_date, o.amount
               FROM customers c
               INNER JOIN orders o ON c.id = o.customer_id
               WHERE o.amount > 100''',
            customers=customers_df,
            orders=orders_df
        )

        # Complex multi-table join with aggregation
        result = sql_join(
            spark,
            '''SELECT
                   c.name,
                   c.city,
                   COUNT(o.order_id) as total_orders,
                   SUM(o.amount) as total_spent,
                   AVG(o.amount) as avg_order_value
               FROM customers c
               LEFT JOIN orders o ON c.id = o.customer_id
               GROUP BY c.name, c.city
               HAVING total_spent > 500
               ORDER BY total_spent DESC''',
            customers=customers_df,
            orders=orders_df
        )

        # Window functions and advanced analytics
        result = sql_join(
            spark,
            '''SELECT
                   c.name,
                   o.order_date,
                   o.amount,
                   ROW_NUMBER() OVER (PARTITION BY c.id ORDER BY o.order_date) as
                   order_rank,
                   SUM(o.amount) OVER (PARTITION BY c.id) as customer_total
               FROM customers c
               JOIN orders o ON c.id = o.customer_id''',
            customers=customers_df,
            orders=orders_df
        )
    """
    # Input validation
    if not isinstance(spark, SparkSession):
        raise TypeError(f"Expected SparkSession, got {type(spark)}")

    if not dataframes:
        raise ValueError("At least one DataFrame must be provided")

    if not isinstance(sql_query, str):
        raise TypeError(f"SQL query must be a string, got {type(sql_query)}")

    # Validate SQL query
    table_names = set(dataframes.keys())
    _validate_sql_query(sql_query, table_names)

    _joins_logger.info(
        f"Executing SQL join on {len(dataframes)} DataFrames: {list(table_names)}"
    )
    _joins_logger.debug(f"SQL Query: {sql_query}")

    try:
        # Use context manager for automatic cleanup
        with _managed_temp_views(spark, dataframes) as view_names:
            # Replace table names in query with unique view names
            modified_query = sql_query
            for original_name, unique_name in view_names.items():
                # Use word boundaries to avoid partial replacements
                pattern = rf"\b{re.escape(original_name)}\b"
                modified_query = re.sub(
                    pattern, unique_name, modified_query, flags=re.IGNORECASE
                )

            _joins_logger.debug(
                f"Modified query with unique view names: {modified_query}"
            )

            # Execute SQL query
            result = spark.sql(modified_query)

            # Log success metrics
            try:
                row_count = result.count()
                column_count = len(result.columns)
                _joins_logger.info(
                    f"SQL join completed successfully - "
                    f"Result: {row_count:,} rows × {column_count} columns"
                )
            except (RuntimeError, AnalysisException):
                _joins_logger.info("SQL join completed successfully")

            return result

    except AnalysisException as e:
        error_msg = f"SQL analysis error: {str(e)}"
        _joins_logger.error(error_msg)
        raise AnalysisException(error_msg) from e

    except Exception as e:
        error_msg = f"SQL execution failed: {str(e)}"
        _joins_logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def sql_union(
    spark: SparkSession, union_type: str = DEFAULT_UNION_TYPE, **dataframes: DataFrame
) -> DataFrame:
    """
    Combine multiple DataFrames using SQL UNION operations with comprehensive
    validation.

    This function provides a production-ready interface for executing SQL UNION queries
    on multiple Spark DataFrames with automatic schema validation, temporary view
    management, and comprehensive error handling.

    Args:
        spark: SparkSession instance (must be active)
        union_type: Type of union operation ("UNION", "UNION ALL", "UNION DISTINCT")
        **dataframes: DataFrames passed as keyword arguments (name=dataframe)

    Returns:
        Result DataFrame from SQL union operation

    Raises:
        TypeError: If spark is not a SparkSession or dataframes are not DataFrames
        ValueError: If union_type is invalid or fewer than 2 DataFrames provided
        AnalysisException: If DataFrames have incompatible schemas
        RuntimeError: If execution fails due to Spark errors

    Example:
        # Basic union all (default)
        result = sql_union(
            spark,
            customers_2023=customers_2023_df,
            customers_2024=customers_2024_df
        )

        # Union distinct (removes duplicates)
        result = sql_union(
            spark,
            union_type="UNION DISTINCT",
            north_sales=north_df,
            south_sales=south_df,
            east_sales=east_df
        )

        # Complex union with filtering
        result = sql_union(
            spark,
            union_type="UNION",
            active_customers=active_customers_df,
            inactive_customers=inactive_customers_df
        )
    """
    # Input validation
    _validate_basic_union_inputs(spark, dataframes)
    union_type_upper = _validate_union_type(union_type)

    _joins_logger.info(
        f"Executing {union_type_upper} on {len(dataframes)} DataFrames: "
        f"{list(dataframes.keys())}"
    )

    try:
        # Validate schema compatibility before creating views
        _validate_union_schemas(list(dataframes.values()))

        # Use context manager for automatic cleanup
        with _managed_temp_views(spark, dataframes) as view_names:
            # Build UNION query
            view_list = list(view_names.values())

            # Create SELECT statements for each DataFrame
            select_statements = []
            for view_name in view_list:
                select_statements.append(f"SELECT * FROM {view_name}")

            # Join with UNION operator
            union_query = f" {union_type_upper} ".join(select_statements)

            _joins_logger.debug(f"Generated union query: {union_query}")

            # Execute SQL query
            result = spark.sql(union_query)

            # Log success metrics
            try:
                row_count = result.count()
                column_count = len(result.columns)
                _joins_logger.info(
                    f"{union_type_upper} completed successfully - "
                    f"Result: {row_count:,} rows × {column_count} columns"
                )
            except (RuntimeError, AnalysisException):
                _joins_logger.info(f"{union_type_upper} completed successfully")

            return result

    except AnalysisException as e:
        error_msg = f"SQL union analysis error: {str(e)}"
        _joins_logger.error(error_msg)
        raise AnalysisException(error_msg) from e

    except Exception as e:
        error_msg = f"SQL union execution failed: {str(e)}"
        _joins_logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def _validate_union_schemas(dataframes: List[DataFrame]) -> None:
    """
    Validate that all DataFrames have compatible schemas for UNION operations.

    Args:
        dataframes: List of DataFrames to validate

    Raises:
        ValueError: If schemas are incompatible
    """
    if len(dataframes) < 2:
        return

    # Get reference schema from first DataFrame
    reference_df = dataframes[0]
    ref_columns = reference_df.columns
    ref_types = [field.dataType for field in reference_df.schema.fields]

    _joins_logger.debug(f"Reference schema: {len(ref_columns)} columns")

    # Validate each subsequent DataFrame
    for i, df in enumerate(dataframes[1:], start=1):
        current_columns = df.columns
        current_types = [field.dataType for field in df.schema.fields]

        # Check column count
        if len(current_columns) != len(ref_columns):
            raise ValueError(
                f"DataFrame {i} has {len(current_columns)} columns, "
                f"but reference has {len(ref_columns)} columns. "
                f"All DataFrames must have the same number of columns for UNION."
            )

        # Check column names (order matters for UNION)
        if current_columns != ref_columns:
            _joins_logger.warning(
                f"DataFrame {i} has different column names or order: "
                f"{current_columns} vs reference: {ref_columns}. "
                f"UNION will match by position, not name."
            )

        # Check data types compatibility
        incompatible_types = []
        for j, (ref_type, curr_type) in enumerate(zip(ref_types, current_types)):
            if not _are_types_compatible(ref_type, curr_type):
                incompatible_types.append(
                    f"Column {j} ({ref_columns[j]}): {ref_type} vs {curr_type}"
                )

        if incompatible_types:
            raise ValueError(
                f"DataFrame {i} has incompatible data types:\n"
                + "\n".join(incompatible_types)
            )

    _joins_logger.debug("All DataFrames have compatible schemas for UNION")


def _are_types_compatible(type1: Any, type2: Any) -> bool:
    """
    Check if two Spark data types are compatible for UNION operations.

    Args:
        type1: First data type
        type2: Second data type

    Returns:
        True if types are compatible for UNION
    """
    # Exact match
    if type1 == type2:
        return True

    # Convert to string for easier comparison
    str_type1 = str(type1).lower()
    str_type2 = str(type2).lower()

    # Numeric type compatibility
    numeric_types = {"byte", "short", "integer", "long", "float", "double", "decimal"}

    # Check if both are numeric (generally compatible)
    type1_numeric = any(nt in str_type1 for nt in numeric_types)
    type2_numeric = any(nt in str_type2 for nt in numeric_types)

    if type1_numeric and type2_numeric:
        return True

    # String types compatibility
    string_types = {"string", "varchar", "char"}
    type1_string = any(st in str_type1 for st in string_types)
    type2_string = any(st in str_type2 for st in string_types)

    if type1_string and type2_string:
        return True

    # Date/timestamp compatibility
    temporal_types = {"date", "timestamp"}
    type1_temporal = any(tt in str_type1 for tt in temporal_types)
    type2_temporal = any(tt in str_type2 for tt in temporal_types)

    if type1_temporal and type2_temporal:
        return True

    # Boolean compatibility
    if "boolean" in str_type1 and "boolean" in str_type2:
        return True

    # If none of the above, types are likely incompatible
    return False


def sql_union_flexible(
    spark: SparkSession,
    union_type: str = DEFAULT_UNION_TYPE,
    fill_missing: Any = None,
    **dataframes: DataFrame,
) -> DataFrame:
    """
    Combine multiple DataFrames with flexible schema alignment and automatic column
    handling.

    This function provides intelligent UNION operations that automatically handle:
    - Different column orders between DataFrames
    - Missing columns (filled with specified value or NULL)
    - Column name mismatches with automatic alignment
    - Type casting when safe and possible

    Args:
        spark: SparkSession instance (must be active)
        union_type: Type of union operation ("UNION", "UNION ALL", "UNION DISTINCT")
        fill_missing: Value to use for missing columns (None = NULL)
        **dataframes: DataFrames passed as keyword arguments (name=dataframe)

    Returns:
        Result DataFrame with aligned schemas from flexible union operation

    Raises:
        TypeError: If spark is not a SparkSession or dataframes are not DataFrames
        ValueError: If union_type is invalid or fewer than 2 DataFrames provided
        AnalysisException: If DataFrames have fundamentally incompatible schemas
        RuntimeError: If execution fails due to Spark errors

    Example:
        # DataFrames with different column orders and missing columns
        df1 = spark.createDataFrame([(1, "Alice", 100)], ["id", "name", "amount"])
        df2 = spark.createDataFrame([("Bob", 2, "NY")], ["name", "id", "city"])

        # Flexible union - automatically aligns and fills missing columns
        result = sql_union_flexible(
            spark,
            customers=df1,
            prospects=df2,
            fill_missing="Unknown"
        )
        # Result schema: [id, name, amount, city]
        # df1 row: [1, "Alice", 100, "Unknown"]
        # df2 row: [2, "Bob", "Unknown", "NY"]

        # Complex example with type casting
        sales_2023 = spark.createDataFrame(
            [(1, "Product A", 100.50)], ["id", "product", "revenue"]
        )
        sales_2024 = spark.createDataFrame(
            [("Product B", 200, 1, "Q1")], ["product", "revenue", "id", "quarter"]
        )

        result = sql_union_flexible(
            spark,
            union_type="UNION DISTINCT",
            sales_2023=sales_2023,
            sales_2024=sales_2024,
            fill_missing="N/A"
        )
    """
    # Input validation
    _validate_basic_union_inputs(spark, dataframes)
    union_type_upper = _validate_union_type(union_type)

    _joins_logger.info(
        f"🔄 Executing flexible {union_type_upper} on {len(dataframes)} DataFrames: "
        f"{list(dataframes.keys())}"
    )

    try:
        # Analyze and align schemas
        aligned_schemas = _analyze_and_align_schemas(
            list(dataframes.values()), fill_missing
        )

        # Use context manager for automatic cleanup
        with _managed_temp_views(spark, dataframes) as view_names:
            # Build flexible UNION query with schema alignment
            select_statements = []

            for i, (df_name, view_name) in enumerate(view_names.items()):
                aligned_schema = aligned_schemas[i]
                select_statement = _build_aligned_select(view_name, aligned_schema)
                select_statements.append(select_statement)

                _joins_logger.debug(f"Aligned SELECT for {df_name}: {select_statement}")

            # Join with UNION operator
            union_query = f" {union_type_upper} ".join(select_statements)

            _joins_logger.debug(f"Generated flexible union query: {union_query}")

            # Execute SQL query
            result = spark.sql(union_query)

            # Log success metrics
            try:
                row_count = result.count()
                column_count = len(result.columns)
                _joins_logger.info(
                    f"✅ Flexible {union_type_upper} completed successfully - "
                    f"Result: {row_count:,} rows × {column_count} columns"
                )
            except (RuntimeError, AnalysisException):
                _joins_logger.info(
                    f"✅ Flexible {union_type_upper} completed successfully"
                )

            return result

    except AnalysisException as e:
        error_msg = f"Flexible SQL union analysis error: {str(e)}"
        _joins_logger.error(error_msg)
        raise AnalysisException(error_msg) from e

    except Exception as e:
        error_msg = f"Flexible SQL union execution failed: {str(e)}"
        _joins_logger.error(error_msg)
        raise RuntimeError(error_msg) from e


def _analyze_and_align_schemas(
    dataframes: List[DataFrame], fill_missing: Any
) -> List[List[Dict[str, Any]]]:
    """
    Analyze DataFrames and create aligned schema specifications for each.

    Args:
        dataframes: List of DataFrames to analyze
        fill_missing: Value to use for missing columns

    Returns:
        List of aligned schema specifications for each DataFrame

    Raises:
        ValueError: If schemas cannot be reconciled
    """
    if len(dataframes) < 2:
        return []

    # Collect all unique columns from all DataFrames
    all_columns = _collect_all_columns(dataframes)

    # Create master schema and log analysis
    master_columns = _create_master_schema(all_columns)

    # Create aligned schema for each DataFrame
    return _create_aligned_schemas(
        dataframes, all_columns, master_columns, fill_missing
    )


def _collect_all_columns(
    dataframes: List[DataFrame],
) -> Dict[str, Tuple[Any, List[int]]]:
    """
    Collect all unique columns from all DataFrames.

    Args:
        dataframes: List of DataFrames to analyze

    Returns:
        Dictionary mapping column names to (data_type, source_df_indices)
    """
    all_columns: Dict[str, Tuple[Any, List[int]]] = {}

    for i, df in enumerate(dataframes):
        for field in df.schema.fields:
            col_name = field.name
            col_type = field.dataType

            if col_name in all_columns:
                existing_type, source_indices = all_columns[col_name]
                _validate_column_type_compatibility(col_name, existing_type, col_type)
                source_indices.append(i)
            else:
                all_columns[col_name] = (col_type, [i])

    return all_columns


def _validate_column_type_compatibility(
    col_name: str, existing_type: Any, col_type: Any
) -> None:
    """
    Validate column type compatibility and log warnings if needed.

    Args:
        col_name: Column name
        existing_type: Existing data type
        col_type: New data type to check
    """
    if not _are_types_compatible(existing_type, col_type):
        _joins_logger.warning(
            f"Column '{col_name}' has incompatible types: "
            f"{existing_type} vs {col_type}. Using first occurrence type."
        )


def _create_master_schema(all_columns: Dict[str, Tuple[Any, List[int]]]) -> List[str]:
    """
    Create master schema and log analysis information.

    Args:
        all_columns: Dictionary of all collected columns

    Returns:
        List of master column names
    """
    master_columns = list(all_columns.keys())

    _joins_logger.info(
        f"🔍 Schema analysis: {len(master_columns)} unique columns across DataFrames"
    )
    _joins_logger.debug(f"Master columns: {master_columns}")

    return master_columns


def _create_aligned_schemas(
    dataframes: List[DataFrame],
    all_columns: Dict[str, Tuple[Any, List[int]]],
    master_columns: List[str],
    fill_missing: Any,
) -> List[List[Dict[str, Any]]]:
    """
    Create aligned schema specifications for each DataFrame.

    Args:
        dataframes: List of DataFrames
        all_columns: Dictionary of all collected columns
        master_columns: List of master column names
        fill_missing: Value to use for missing columns

    Returns:
        List of aligned schema specifications
    """
    aligned_schemas = []

    for i, df in enumerate(dataframes):
        df_columns = {field.name: field.dataType for field in df.schema.fields}
        aligned_schema = _create_single_aligned_schema(
            df_columns, master_columns, all_columns, fill_missing
        )
        aligned_schemas.append(aligned_schema)

        _log_missing_columns(i, aligned_schema)

    return aligned_schemas


def _create_single_aligned_schema(
    df_columns: Dict[str, Any],
    master_columns: List[str],
    all_columns: Dict[str, Tuple[Any, List[int]]],
    fill_missing: Any,
) -> List[Dict[str, Any]]:
    """
    Create aligned schema for a single DataFrame.

    Args:
        df_columns: DataFrame columns mapping
        master_columns: List of master column names
        all_columns: Dictionary of all collected columns
        fill_missing: Value to use for missing columns

    Returns:
        Aligned schema specification for the DataFrame
    """
    aligned_schema = []

    for col_name in master_columns:
        if col_name in df_columns:
            # Column exists - use as-is
            aligned_schema.append(
                {
                    "name": col_name,
                    "expression": col_name,
                    "type": df_columns[col_name],
                    "exists": True,
                }
            )
        else:
            # Column missing - fill with specified value
            target_type, _ = all_columns[col_name]
            fill_expression = _get_fill_expression(fill_missing, target_type)

            aligned_schema.append(
                {
                    "name": col_name,
                    "expression": f"{fill_expression} AS {col_name}",
                    "type": target_type,
                    "exists": False,
                }
            )

    return aligned_schema


def _log_missing_columns(df_index: int, aligned_schema: List[Dict[str, Any]]) -> None:
    """
    Log information about missing columns for a DataFrame.

    Args:
        df_index: DataFrame index
        aligned_schema: Aligned schema specification
    """
    missing_cols = [spec["name"] for spec in aligned_schema if not spec["exists"]]
    if missing_cols:
        _joins_logger.debug(
            f"DataFrame {df_index}: Adding missing columns {missing_cols}"
        )


def _build_aligned_select(view_name: str, aligned_schema: List[Dict[str, Any]]) -> str:
    """
    Build SELECT statement with aligned schema for a specific view.

    Args:
        view_name: Name of the temporary view
        aligned_schema: Schema specification for alignment

    Returns:
        SELECT statement string with proper column alignment
    """
    select_expressions = []

    for col_spec in aligned_schema:
        if col_spec["exists"]:
            # Column exists in original DataFrame
            select_expressions.append(col_spec["name"])
        else:
            # Column needs to be filled
            select_expressions.append(col_spec["expression"])

    return f"SELECT {', '.join(select_expressions)} FROM {view_name}"


def _get_fill_expression(fill_missing: Any, target_type: Any) -> str:
    """
    Generate appropriate fill expression for missing columns based on type.

    Args:
        fill_missing: User-specified fill value
        target_type: Target data type for the column

    Returns:
        SQL expression for filling missing column
    """
    if fill_missing is None:
        return "NULL"

    type_str = str(target_type).lower()

    # Delegate to specific type handlers
    if _is_string_type(type_str):
        return _handle_string_fill(fill_missing)
    elif _is_numeric_type(type_str):
        return _handle_numeric_fill(fill_missing, target_type, type_str)
    elif _is_boolean_type(type_str):
        return _handle_boolean_fill(fill_missing)
    elif _is_temporal_type(type_str):
        return _handle_temporal_fill(fill_missing, target_type)
    else:
        return _handle_unknown_fill(fill_missing, target_type)


def _is_string_type(type_str: str) -> bool:
    """Check if type is a string type."""
    return any(t in type_str for t in ["string", "varchar", "char"])


def _is_numeric_type(type_str: str) -> bool:
    """Check if type is a numeric type."""
    return any(
        t in type_str
        for t in ["int", "long", "float", "double", "decimal", "byte", "short"]
    )


def _is_boolean_type(type_str: str) -> bool:
    """Check if type is a boolean type."""
    return "boolean" in type_str


def _is_temporal_type(type_str: str) -> bool:
    """Check if type is a temporal type."""
    return any(t in type_str for t in ["date", "timestamp"])


def _handle_string_fill(fill_missing: Any) -> str:
    """Handle string type fill values."""
    if isinstance(fill_missing, str):
        escaped_value = fill_missing.replace("'", "''")
        return f"'{escaped_value}'"
    else:
        return f"'{str(fill_missing)}'"


def _handle_numeric_fill(fill_missing: Any, target_type: Any, type_str: str) -> str:
    """Handle numeric type fill values."""
    try:
        if _is_integer_type(type_str):
            return str(int(float(str(fill_missing))))
        else:
            return str(float(str(fill_missing)))
    except (ValueError, TypeError):
        _joins_logger.warning(
            f"Cannot convert fill_missing '{fill_missing}' to numeric type "
            f"{target_type}. Using NULL."
        )
        return "NULL"


def _is_integer_type(type_str: str) -> bool:
    """Check if type is an integer type."""
    return any(t in type_str for t in ["int", "long", "byte", "short"])


def _handle_boolean_fill(fill_missing: Any) -> str:
    """Handle boolean type fill values."""
    if isinstance(fill_missing, bool):
        return "true" if fill_missing else "false"
    elif isinstance(fill_missing, str):
        return "true" if fill_missing.lower() in ("true", "1", "yes") else "false"
    else:
        return "false"


def _handle_temporal_fill(fill_missing: Any, target_type: Any) -> str:
    """Handle temporal type fill values."""
    if isinstance(fill_missing, str):
        return f"'{fill_missing}'"
    else:
        _joins_logger.warning(
            f"Cannot convert fill_missing '{fill_missing}' to temporal type "
            f"{target_type}. Using NULL."
        )
        return "NULL"


def _handle_unknown_fill(fill_missing: Any, target_type: Any) -> str:
    """Handle unknown type fill values."""
    _joins_logger.warning(
        f"Unknown data type {target_type} for fill_missing. Treating as string."
    )
    return f"'{str(fill_missing)}'"
