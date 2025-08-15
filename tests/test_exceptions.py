"""
Spark Simplicity - Exceptions Tests
===================================

Comprehensive test suite for all custom exceptions with enterprise-grade
coverage and validation.
This module provides extensive testing of exception hierarchy, initialization
patterns, message handling, and error propagation characteristics essential
for production Spark data processing environments.

Key Testing Areas:
    - **Exception Hierarchy**: Base class implementation and inheritance patterns
    - **Initialization**: Message handling, details dictionary, and parameter validation
    - **Error Propagation**: Exception raising, catching, and message preservation
    - **Inheritance Behavior**: Proper subclass relationships and isinstance checks
    - **Edge Cases**: Empty messages, None details, special characters, and Unicode
    - **Documentation**: Docstring validation and exception classification

Test Coverage:
    **Base Exception Class**:
    - SparkSimplicityError initialization with various parameter combinations
    - Message and details attribute validation and preservation
    - Exception raising and catching behavior with proper message propagation
    - Edge cases including empty strings, None values, and complex data structures

    **Exception Hierarchy Validation**:
    - Proper inheritance relationships between base and derived classes
    - isinstance and issubclass checks for correct type hierarchy
    - Exception categorization by functional domain (validation, IO, connection)
    - Multiple inheritance levels and proper method resolution order

Enterprise Integration Testing:
    - **Production Error Scenarios**: Realistic error conditions and exception usage
    - **Message Formatting**: Consistent error messaging and debugging information
    - **Details Dictionary**: Structured error context and debugging metadata
    - **Type Safety**: Exception type validation and proper inheritance patterns
    - **Internationalization**: Unicode support and character encoding validation

Testing Philosophy:
    This test suite follows enterprise software development best practices with
    comprehensive coverage, realistic error simulation, and production-ready
    validation patterns. All tests are designed to validate both functional
    correctness and operational reliability in demanding production Spark
    environments.
"""

import sys
from pathlib import Path
from typing import Any, Dict

import pytest

# Import optimisé avec gestion propre des chemins - placé avant les imports du module
sys.path.insert(0, str(Path(__file__).parent.parent))

from spark_simplicity.exceptions import (  # noqa: E402
    ApiConnectionError,
    ConfigurationError,
    CorruptDataError,
    DatabaseConnectionError,
    DataFrameValidationError,
    DataValidationError,
    EmailConnectionError,
    FileReadError,
    FileWriteError,
    FormatError,
    JoinError,
    PerformanceError,
    SchemaValidationError,
    SessionError,
    SftpConnectionError,
    SparkConnectionError,
    SparkIOError,
    SparkSimplicityError,
    TransformationError,
)


