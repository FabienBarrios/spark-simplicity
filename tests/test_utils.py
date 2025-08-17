"""
Spark Simplicity - Utils Module Tests
====================================

Comprehensive test suite for the utils module with enterprise-grade
coverage and validation.

This module provides extensive testing of DataFrame utility functions,
data quality analysis, performance profiling, and DataFrame comparison
functionality essential for production Spark data processing environments.

Key Testing Areas:
    - **DataFrame Cleaning**: NULL and empty value handling with various configurations
    - **Data Quality Analysis**: Completeness, uniqueness, and consistency metrics
    - **Performance Profiling**: DataFrame operation timing and throughput measurement
    - **DataFrame Comparison**: Comprehensive DataFrame difference analysis
    - **Edge Cases**: Empty DataFrames, invalid inputs, and error scenarios

Test Coverage:
    **clean_nulls_and_empty Function**:
    - String column cleaning with default and custom replacement values
    - Custom column filtering and validation
    - Custom null value list handling
    - Missing column error scenarios
    - Empty DataFrame and no string columns scenarios

    **analyze_data_quality Function**:
    - Completeness analysis for all data types
    - Uniqueness calculation and percentage metrics
    - Overall quality score computation
    - Sample size handling for large DataFrames
    - Quality issue identification and reporting

    **profile_dataframe_performance Function**:
    - Execution time measurement and row count analysis
    - Partition count evaluation and throughput calculation
    - Custom operation naming and timestamp recording
    - Performance metrics validation

    **compare_dataframes Function**:
    - DataFrame difference detection using key columns
    - Common row identification and count validation
    - Missing key column error handling
    - Identical DataFrame detection

Enterprise Integration Testing:
    - **Error Handling**: Comprehensive exception handling and graceful degradation
    - **Performance Validation**: Large dataset simulation and optimization
    - **Data Type Support**: String, numeric, boolean, and null value handling
    - **Production Scenarios**: Real-world data quality and comparison patterns

Testing Philosophy:
    This test suite follows enterprise software development best practices with
    comprehensive coverage, realistic scenario simulation, and production-ready
    validation patterns. All tests validate both functional correctness and
    operational reliability in production DataFrame processing environments.
"""

from typing import Any
from unittest.mock import Mock, patch

import pytest
from pyspark.sql import DataFrame

from spark_simplicity.utils import (
    analyze_data_quality,
    clean_nulls_and_empty,
    compare_dataframes,
    profile_dataframe_performance,
)


