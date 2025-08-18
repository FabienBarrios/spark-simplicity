"""
Spark Simplicity - Utility Functions
====================================

Utility functions for DataFrame optimization and analysis.
This module provides helpful functions for DataFrame manipulation and tuning.

Key Features:
    - DataFrame analysis and profiling
    - Performance optimization utilities
    - Caching and persistence management
    - Partitioning optimization
    - Memory usage analysis

Usage:
     from spark_simplicity import describe_dataframe, optimize_dataframe
     describe_dataframe(df)
     optimized_df = optimize_dataframe(df)
"""

from typing import Any, Dict, List, Optional, Sequence, Union

from pyspark.sql import DataFrame
from pyspark.sql.functions import col

# Import du logger spécialisé
from .logger import get_logger

# Logger spécialisé pour les utilitaires
_utils_logger = get_logger("spark_simplicity.utils")


def clean_nulls_and_empty(
    df: DataFrame,
    replacement_value: str = "",
    columns: Optional[List[str]] = None,
    null_values: Optional[List[str]] = None,
) -> DataFrame:
    """
    Replace NULL, empty strings, and NaN-like values with a replacement value.

    Args:
        df: DataFrame to clean
        replacement_value: Value to use as replacement
        columns: Specific columns to clean (None = all string columns)
        null_values: Additional values to treat as null/empty

    Returns:
        Cleaned DataFrame

    Example:
         df_clean = clean_nulls_and_empty(df, "Non renseigné")
         df_clean = clean_nulls_and_empty(df, "N/A", ["nom", "ville"])
         df_clean = clean_nulls_and_empty(
             df, "Vide", null_values=["undefined", "missing"]
         )
    """
    try:
        # Default null values to replace
        default_null_values = ["", "NaN", "nan", "null", "NULL", "None", "N/A", "n/a"]

        # Combine default and user-provided null values
        if null_values:
            all_null_values = list(set(default_null_values + null_values))
        else:
            all_null_values = default_null_values

        # Determine columns to clean
        if columns is None:
            # Clean all string columns
            target_columns = [
                col_name for col_name, _ in df.dtypes if "string" in _.lower()
            ]
        else:
            # Validate provided columns exist
            missing_cols = set(columns) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Columns not found: {missing_cols}")
            target_columns = columns

        if not target_columns:
            _utils_logger.info("No string columns to clean")
            return df

        # Step 1: Replace NULL values
        fill_dict: Dict[str, Union[str, int, float, bool]] = dict.fromkeys(
            target_columns, replacement_value
        )
        df_clean = df.fillna(fill_dict)

        # Step 2: Replace empty strings and NaN-like values
        # Use sequence for covariant typing
        null_values_seq: Sequence[Union[str, int, float, bool]] = all_null_values
        df_clean = df_clean.replace(list(null_values_seq), replacement_value)

        _utils_logger.info(
            "🧹 Cleaned NULL/empty values in %d columns: %s",
            len(target_columns),
            target_columns,
        )

        return df_clean

    except Exception as e:
        _utils_logger.error("⚠️  Error cleaning DataFrame: %s", str(e))
        return df