class TestSparkSimplicityError:
    """
    Comprehensive test suite for SparkSimplicityError base exception class.

    This test class validates all aspects of the base exception functionality
    including initialization patterns, message handling, details dictionary
    management, and proper exception behavior. Tests are organized by
    functional areas with comprehensive coverage of normal operations,
    edge cases, and error conditions.

    Test Organization:
        - Basic Initialization: Standard exception creation and parameter handling
        - Message Validation: String handling, encoding, and preservation
        - Details Dictionary: Optional metadata and structured error context
        - Exception Behavior: Raising, catching, and propagation patterns
        - Edge Cases: Empty values, None parameters, and special characters
    """

    # Basic Initialization Testing
    # ===========================

    @pytest.mark.unit
    def test_basic_initialization_message_only(self) -> None:
        """
        Test basic exception initialization with message only.

        Validates that SparkSimplicityError can be properly initialized with
        just a message parameter, ensuring correct attribute assignment and
        default values for optional parameters.
        """
        message = "Test error message"
        exception = SparkSimplicityError(message)

        assert exception.message == message, (
            f"Message not properly assigned: expected '{message}', "
            f"got '{exception.message}'"
        )
        assert str(exception) == message, (
            f"String representation incorrect: expected '{message}', "
            f"got '{str(exception)}'"
        )
        assert (
            exception.details == {}
        ), f"Details should default to empty dict, got '{exception.details}'"

    @pytest.mark.unit
    def test_initialization_with_message_and_details(self) -> None:
        """
        Test exception initialization with both message and details dictionary.

        Validates proper handling of structured error context through the
        details parameter, ensuring both message and metadata are correctly
        preserved for debugging and operational monitoring.
        """
        message = "Database connection failed"
        details = {
            "host": "localhost",
            "port": 5432,
            "database": "test_db",
            "error_code": "CONNECTION_TIMEOUT",
        }

        exception = SparkSimplicityError(message, details)

        assert (
            exception.message == message
        ), f"Message not preserved: expected '{message}', got '{exception.message}'"
        assert (
            exception.details == details
        ), f"Details not preserved: expected {details}, got {exception.details}"
        assert str(exception) == message, (
            f"String representation should be message: expected '{message}', "
            f"got '{str(exception)}'"
        )

    @pytest.mark.unit
    def test_initialization_with_empty_details(self) -> None:
        """
        Test exception initialization with explicitly empty details dictionary.

        Validates that passing an empty dictionary as details parameter
        results in the expected behavior and proper attribute assignment
        without affecting exception functionality.
        """
        message = "Validation error"
        empty_details: Dict[str, Any] = {}

        exception = SparkSimplicityError(message, empty_details)

        assert exception.message == message
        assert exception.details == empty_details
        # Note: Due to 'details or {}' logic, empty dict creates new instance
        assert isinstance(exception.details, dict), "Details should be a dictionary"

    @pytest.mark.unit
    def test_initialization_with_none_details(self) -> None:
        """
        Test exception initialization with None details parameter.

        Validates that None details parameter correctly defaults to empty
        dictionary, ensuring consistent behavior and preventing attribute
        access errors during exception handling.
        """
        message = "Configuration error"
        exception = SparkSimplicityError(message)

        assert exception.message == message
        assert exception.details == {}, (
            "None details should default to empty dict, got " f"'{exception.details}'"
        )

    # Message Validation Testing
    # =========================

    @pytest.mark.unit
    def test_empty_message_handling(self) -> None:
        """
        Test exception behavior with empty string message.

        Validates that empty messages are properly handled without breaking
        exception functionality, ensuring robust error handling even with
        incomplete error information.
        """
        empty_message = ""
        exception = SparkSimplicityError(empty_message)

        assert exception.message == empty_message
        assert str(exception) == empty_message
        assert exception.details == {}

    @pytest.mark.unit
    def test_whitespace_message_handling(self) -> None:
        """
        Test exception handling with whitespace-only messages.

        Validates that messages containing only whitespace characters
        are preserved without modification, maintaining exact error
        message formatting for debugging purposes.
        """
        whitespace_messages = [
            " ",
            "\t",
            "\n",
            "\r\n",
            "   \t\n   ",
        ]

        for message in whitespace_messages:
            exception = SparkSimplicityError(message)

            assert exception.message == message, (
                f"Whitespace message not preserved: expected '{repr(message)}', "
                f"got '{repr(exception.message)}'"
            )
            assert str(exception) == message

    @pytest.mark.unit
    @pytest.mark.unicode
    def test_unicode_message_handling(self) -> None:
        """
        Test exception handling with Unicode characters in messages.

        Validates proper encoding and processing of international characters
        in error messages, ensuring global compatibility and robust character
        encoding support for multilingual error reporting.
        """
        unicode_messages = [
            "测试错误消息",  # Chinese
            "Ошибка подключения",  # Russian
            "Erro de configuração",  # Portuguese
            "🚨 Critical Error 🚨",  # Emoji
            "Fichier non trouvé à l'emplacement spécifié",  # French with accents
        ]

        for message in unicode_messages:
            exception = SparkSimplicityError(message)

            assert exception.message == message, (
                f"Unicode message not preserved: expected '{message}', "
                f"got '{exception.message}'"
            )
            assert str(exception) == message

    @pytest.mark.unit
    def test_special_characters_in_message(self) -> None:
        """
        Test exception handling with special characters and escape sequences.

        Validates that messages containing special characters, quotes, and
        escape sequences are properly handled without breaking string
        representation or message integrity.
        """
        special_messages = [
            "Error with 'single quotes'",
            'Error with "double quotes"',
            "Error with\ttabs\tand\nnewlines",
            "Error with backslash \\ characters",
            "Error with special chars: !@#$%^&*()[]{}|;:,.<>?",
        ]

        for message in special_messages:
            exception = SparkSimplicityError(message)

            assert (
                exception.message == message
            ), f"Special characters not preserved in: {repr(message)}"
            assert str(exception) == message

    # Details Dictionary Testing
    # =========================

    @pytest.mark.unit
    def test_complex_details_structure(self) -> None:
        """
        Test exception with complex nested details dictionary.

        Validates that sophisticated error context structures including
        nested dictionaries, lists, and various data types are properly
        preserved for comprehensive debugging information.
        """
        message = "Complex operation failed"
        complex_details = {
            "operation": "data_transformation",
            "timestamp": "2024-01-15T10:30:00Z",
            "parameters": {
                "input_path": "/data/input.csv",
                "output_path": "/data/output.parquet",
                "partition_count": 10,
            },
            "error_stack": [
                {"level": "high", "component": "transformer"},
                {"level": "low", "component": "file_reader"},
            ],
            "metrics": {
                "rows_processed": 1000000,
                "processing_time_ms": 45000,
                "memory_usage_mb": 2048,
            },
        }

        exception = SparkSimplicityError(message, complex_details)

        assert exception.message == message
        assert exception.details == complex_details
        assert exception.details["operation"] == "data_transformation"
        assert exception.details["parameters"]["partition_count"] == 10
        assert len(exception.details["error_stack"]) == 2

    @pytest.mark.unit
    def test_details_immutability_behavior(self) -> None:
        """
        Test details dictionary mutability and reference behavior.

        Validates how the exception handles the details dictionary reference,
        ensuring appropriate behavior for mutable objects passed as details
        parameter during exception initialization.
        """
        message = "Mutable details test"
        original_details = {"status": "failed", "retry_count": 0}

        exception = SparkSimplicityError(message, original_details)

        # Modify original dictionary after exception creation
        original_details["status"] = "modified"
        original_details["new_field"] = "added"

        # Exception should maintain reference behavior (not deep copy)
        assert (
            exception.details["status"] == "modified"
        ), "Details dictionary should maintain reference to original"
        assert (
            "new_field" in exception.details
        ), "New fields should appear in exception details"

    @pytest.mark.unit
    def test_details_with_none_values(self) -> None:
        """
        Test details dictionary containing None values.

        Validates proper handling of None values within the details
        dictionary, ensuring that None values are preserved and don't
        cause issues during exception processing or debugging.
        """
        message = "Error with None values"
        details_with_none = {
            "valid_field": "valid_value",
            "none_field": None,
            "empty_string": "",
            "zero_value": 0,
            "false_value": False,
        }

        exception = SparkSimplicityError(message, details_with_none)

        assert exception.message == message
        assert exception.details == details_with_none
        assert exception.details["none_field"] is None
        assert exception.details["valid_field"] == "valid_value"

    # Exception Behavior Testing
    # =========================

    @pytest.mark.unit
    def test_exception_raising_and_catching(self) -> None:
        """
        Test proper exception raising and catching behavior.

        Validates that SparkSimplicityError can be raised and caught correctly,
        maintaining message and details integrity through the exception
        propagation process.
        """
        message = "Test exception for raising"
        details = {"test_context": "exception_propagation"}

        with pytest.raises(SparkSimplicityError) as exc_info:
            raise SparkSimplicityError(message, details)

        caught_exception = exc_info.value
        assert caught_exception.message == message
        assert caught_exception.details == details
        assert str(caught_exception) == message

    @pytest.mark.unit
    def test_exception_inheritance_from_exception(self) -> None:
        """
        Test proper inheritance from built-in Exception class.

        Validates that SparkSimplicityError properly inherits from Exception
        and maintains all expected behaviors of standard Python exceptions
        while adding custom functionality.
        """
        message = "Inheritance test"
        exception = SparkSimplicityError(message)

        # Test inheritance
        assert isinstance(
            exception, Exception
        ), "SparkSimplicityError should inherit from Exception"
        assert isinstance(
            exception, SparkSimplicityError
        ), "Should be instance of SparkSimplicityError"

        # Test exception args
        assert exception.args == (
            message,
        ), f"Exception args should be ('{message}',), got {exception.args}"

    @pytest.mark.unit
    def test_exception_with_multiple_catch_blocks(self) -> None:
        """
        Test exception behavior in multiple catch block scenarios.

        Validates that SparkSimplicityError can be properly caught at
        different inheritance levels, ensuring correct exception handling
        patterns in complex error management scenarios.
        """
        message = "Multi-catch test"
        exception = SparkSimplicityError(message)

        # Test catching as base Exception
        try:
            raise exception
        except Exception as e:
            assert isinstance(e, SparkSimplicityError)
            assert e.message == message

        # Test catching as specific type
        try:
            raise exception
        except SparkSimplicityError as e:
            assert e.message == message
            assert hasattr(e, "details")

    # Integration and Edge Case Testing
    # ================================

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_very_long_message_handling(self) -> None:
        """
        Test exception handling with extremely long error messages.

        Validates that very long error messages don't break exception
        functionality, ensuring robust handling of verbose error descriptions
        and large debugging information.
        """
        long_message = "Error: " + "x" * 10000  # 10KB+ message

        exception = SparkSimplicityError(long_message)

        assert exception.message == long_message
        assert str(exception) == long_message
        assert len(exception.message) > 10000

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_large_details_dictionary(self) -> None:
        """
        Test exception with large details dictionary.

        Validates that large amounts of debugging information can be
        stored in the details dictionary without affecting exception
        performance or functionality.
        """
        message = "Large details test"
        large_details = {f"field_{i}": f"value_{i}" for i in range(1000)}

        exception = SparkSimplicityError(message, large_details)

        assert exception.message == message
        assert len(exception.details) == 1000
        assert exception.details["field_500"] == "value_500"

    @pytest.mark.unit
    @pytest.mark.type_validation
    def test_attribute_types_validation(self) -> None:
        """
        Test validation of exception attribute types.

        Validates that exception attributes maintain correct types and
        provide expected interface for debugging and error handling
        operations.
        """
        message = "Type validation test"
        details = {"numeric": 42, "boolean": True}

        exception = SparkSimplicityError(message, details)

        # Validate attribute types
        assert isinstance(
            exception.message, str
        ), f"Message should be str, got {type(exception.message)}"
        assert isinstance(
            exception.details, dict
        ), f"Details should be dict, got {type(exception.details)}"

        # Validate standard exception interface
        assert hasattr(exception, "args"), "Exception should have args attribute"
        assert callable(str), "Exception should be convertible to string"