class TestCleanNullsAndEmpty:
    """
    Comprehensive test suite for clean_nulls_and_empty function with 100% coverage.

    This test class validates all aspects of NULL and empty value cleaning
    functionality including default behavior, custom configurations, column
    filtering, error handling, and edge cases. Tests use mocks to avoid
    Spark environment dependencies.
    """

    def test_basic_cleaning_default_behavior(self, mock_spark_session: Any) -> None:
        """Test basic NULL and empty value cleaning with default settings."""
        # Create mock DataFrame
        mock_df = Mock(spec=DataFrame)
        mock_df.dtypes = [("id", "int"), ("name", "string"), ("city", "string")]
        mock_df.columns = ["id", "name", "city"]

        # Mock cleaned DataFrame
        mock_cleaned_df = Mock(spec=DataFrame)
        mock_df.fillna.return_value = mock_cleaned_df
        mock_cleaned_df.replace.return_value = mock_cleaned_df

        result_df = clean_nulls_and_empty(mock_df)

        # Verify fillna was called with proper dictionary
        mock_df.fillna.assert_called_once()
        mock_cleaned_df.replace.assert_called_once()
        assert result_df is mock_cleaned_df

    def test_custom_replacement_value(self, mock_spark_session: Any) -> None:
        """Test NULL and empty value cleaning with custom replacement value."""
        mock_df = Mock(spec=DataFrame)
        mock_df.dtypes = [("name", "string")]
        mock_df.columns = ["name"]

        mock_cleaned_df = Mock(spec=DataFrame)
        mock_df.fillna.return_value = mock_cleaned_df
        mock_cleaned_df.replace.return_value = mock_cleaned_df

        result_df = clean_nulls_and_empty(mock_df, replacement_value="CUSTOM")

        mock_df.fillna.assert_called_once_with({"name": "CUSTOM"})
        assert result_df is mock_cleaned_df

    def test_specific_columns_cleaning(self, mock_spark_session: Any) -> None:
        """Test cleaning specific columns only."""
        mock_df = Mock(spec=DataFrame)
        mock_df.columns = ["id", "name", "city", "status"]

        mock_cleaned_df = Mock(spec=DataFrame)
        mock_df.fillna.return_value = mock_cleaned_df
        mock_cleaned_df.replace.return_value = mock_cleaned_df

        result_df = clean_nulls_and_empty(
            mock_df, replacement_value="CLEAN", columns=["name", "city"]
        )

        # Should only clean specified columns
        expected_fill_dict = {"name": "CLEAN", "city": "CLEAN"}
        mock_df.fillna.assert_called_once_with(expected_fill_dict)
        assert result_df is mock_cleaned_df

    @patch("spark_simplicity.utils._utils_logger")
    def test_missing_columns_error(
        self, mock_logger: Mock, mock_spark_session: Any
    ) -> None:
        """Test error handling for missing columns."""
        mock_df = Mock(spec=DataFrame)
        mock_df.columns = ["id", "name"]

        result_df = clean_nulls_and_empty(mock_df, columns=["nonexistent_column"])

        # Function should return original DataFrame and log error
        assert result_df is mock_df
        mock_logger.error.assert_called_once()
        error_call_args = str(mock_logger.error.call_args)
        assert "Columns not found" in error_call_args
        assert "nonexistent_column" in error_call_args

    def test_no_string_columns_scenario(self, mock_spark_session: Any) -> None:
        """Test behavior when DataFrame has no string columns."""
        mock_df = Mock(spec=DataFrame)
        mock_df.dtypes = [("id", "int"), ("value", "double")]
        mock_df.columns = ["id", "value"]

        result_df = clean_nulls_and_empty(mock_df)

        # Should return original DataFrame unchanged
        assert result_df is mock_df
        mock_df.fillna.assert_not_called()

    @patch("spark_simplicity.utils._utils_logger")
    def test_exception_handling_returns_original_df(
        self, mock_logger: Mock, mock_spark_session: Any
    ) -> None:
        """Test exception handling returns original DataFrame."""
        mock_df = Mock(spec=DataFrame)
        mock_df.dtypes = [("name", "string")]
        mock_df.columns = ["name"]
        mock_df.fillna.side_effect = Exception("Test error")

        result_df = clean_nulls_and_empty(mock_df)

        # Should return original DataFrame
        assert result_df is mock_df
        mock_logger.error.assert_called_once()

    @patch("spark_simplicity.utils._utils_logger")
    def test_successful_cleaning_logging(
        self, mock_logger: Mock, mock_spark_session: Any
    ) -> None:
        """Test successful cleaning operation logging."""
        mock_df = Mock(spec=DataFrame)
        mock_df.dtypes = [("name", "string")]
        mock_df.columns = ["name"]

        mock_cleaned_df = Mock(spec=DataFrame)
        mock_df.fillna.return_value = mock_cleaned_df
        mock_cleaned_df.replace.return_value = mock_cleaned_df

        clean_nulls_and_empty(mock_df)

        # Verify info logging was called
        mock_logger.info.assert_called()

    def test_custom_null_values(self, mock_spark_session: Any) -> None:
        """Test cleaning with custom null values list."""
        mock_df = Mock(spec=DataFrame)
        mock_df.dtypes = [("name", "string")]
        mock_df.columns = ["name"]

        mock_cleaned_df = Mock(spec=DataFrame)
        mock_df.fillna.return_value = mock_cleaned_df
        mock_cleaned_df.replace.return_value = mock_cleaned_df

        # This should cover line 62: combining default and custom null values
        result_df = clean_nulls_and_empty(
            mock_df,
            replacement_value="REPLACED",
            null_values=["CUSTOM_NULL", "MISSING"],
        )

        # Verify the function executed the combining logic
        mock_df.fillna.assert_called_once()
        mock_cleaned_df.replace.assert_called_once()
        assert result_df is mock_cleaned_df