def analyze_data_quality(
    df: DataFrame, sample_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform basic data quality analysis on a DataFrame.

    Args:
        df: DataFrame to analyze
        sample_size: Number of rows to sample (None = full DataFrame)

    Returns:
        Dictionary containing data quality metrics

    Example:
         quality_report = analyze_data_quality(df, sample_size=10000)
         quality_report['overall_score']  # Returns data quality score
    """
    try:
        # Sample DataFrame if requested
        analysis_df = df
        if sample_size and df.count() > sample_size:
            analysis_df = df.sample(fraction=sample_size / df.count(), seed=42)

        row_count = analysis_df.count()
        columns = analysis_df.columns

        quality_metrics: Dict[str, Any] = {
            "row_count": row_count,
            "column_count": len(columns),
            "completeness": {},  # Percentage of non-null values per column
            "uniqueness": {},  # Percentage of unique values per column
            "consistency": {},  # Data type consistency
        }

        # Analyze each column
        for column in columns:
            # Completeness (non-null percentage)
            non_null_count = analysis_df.filter(col(column).isNotNull()).count()
            completeness = (non_null_count / row_count) * 100 if row_count > 0 else 0
            quality_metrics["completeness"][column] = completeness

            # Uniqueness (distinct value percentage)
            if row_count > 0:
                distinct_count = analysis_df.select(column).distinct().count()
                uniqueness = (distinct_count / row_count) * 100
                quality_metrics["uniqueness"][column] = min(uniqueness, 100.0)
            else:
                quality_metrics["uniqueness"][column] = 0

        # Calculate overall quality score
        avg_completeness = (
            sum(quality_metrics["completeness"].values()) / len(columns)
            if columns
            else 0
        )
        quality_metrics["overall_score"] = avg_completeness

        # Identify potential issues
        issues = []
        for column, completeness in quality_metrics["completeness"].items():
            if completeness < 90:
                issues.append(
                    f"Column '{column}' has {100-completeness:.1f}% missing values"
                )

        quality_metrics["issues"] = issues

        return quality_metrics

    except Exception as e:
        return {"error": f"Failed to analyze data quality: {e}"}


def profile_dataframe_performance(
    df: DataFrame, operation_name: str = "operation"
) -> Dict[str, Any]:
    """
    Profile DataFrame operation performance.

    Args:
        df: DataFrame to profile
        operation_name: Name of the operation being profiled

    Returns:
        Dictionary containing performance metrics

    Example:
         # Profile a transformation
         df_transformed = df.filter(col("age") > 18)
         perf_metrics = profile_dataframe_performance(df_transformed, "age_filter")
    """
    try:
        import time

        start_time = time.time()

        # Force evaluation to measure actual performance
        row_count = df.count()
        partition_count = df.rdd.getNumPartitions()

        end_time = time.time()
        duration = end_time - start_time

        metrics = {
            "operation": operation_name,
            "row_count": row_count,
            "partition_count": partition_count,
            "duration_seconds": duration,
            "rows_per_second": row_count / duration if duration > 0 else 0,
            "timestamp": time.time(),
        }

        _utils_logger.info("📊 Performance Profile - %s:", operation_name)
        _utils_logger.info("   Rows: %d", row_count)
        _utils_logger.info("   Partitions: %d", partition_count)
        _utils_logger.info("   Duration: %.2fs", duration)
        _utils_logger.info("   Throughput: %.0f rows/sec", metrics["rows_per_second"])

        return metrics

    except Exception as e:
        return {"error": f"Failed to profile performance: {e}"}


def compare_dataframes(
    df1: DataFrame, df2: DataFrame, key_columns: List[str]
) -> Dict[str, Any]:
    """
    Compare two DataFrames and identify differences.

    Args:
        df1: First DataFrame
        df2: Second DataFrame
        key_columns: Columns to use as join keys for comparison

    Returns:
        Dictionary containing comparison results

    Example:
         comparison = compare_dataframes(df_old, df_new, ["id"])
         comparison['only_in_df1']  # Returns rows only in df1
         comparison['only_in_df2']  # Returns rows only in df2
    """
    try:
        # Validate key columns exist in both DataFrames
        missing_cols_df1 = set(key_columns) - set(df1.columns)
        missing_cols_df2 = set(key_columns) - set(df2.columns)

        if missing_cols_df1:
            raise ValueError(f"Key columns missing in df1: {missing_cols_df1}")
        if missing_cols_df2:
            raise ValueError(f"Key columns missing in df2: {missing_cols_df2}")

        # Count rows
        count_df1 = df1.count()
        count_df2 = df2.count()

        # Find rows only in df1 (left anti join)
        only_in_df1 = df1.join(df2, key_columns, "left_anti").count()

        # Find rows only in df2 (left anti join)
        only_in_df2 = df2.join(df1, key_columns, "left_anti").count()

        # Find common rows
        common_rows = df1.join(df2, key_columns, "inner").count()

        comparison = {
            "df1_row_count": count_df1,
            "df2_row_count": count_df2,
            "only_in_df1": only_in_df1,
            "only_in_df2": only_in_df2,
            "common_rows": common_rows,
            "key_columns": key_columns,
            "identical": only_in_df1 == 0
            and only_in_df2 == 0
            and count_df1 == count_df2,
        }

        _utils_logger.info("📈 DataFrame Comparison:")
        _utils_logger.info("   DF1 rows: %d", count_df1)
        _utils_logger.info("   DF2 rows: %d", count_df2)
        _utils_logger.info("   Only in DF1: %d", only_in_df1)
        _utils_logger.info("   Only in DF2: %d", only_in_df2)
        _utils_logger.info("   Common rows: %d", common_rows)
        _utils_logger.info("   Identical: %s", comparison["identical"])

        return comparison

    except Exception as e:
        return {"error": f"Failed to compare DataFrames: {e}"}