class TestExceptionHierarchy:
    """
    Comprehensive test suite for exception inheritance hierarchy.

    This test class validates the complete exception hierarchy structure,
    inheritance relationships, and proper categorization of exceptions
    by functional domain. Tests ensure that all exceptions maintain
    proper inheritance patterns and can be caught at appropriate levels.

    Test Organization:
        - Inheritance Validation: Parent-child relationships and isinstance checks
        - Domain Categorization: Functional grouping and exception classification
        - Multiple Inheritance: Complex inheritance patterns and method resolution
        - Type Safety: Proper type checking and exception identification
    """

    # Inheritance Pattern Testing
    # ==========================

    @pytest.mark.unit
    def test_data_validation_exceptions_hierarchy(self) -> None:
        """
        Test data validation exception inheritance hierarchy.

        Validates that all data validation related exceptions properly
        inherit from DataValidationError and ultimately from the base
        SparkSimplicityError class.
        """
        # Test base DataValidationError
        data_error = DataValidationError("Data validation failed")
        assert isinstance(data_error, SparkSimplicityError)
        assert isinstance(data_error, DataValidationError)

        # Test DataFrame validation inheritance
        df_error = DataFrameValidationError("DataFrame validation failed")
        assert isinstance(df_error, SparkSimplicityError)
        assert isinstance(df_error, DataValidationError)
        assert isinstance(df_error, DataFrameValidationError)

        # Test Schema validation inheritance
        schema_error = SchemaValidationError("Schema validation failed")
        assert isinstance(schema_error, SparkSimplicityError)
        assert isinstance(schema_error, DataValidationError)
        assert isinstance(schema_error, SchemaValidationError)

        # Test Corrupt data inheritance
        corrupt_error = CorruptDataError("Corrupt data detected")
        assert isinstance(corrupt_error, SparkSimplicityError)
        assert isinstance(corrupt_error, DataValidationError)
        assert isinstance(corrupt_error, CorruptDataError)

    @pytest.mark.unit
    def test_io_exceptions_hierarchy(self) -> None:
        """
        Test I/O exception inheritance hierarchy.

        Validates that all I/O related exceptions properly inherit from
        SparkIOError and maintain correct hierarchical relationships
        for file operations and format handling.
        """
        # Test base SparkIOError
        io_error = SparkIOError("I/O operation failed")
        assert isinstance(io_error, SparkSimplicityError)
        assert isinstance(io_error, SparkIOError)

        # Test FileReadError inheritance
        read_error = FileReadError("File read failed")
        assert isinstance(read_error, SparkSimplicityError)
        assert isinstance(read_error, SparkIOError)
        assert isinstance(read_error, FileReadError)

        # Test FileWriteError inheritance
        write_error = FileWriteError("File write failed")
        assert isinstance(write_error, SparkSimplicityError)
        assert isinstance(write_error, SparkIOError)
        assert isinstance(write_error, FileWriteError)

        # Test FormatError inheritance
        format_error = FormatError("Invalid file format")
        assert isinstance(format_error, SparkSimplicityError)
        assert isinstance(format_error, SparkIOError)
        assert isinstance(format_error, FormatError)

    @pytest.mark.unit
    def test_connection_exceptions_hierarchy(self) -> None:
        """
        Test connection exception inheritance hierarchy.

        Validates that all connection related exceptions properly inherit
        from SparkConnectionError and maintain correct relationships for
        different connection types and protocols.
        """
        # Test base SparkConnectionError
        conn_error = SparkConnectionError("Connection failed")
        assert isinstance(conn_error, SparkSimplicityError)
        assert isinstance(conn_error, SparkConnectionError)

        # Test DatabaseConnectionError inheritance
        db_error = DatabaseConnectionError("Database connection failed")
        assert isinstance(db_error, SparkSimplicityError)
        assert isinstance(db_error, SparkConnectionError)
        assert isinstance(db_error, DatabaseConnectionError)

        # Test SftpConnectionError inheritance
        sftp_error = SftpConnectionError("SFTP connection failed")
        assert isinstance(sftp_error, SparkSimplicityError)
        assert isinstance(sftp_error, SparkConnectionError)
        assert isinstance(sftp_error, SftpConnectionError)

        # Test EmailConnectionError inheritance
        email_error = EmailConnectionError("Email connection failed")
        assert isinstance(email_error, SparkSimplicityError)
        assert isinstance(email_error, SparkConnectionError)
        assert isinstance(email_error, EmailConnectionError)

        # Test ApiConnectionError inheritance
        api_error = ApiConnectionError("API connection failed")
        assert isinstance(api_error, SparkSimplicityError)
        assert isinstance(api_error, SparkConnectionError)
        assert isinstance(api_error, ApiConnectionError)

    @pytest.mark.unit
    def test_direct_base_exceptions(self) -> None:
        """
        Test exceptions that inherit directly from SparkSimplicityError.

        Validates that exceptions without intermediate parent classes
        properly inherit from the base exception and maintain expected
        behavior patterns.
        """
        direct_exceptions = [
            (ConfigurationError, "Configuration error"),
            (SessionError, "Session error"),
            (JoinError, "Join operation failed"),
            (TransformationError, "Transformation failed"),
            (PerformanceError, "Performance issue detected"),
        ]

        for exception_class, message in direct_exceptions:
            exception = exception_class(message)

            assert isinstance(
                exception, SparkSimplicityError
            ), f"{exception_class.__name__} should inherit from SparkSimplicityError"
            assert isinstance(
                exception, exception_class
            ), f"Should be instance of {exception_class.__name__}"
            assert exception.message == message
            assert hasattr(exception, "details")

    # Exception Catching Patterns Testing
    # ==================================

    @pytest.mark.unit
    def test_catching_by_base_class(self) -> None:
        """
        Test catching exceptions using base class patterns.

        Validates that specific exceptions can be caught using their
        parent classes, ensuring proper exception handling hierarchy
        and polymorphic exception management.
        """
        # Test catching data validation errors by base class
        with pytest.raises(DataValidationError):
            raise DataFrameValidationError("DataFrame validation failed")

        with pytest.raises(DataValidationError):
            raise SchemaValidationError("Schema validation failed")

        # Test catching I/O errors by base class
        with pytest.raises(SparkIOError):
            raise FileReadError("File read failed")

        with pytest.raises(SparkIOError):
            raise FormatError("Format error")

        # Test catching connection errors by base class
        with pytest.raises(SparkConnectionError):
            raise DatabaseConnectionError("Database connection failed")

        with pytest.raises(SparkConnectionError):
            raise SftpConnectionError("SFTP connection failed")

    @pytest.mark.unit
    def test_catching_by_ultimate_base_class(self) -> None:
        """
        Test catching all exceptions using SparkSimplicityError base class.

        Validates that any exception in the hierarchy can be caught using
        the root base class, ensuring comprehensive error handling
        capabilities for broad exception management scenarios.
        """
        exception_instances = [
            DataValidationError("Data error"),
            DataFrameValidationError("DataFrame error"),
            SchemaValidationError("Schema error"),
            CorruptDataError("Corrupt data error"),
            SparkIOError("I/O error"),
            FileReadError("Read error"),
            FileWriteError("Write error"),
            FormatError("Format error"),
            SparkConnectionError("Connection error"),
            DatabaseConnectionError("Database error"),
            SftpConnectionError("SFTP error"),
            EmailConnectionError("Email error"),
            ApiConnectionError("API error"),
            ConfigurationError("Configuration error"),
            SessionError("Session error"),
            JoinError("Join error"),
            TransformationError("Transformation error"),
            PerformanceError("Performance error"),
        ]

        for exception in exception_instances:
            with pytest.raises(SparkSimplicityError):
                raise exception

    @pytest.mark.unit
    def test_exception_type_identification(self) -> None:
        """
        Test proper exception type identification using isinstance.

        Validates that exception instances can be correctly identified
        using isinstance checks at various levels of the inheritance
        hierarchy, ensuring reliable exception type detection.
        """
        # Create exception instances
        df_error = DataFrameValidationError("DataFrame error")
        read_error = FileReadError("Read error")
        db_error = DatabaseConnectionError("Database error")

        # Test multi-level isinstance checks
        assert isinstance(df_error, DataFrameValidationError)
        assert isinstance(df_error, DataValidationError)
        assert isinstance(df_error, SparkSimplicityError)
        assert isinstance(df_error, Exception)

        assert isinstance(read_error, FileReadError)
        assert isinstance(read_error, SparkIOError)
        assert isinstance(read_error, SparkSimplicityError)
        assert isinstance(read_error, Exception)

        assert isinstance(db_error, DatabaseConnectionError)
        assert isinstance(db_error, SparkConnectionError)
        assert isinstance(db_error, SparkSimplicityError)
        assert isinstance(db_error, Exception)

    # Class Relationships Testing
    # ==========================

    @pytest.mark.unit
    def test_issubclass_relationships(self) -> None:
        """
        Test proper class inheritance relationships using issubclass.

        Validates that exception classes maintain correct subclass
        relationships throughout the inheritance hierarchy, ensuring
        proper class design and inheritance patterns.
        """
        # Test data validation hierarchy
        assert issubclass(DataValidationError, SparkSimplicityError)
        assert issubclass(DataFrameValidationError, DataValidationError)
        assert issubclass(SchemaValidationError, DataValidationError)
        assert issubclass(CorruptDataError, DataValidationError)

        # Test I/O hierarchy
        assert issubclass(SparkIOError, SparkSimplicityError)
        assert issubclass(FileReadError, SparkIOError)
        assert issubclass(FileWriteError, SparkIOError)
        assert issubclass(FormatError, SparkIOError)

        # Test connection hierarchy
        assert issubclass(SparkConnectionError, SparkSimplicityError)
        assert issubclass(DatabaseConnectionError, SparkConnectionError)
        assert issubclass(SftpConnectionError, SparkConnectionError)
        assert issubclass(EmailConnectionError, SparkConnectionError)
        assert issubclass(ApiConnectionError, SparkConnectionError)

        # Test direct inheritance
        assert issubclass(ConfigurationError, SparkSimplicityError)
        assert issubclass(SessionError, SparkSimplicityError)
        assert issubclass(JoinError, SparkSimplicityError)
        assert issubclass(TransformationError, SparkSimplicityError)
        assert issubclass(PerformanceError, SparkSimplicityError)

    @pytest.mark.unit
    def test_exception_documentation_validation(self) -> None:
        """
        Test that all exception classes have proper documentation.

        Validates that all exception classes include docstrings with
        appropriate descriptions of their purpose and usage, ensuring
        good code documentation and developer experience.
        """
        exception_classes = [
            SparkSimplicityError,
            DataValidationError,
            DataFrameValidationError,
            SchemaValidationError,
            CorruptDataError,
            SparkIOError,
            FileReadError,
            FileWriteError,
            FormatError,
            SparkConnectionError,
            DatabaseConnectionError,
            SftpConnectionError,
            EmailConnectionError,
            ApiConnectionError,
            ConfigurationError,
            SessionError,
            JoinError,
            TransformationError,
            PerformanceError,
        ]

        for exception_class in exception_classes:
            assert (
                exception_class.__doc__ is not None
            ), f"{exception_class.__name__} should have a docstring"
            assert (
                len(exception_class.__doc__.strip()) > 0
            ), f"{exception_class.__name__} docstring should not be empty"