class TestAnalyzeDataQuality:
    """
    Comprehensive test suite for analyze_data_quality function with 100% coverage.
    """

    @patch("spark_simplicity.utils.col")
    def test_basic_quality_analysis(
        self, mock_col: Any, mock_spark_session: Any
    ) -> None:
        """Test basic data quality analysis functionality."""
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 5
        mock_df.columns = ["id", "name", "email"]

        # Mock col function
        mock_column_obj = Mock()
        mock_column_obj.isNotNull.return_value = Mock()
        mock_col.return_value = mock_column_obj

        def mock_filter_side_effect(_: Any) -> Mock:
            """Mock side effect for DataFrame filter operations."""
            mock_filtered = Mock()
            mock_filtered.count.return_value = 4  # 4 non-null out of 5
            return mock_filtered

        mock_df.filter.side_effect = mock_filter_side_effect

        # Mock select operations for uniqueness
        def mock_select_side_effect(_: Any) -> Mock:
            """Mock side effect for DataFrame select operations."""
            mock_selected = Mock()
            mock_distinct = Mock()
            mock_distinct.count.return_value = 4  # 4 unique out of 5
            mock_selected.distinct.return_value = mock_distinct
            return mock_selected

        mock_df.select.side_effect = mock_select_side_effect

        result = analyze_data_quality(mock_df)

        # Validate result structure
        assert isinstance(result, dict)
        assert "row_count" in result
        assert "column_count" in result
        assert "completeness" in result
        assert "uniqueness" in result
        assert "overall_score" in result

        assert result["row_count"] == 5
        assert result["column_count"] == 3

    @patch("spark_simplicity.utils.col")
    def test_empty_dataframe_analysis(
        self, mock_col: Any, mock_spark_session: Any
    ) -> None:
        """Test quality analysis on empty DataFrame."""
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 0
        mock_df.columns = ["test_col"]

        # Mock col function
        mock_column_obj = Mock()
        mock_column_obj.isNotNull.return_value = Mock()
        mock_col.return_value = mock_column_obj

        # Mock empty filter result
        def mock_filter_side_effect(_: Any) -> Mock:
            """Mock side effect for DataFrame filter operations."""
            mock_filtered = Mock()
            mock_filtered.count.return_value = 0
            return mock_filtered

        mock_df.filter.side_effect = mock_filter_side_effect

        # Mock empty select result
        def mock_select_side_effect(_: Any) -> Mock:
            """Mock side effect for DataFrame select operations."""
            mock_selected = Mock()
            mock_distinct = Mock()
            mock_distinct.count.return_value = 0
            mock_selected.distinct.return_value = mock_distinct
            return mock_selected

        mock_df.select.side_effect = mock_select_side_effect

        result = analyze_data_quality(mock_df)

        assert result["row_count"] == 0
        assert result["column_count"] == 1
        assert result["completeness"]["test_col"] == 0
        assert result["uniqueness"]["test_col"] == 0

    def test_exception_handling_returns_error_dict(
        self, mock_spark_session: Any
    ) -> None:
        """Test exception handling returns error dictionary."""
        mock_df = Mock(spec=DataFrame)
        mock_df.count.side_effect = Exception("Test error")

        result = analyze_data_quality(mock_df)

        assert "error" in result
        assert "Failed to analyze data quality" in result["error"]
        assert "Test error" in result["error"]

    @patch("spark_simplicity.utils.col")
    def test_sampling_functionality(
        self, mock_col: Any, mock_spark_session: Any
    ) -> None:
        """Test DataFrame sampling for large datasets."""
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 1000

        # Mock col function
        mock_column_obj = Mock()
        mock_column_obj.isNotNull.return_value = Mock()
        mock_col.return_value = mock_column_obj

        # Mock sampled DataFrame
        mock_sampled_df = Mock()
        mock_sampled_df.count.return_value = 100
        mock_sampled_df.columns = ["id"]
        mock_df.sample.return_value = mock_sampled_df

        # Mock filter and select operations on sampled df
        mock_filtered_df = Mock()
        mock_filtered_df.count.return_value = 100
        mock_sampled_df.filter.return_value = mock_filtered_df

        mock_selected_df = Mock()
        mock_distinct_df = Mock()
        mock_distinct_df.count.return_value = 100
        mock_selected_df.distinct.return_value = mock_distinct_df
        mock_sampled_df.select.return_value = mock_selected_df

        result = analyze_data_quality(mock_df, sample_size=100)

        # Should use sampled DataFrame
        mock_df.sample.assert_called_once()
        assert result["column_count"] == 1


class TestProfileDataframePerformance:
    """
    Comprehensive test suite for profile_dataframe_performance function with 100%
    coverage.
    """

    def test_basic_performance_profiling(self, mock_spark_session: Any) -> None:
        """Test basic performance profiling functionality."""
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 100

        # Mock RDD for partition count
        mock_rdd = Mock()
        mock_rdd.getNumPartitions.return_value = 4
        mock_df.rdd = mock_rdd

        result = profile_dataframe_performance(mock_df, "test_operation")

        # Validate result structure
        assert isinstance(result, dict)
        required_keys = [
            "operation",
            "row_count",
            "partition_count",
            "duration_seconds",
            "rows_per_second",
            "timestamp",
        ]
        for key in required_keys:
            assert key in result

        assert result["operation"] == "test_operation"
        assert result["row_count"] == 100
        assert result["partition_count"] == 4
        assert isinstance(result["duration_seconds"], (int, float))
        assert isinstance(result["rows_per_second"], (int, float))

    def test_default_operation_name(self, mock_spark_session: Any) -> None:
        """Test default operation name when not specified."""
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 10

        mock_rdd = Mock()
        mock_rdd.getNumPartitions.return_value = 1
        mock_df.rdd = mock_rdd

        result = profile_dataframe_performance(mock_df)

        assert result["operation"] == "operation"

    def test_exception_handling_returns_error_dict(
        self, mock_spark_session: Any
    ) -> None:
        """Test exception handling returns error dictionary."""
        mock_df = Mock(spec=DataFrame)
        mock_df.count.side_effect = Exception("Profile test error")

        result = profile_dataframe_performance(mock_df, "error_test")

        assert "error" in result
        assert "Failed to profile performance" in result["error"]
        assert "Profile test error" in result["error"]

    def test_zero_duration_handling(self, mock_spark_session: Any) -> None:
        """Test handling of extremely fast operations with near-zero duration."""
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 1

        mock_rdd = Mock()
        mock_rdd.getNumPartitions.return_value = 1
        mock_df.rdd = mock_rdd

        result = profile_dataframe_performance(mock_df, "zero_duration_test")

        assert isinstance(result, dict)
        assert "operation" in result
        assert "duration_seconds" in result
        assert "rows_per_second" in result
        assert result["operation"] == "zero_duration_test"
        assert isinstance(result["duration_seconds"], (int, float))
        assert isinstance(result["rows_per_second"], (int, float))

    @patch("spark_simplicity.utils._utils_logger")
    def test_successful_profiling_logging(
        self, mock_logger: Mock, mock_spark_session: Any
    ) -> None:
        """Test successful profiling operation logging."""
        mock_df = Mock(spec=DataFrame)
        mock_df.count.return_value = 50

        mock_rdd = Mock()
        mock_rdd.getNumPartitions.return_value = 2
        mock_df.rdd = mock_rdd

        profile_dataframe_performance(mock_df, "logged_operation")

        # Verify logging was called for successful profiling
        assert mock_logger.info.call_count >= 4