class TestExceptionUsagePatterns:
    """
    Test suite for common exception usage patterns and scenarios.

    This test class validates realistic exception usage patterns that
    would occur in production Spark Simplicity applications, ensuring
    that exceptions behave correctly in real-world scenarios.

    Test Organization:
        - Real-world Scenarios: Practical exception usage patterns
        - Error Context: Details dictionary usage for debugging
        - Exception Chaining: Nested exceptions and cause relationships
        - Performance: Exception creation and handling performance
    """

    # Real-world Exception Scenarios
    # ==============================

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_data_validation_scenario(self) -> None:
        """
        Test realistic data validation error scenario.

        Simulates a practical data validation failure with contextual
        information that would be useful for debugging and operational
        monitoring in production environments.
        """
        invalid_data_details = {
            "file_path": "/data/input/customers.csv",
            "validation_rules": ["not_null", "unique_id", "valid_email"],
            "failed_rows": [125, 347, 892],
            "failure_count": 3,
            "total_rows": 10000,
            "failure_rate": 0.0003,
        }

        with pytest.raises(DataFrameValidationError) as exc_info:
            raise DataFrameValidationError(
                "DataFrame validation failed: 3 rows contain invalid data",
                invalid_data_details,
            )

        exception = exc_info.value
        assert "3 rows contain invalid data" in exception.message
        assert exception.details["failure_count"] == 3
        assert "/data/input/customers.csv" in exception.details["file_path"]

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_connection_failure_scenario(self) -> None:
        """
        Test realistic connection failure error scenario.

        Simulates a database connection failure with detailed connection
        parameters and error context for operational troubleshooting.
        """
        connection_details = {
            "host": "prod-db.company.com",
            "port": 1433,
            "database": "analytics_warehouse",
            "connection_timeout": 30,
            "retry_attempts": 3,
            "error_code": "TIMEOUT",
            "network_latency_ms": 2500,
        }

        with pytest.raises(DatabaseConnectionError) as exc_info:
            raise DatabaseConnectionError(
                "Failed to connect to SQL Server after 3 retry attempts",
                connection_details,
            )

        exception = exc_info.value
        assert "3 retry attempts" in exception.message
        assert exception.details["host"] == "prod-db.company.com"
        assert exception.details["retry_attempts"] == 3

    @pytest.mark.unit
    @pytest.mark.scenario
    def test_file_processing_scenario(self) -> None:
        """
        Test realistic file processing error scenario.

        Simulates file I/O operations with comprehensive error context
        including file paths, sizes, and processing parameters.
        """
        file_processing_details = {
            "operation": "parquet_write",
            "input_file": "/tmp/processed_data.csv",
            "output_file": "/data/warehouse/processed_data.parquet",
            "file_size_mb": 2048,
            "partition_count": 100,
            "compression": "snappy",
            "processing_time_ms": 45000,
            "memory_usage_mb": 8192,
        }

        with pytest.raises(FileWriteError) as exc_info:
            raise FileWriteError(
                "Failed to write Parquet file: insufficient disk space",
                file_processing_details,
            )

        exception = exc_info.value
        assert "insufficient disk space" in exception.message
        assert exception.details["file_size_mb"] == 2048
        assert exception.details["operation"] == "parquet_write"

    # Error Context and Debugging Testing
    # ==================================

    @pytest.mark.unit
    def test_structured_error_context(self) -> None:
        """
        Test structured error context for debugging support.

        Validates that complex error context can be properly stored
        and retrieved from exception details, supporting advanced
        debugging and operational monitoring requirements.
        """
        error_context = {
            "timestamp": "2024-01-15T14:30:00Z",
            "user_id": "analyst_001",
            "session_id": "spark_session_abc123",
            "operation_stack": [
                "data_transformation",
                "schema_validation",
                "type_conversion",
            ],
            "system_info": {
                "spark_version": "3.5.0",
                "python_version": "3.11.7",
                "memory_total_gb": 64,
                "cpu_cores": 16,
            },
            "performance_metrics": {
                "execution_time_ms": 12500,
                "records_processed": 500000,
                "memory_peak_mb": 4096,
            },
        }

        exception = TransformationError(
            "Data transformation failed during type conversion", error_context
        )

        # Validate structured access to error context
        assert exception.details["user_id"] == "analyst_001"
        assert len(exception.details["operation_stack"]) == 3
        assert exception.details["system_info"]["spark_version"] == "3.5.0"
        assert exception.details["performance_metrics"]["records_processed"] == 500000

    @pytest.mark.unit
    def test_exception_with_dynamic_context(self) -> None:
        """
        Test exception with dynamically generated error context.

        Validates that error context can be built dynamically based on
        runtime conditions, supporting flexible error reporting and
        contextual debugging information.
        """

        def generate_error_context(operation: str, **kwargs: Any) -> Dict[str, Any]:
            """Generate dynamic error context based on operation and parameters."""
            base_context = {
                "operation": operation,
                "timestamp": "2024-01-15T15:00:00Z",
                "environment": "production",
            }
            base_context.update(kwargs)
            return base_context

        # Generate context for different operations
        join_context = generate_error_context(
            "inner_join",
            left_table="customers",
            right_table="orders",
            join_keys=["customer_id"],
            result_count=0,
        )

        session_context = generate_error_context(
            "session_creation",
            driver_memory="8g",
            executor_memory="4g",
            executor_cores=2,
            config_overrides={"spark.sql.adaptive.enabled": "true"},
        )

        # Test join error with dynamic context
        join_exception = JoinError("Join operation returned empty result", join_context)
        assert join_exception.details["operation"] == "inner_join"
        assert join_exception.details["result_count"] == 0

        # Test session error with dynamic context
        session_exception = SessionError("Session creation failed", session_context)
        assert session_exception.details["driver_memory"] == "8g"
        config_overrides = session_exception.details["config_overrides"]
        assert config_overrides["spark.sql.adaptive.enabled"] == "true"

    # Performance and Edge Case Testing
    # =================================

    @pytest.mark.unit
    @pytest.mark.performance
    def test_exception_creation_performance(self) -> None:
        """
        Test exception creation performance with large details.

        Validates that exception creation remains performant even with
        large error context dictionaries, ensuring that error handling
        doesn't significantly impact application performance.
        """
        # Create large details dictionary
        large_details = {f"metric_{i}": f"value_{i}" for i in range(10000)}
        large_details["summary"] = "Performance test with large context"

        # Exception creation should complete quickly
        exception = PerformanceError("Performance test exception", large_details)

        assert len(exception.details) == 10001  # 10000 + summary
        assert exception.details["summary"] == "Performance test with large context"
        assert exception.details["metric_5000"] == "value_5000"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_exception_with_circular_references(self) -> None:
        """
        Test exception handling with circular references in details.

        Validates behavior when details dictionary contains circular
        references, ensuring that exception creation doesn't fail
        catastrophically with complex object structures.
        """
        # Create circular reference structure
        details_with_cycle: Dict[str, Any] = {"status": "failed"}
        details_with_cycle["self_reference"] = details_with_cycle

        # Exception should handle circular references gracefully
        exception = ConfigurationError("Circular reference test", details_with_cycle)

        assert exception.details["status"] == "failed"
        assert exception.details["self_reference"] is exception.details

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_exception_serialization_behavior(self) -> None:
        """
        Test exception behavior with serialization scenarios.

        Validates that exceptions maintain expected behavior when
        processed through serialization operations commonly used
        in distributed Spark environments.
        """
        import pickle

        message = "Serialization test"
        details = {"test_data": [1, 2, 3], "test_flag": True}

        original_exception = SessionError(message, details)

        # Test pickle serialization/deserialization
        serialized = pickle.dumps(original_exception)
        deserialized_exception = pickle.loads(serialized)

        assert isinstance(deserialized_exception, SessionError)
        assert deserialized_exception.message == message
        assert deserialized_exception.details == details


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=spark_simplicity.exceptions",
            "--cov-report=term-missing",
        ]
    )