class TestCompareDataframes:
    """
    Comprehensive test suite for compare_dataframes function with 100% coverage.
    """

    def test_basic_dataframe_comparison(self, mock_spark_session: Any) -> None:
        """Test basic DataFrame comparison functionality."""
        mock_df1 = Mock(spec=DataFrame)
        mock_df2 = Mock(spec=DataFrame)

        # Mock basic operations
        mock_df1.columns = ["id", "name"]
        mock_df2.columns = ["id", "name"]
        mock_df1.count.return_value = 4
        mock_df2.count.return_value = 4

        # Mock join operations
        mock_left_anti_df1 = Mock()
        mock_left_anti_df1.count.return_value = 1  # 1 row only in df1
        mock_left_anti_df2 = Mock()
        mock_left_anti_df2.count.return_value = 1  # 1 row only in df2
        mock_inner_df = Mock()
        mock_inner_df.count.return_value = 3  # 3 common rows

        mock_df1.join.side_effect = [mock_left_anti_df1, mock_inner_df]
        mock_df2.join.return_value = mock_left_anti_df2

        result = compare_dataframes(mock_df1, mock_df2, ["id"])

        # Validate result structure
        assert isinstance(result, dict)
        required_keys = [
            "df1_row_count",
            "df2_row_count",
            "only_in_df1",
            "only_in_df2",
            "common_rows",
            "key_columns",
            "identical",
        ]
        for key in required_keys:
            assert key in result

        assert result["df1_row_count"] == 4
        assert result["df2_row_count"] == 4
        assert result["only_in_df1"] == 1
        assert result["only_in_df2"] == 1
        assert result["common_rows"] == 3
        assert result["key_columns"] == ["id"]
        assert result["identical"] is False

    def test_identical_dataframes(self, mock_spark_session: Any) -> None:
        """Test comparison of identical DataFrames."""
        mock_df1 = Mock(spec=DataFrame)
        mock_df2 = Mock(spec=DataFrame)

        mock_df1.columns = ["id"]
        mock_df2.columns = ["id"]
        mock_df1.count.return_value = 2
        mock_df2.count.return_value = 2

        # Mock join operations for identical DataFrames
        mock_left_anti_df1 = Mock()
        mock_left_anti_df1.count.return_value = 0  # No unique rows
        mock_left_anti_df2 = Mock()
        mock_left_anti_df2.count.return_value = 0  # No unique rows
        mock_inner_df = Mock()
        mock_inner_df.count.return_value = 2  # All rows common

        mock_df1.join.side_effect = [mock_left_anti_df1, mock_inner_df]
        mock_df2.join.return_value = mock_left_anti_df2

        result = compare_dataframes(mock_df1, mock_df2, ["id"])

        assert result["only_in_df1"] == 0
        assert result["only_in_df2"] == 0
        assert result["common_rows"] == 2
        assert result["identical"] is True

    def test_missing_key_columns_error(self, mock_spark_session: Any) -> None:
        """Test error handling for missing key columns."""
        mock_df1 = Mock(spec=DataFrame)
        mock_df2 = Mock(spec=DataFrame)

        mock_df1.columns = ["id", "name"]
        mock_df2.columns = ["id", "name"]

        result = compare_dataframes(mock_df1, mock_df2, ["nonexistent_column"])

        # Function should return error dictionary
        assert "error" in result
        assert "Failed to compare DataFrames" in result["error"]

    def test_missing_key_columns_in_df2_error(self, mock_spark_session: Any) -> None:
        """Test error handling for missing key columns in df2."""
        mock_df1 = Mock(spec=DataFrame)
        mock_df2 = Mock(spec=DataFrame)

        mock_df1.columns = ["id", "name", "value"]
        mock_df2.columns = ["id", "name"]  # Missing 'value' column

        result = compare_dataframes(mock_df1, mock_df2, ["id", "value"])

        # Function should return error dictionary - covers line 254
        assert "error" in result
        assert "Failed to compare DataFrames" in result["error"]

    def test_exception_handling_returns_error_dict(
        self, mock_spark_session: Any
    ) -> None:
        """Test exception handling returns error dictionary."""
        mock_df1 = Mock(spec=DataFrame)
        mock_df2 = Mock(spec=DataFrame)

        mock_df1.columns = ["id"]
        mock_df2.columns = ["id"]
        mock_df1.count.side_effect = Exception("Compare test error")

        result = compare_dataframes(mock_df1, mock_df2, ["id"])

        assert "error" in result
        assert "Failed to compare DataFrames" in result["error"]
        assert "Compare test error" in result["error"]

    @patch("spark_simplicity.utils._utils_logger")
    def test_successful_comparison_logging(
        self, mock_logger: Mock, mock_spark_session: Any
    ) -> None:
        """Test successful comparison operation logging."""
        mock_df1 = Mock(spec=DataFrame)
        mock_df2 = Mock(spec=DataFrame)

        mock_df1.columns = ["id"]
        mock_df2.columns = ["id"]
        mock_df1.count.return_value = 2
        mock_df2.count.return_value = 2

        # Mock join operations
        mock_left_anti_df1 = Mock()
        mock_left_anti_df1.count.return_value = 0
        mock_left_anti_df2 = Mock()
        mock_left_anti_df2.count.return_value = 0
        mock_inner_df = Mock()
        mock_inner_df.count.return_value = 2

        mock_df1.join.side_effect = [mock_left_anti_df1, mock_inner_df]
        mock_df2.join.return_value = mock_left_anti_df2

        compare_dataframes(mock_df1, mock_df2, ["id"])

        # Verify logging was called for successful comparison
        assert mock_logger.info.call_count >= 6


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=spark_simplicity.utils",
            "--cov-report=term-missing",
            "--cov-branch",
        ]
    )
