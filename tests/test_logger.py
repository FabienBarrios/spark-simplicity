"""
Spark Simplicity - Logger Module Tests
=====================================

Comprehensive test suite for the logger module with enterprise-grade
coverage and validation.

This module provides extensive testing of logging functionality,
configuration management, handler prevention mechanisms, and formatting
consistency essential for production Spark data processing environments.

Key Testing Areas:
    - **Logger Creation**: Instance creation and configuration validation
    - **Handler Management**: Prevention of duplicate handlers and proper
      console output setup
    - **Format Validation**: Consistent log formatting and timestamp handling
    - **Level Configuration**: INFO level setting and inheritance behavior
    - **Multiple Loggers**: Independent logger instances for different modules
    - **Edge Cases**: Empty names, special characters, and Unicode support

Test Coverage:
    **Logger Lifecycle**:
    - Logger instance creation with proper configuration
    - Handler creation and attachment for console output
    - Format string application and timestamp generation
    - Level setting and propagation control

    **Handler Management**:
    - Prevention of duplicate handler creation for same logger name
    - Console handler configuration with stdout stream
    - Formatter attachment and format string validation
    - Propagation control to prevent duplicate logging

Enterprise Integration Testing:
    - **Multiple Module Support**: Different logger names and isolation
    - **Performance Validation**: Repeated logger requests optimization
    - **Format Consistency**: Standardized log format across all modules
    - **Stream Configuration**: Proper stdout configuration and output handling

Testing Philosophy:
    This test suite follows enterprise software development best practices with
    comprehensive coverage, realistic scenario simulation, and production-ready
    validation patterns. All tests validate both functional correctness and
    operational reliability in production logging environments.
"""

import io
import logging
import sys
from typing import cast

import pytest

from spark_simplicity.logger import get_logger


class TestGetLogger:
    """
    Comprehensive test suite for get_logger function with 100% coverage.

    This test class validates all aspects of logger functionality including
    logger creation, handler management, formatting configuration, and
    duplicate handler prevention. Tests are organized by functional areas
    with comprehensive coverage of normal operations, edge cases, and
    error conditions.

    Test Organization:
        - Logger Creation: Basic instantiation and configuration
        - Handler Management: Console handler setup and duplicate prevention
        - Format Validation: Log format string and timestamp validation
        - Multiple Loggers: Independent logger instances and isolation
        - Performance Testing: Repeated requests and caching behavior
        - Edge Cases: Special characters, empty names, and Unicode support
    """

    def test_basic_logger_creation(self) -> None:
        """
        Test basic logger creation with standard module name.

        Validates that get_logger creates a properly configured Logger instance
        with the specified name, INFO level, and console handler. Ensures basic
        functionality works correctly for standard use cases.
        """
        logger_name = "spark_simplicity.test_module"
        logger = get_logger(logger_name)

        # Validate logger instance and basic properties
        assert isinstance(logger, logging.Logger), "Should return Logger instance"
        assert logger.name == logger_name, f"Logger name should be '{logger_name}'"
        assert logger.level == logging.INFO, "Logger level should be INFO"
        assert logger.propagate is False, "Logger propagation should be disabled"

    def test_console_handler_configuration(self) -> None:
        """
        Test console handler creation and configuration.

        Validates that the logger properly creates a StreamHandler pointing to
        stdout with the correct formatter configuration. Essential for ensuring
        consistent console output across all modules.
        """
        logger_name = "spark_simplicity.handler_test"
        logger = get_logger(logger_name)

        # Validate handler configuration
        assert len(logger.handlers) == 1, "Should have exactly one handler"
        handler = logger.handlers[0]
        assert isinstance(
            handler, logging.StreamHandler
        ), "Handler should be StreamHandler"
        assert handler.stream is sys.stdout, "Handler should output to stdout"

        # Validate formatter configuration
        formatter = handler.formatter
        assert formatter is not None, "Handler should have a formatter"
        expected_format = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        assert (
            formatter._fmt == expected_format
        ), f"Format should be '{expected_format}'"

    def test_duplicate_handler_prevention(self) -> None:
        """
        Test prevention of duplicate handler creation.

        Validates that calling get_logger multiple times with the same name
        returns the same logger instance without creating additional handlers.
        Critical for preventing duplicate log entries in production environments.
        """
        logger_name = "spark_simplicity.duplicate_test"

        # Clear any existing loggers to ensure clean test
        if logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[logger_name]

        # First call should create logger with handler
        logger1 = get_logger(logger_name)
        handler_count_1 = len(logger1.handlers)
        assert handler_count_1 == 1, "First call should create one handler"

        # Second call should not add additional handlers
        logger2 = get_logger(logger_name)
        assert logger1 is logger2, "Should return the same logger instance"
        assert (
            len(logger2.handlers) == handler_count_1
        ), "Should not create additional handlers"

        # Third call should also not add handlers
        logger3 = get_logger(logger_name)
        assert logger1 is logger3, "Should return the same logger instance"
        assert (
            len(logger3.handlers) == handler_count_1
        ), "Should not create additional handlers"

    def test_multiple_logger_instances(self) -> None:
        """
        Test creation of multiple independent logger instances.

        Validates that different logger names create separate logger instances
        with independent handlers and configurations. Essential for module
        isolation and proper logging organization.
        """
        logger_names = [
            "spark_simplicity.module1",
            "spark_simplicity.module2",
            "spark_simplicity.module3",
        ]

        loggers = []
        for name in logger_names:
            logger = get_logger(name)
            loggers.append(logger)

        # Validate each logger is unique
        for i, logger in enumerate(loggers):
            assert (
                logger.name == logger_names[i]
            ), f"Logger {i} should have correct name"
            assert len(logger.handlers) == 1, f"Logger {i} should have one handler"
            assert logger.level == logging.INFO, f"Logger {i} should be INFO level"
            assert logger.propagate is False, f"Logger {i} should not propagate"

        # Validate loggers are independent instances
        for i, logger1 in enumerate(loggers):
            for j, logger2 in enumerate(loggers):
                if i != j:
                    assert (
                        logger1 is not logger2
                    ), f"Logger {i} should be different from Logger {j}"

    def test_logger_output_format(self) -> None:
        """
        Test actual log output format and content.

        Validates that log messages are formatted correctly with timestamp,
        level, logger name, and message content. Essential for ensuring
        consistent and readable log output in production environments.
        """
        logger_name = "spark_simplicity.format_test"

        # Clear any existing logger to ensure clean test
        if logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[logger_name]

        logger = get_logger(logger_name)

        # Capture output by redirecting the handler's stream
        captured_output = io.StringIO()
        handler = cast(logging.StreamHandler, logger.handlers[0])
        original_stream = handler.stream
        handler.stream = captured_output

        try:
            test_message = "Test log message for format validation"
            logger.info(test_message)

            output = captured_output.getvalue()

            # Validate output contains expected elements
            assert test_message in output, "Output should contain the log message"
            assert logger_name in output, "Output should contain logger name"
            assert "INFO" in output, "Output should contain log level"

            # Validate timestamp format (basic check)
            import re

            timestamp_pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}"
            assert re.search(
                timestamp_pattern, output
            ), "Output should contain timestamp"
        finally:
            # Restore original stream
            handler.stream = original_stream

    def test_different_log_levels(self) -> None:
        """
        Test logger behavior with different log levels.

        Validates that the logger properly handles different log levels
        (INFO, WARNING, ERROR, DEBUG) and respects the configured INFO level.
        Essential for proper log level filtering in production environments.
        """
        logger_name = "spark_simplicity.level_test"

        # Clear any existing logger to ensure clean test
        if logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[logger_name]

        logger = get_logger(logger_name)

        # Create a custom string stream for the handler
        captured_output = io.StringIO()
        handler = cast(logging.StreamHandler, logger.handlers[0])
        original_stream = handler.stream
        handler.stream = captured_output

        try:
            logger.debug("Debug message (should not appear)")
            logger.info("Info message (should appear)")
            logger.warning("Warning message (should appear)")
            logger.error("Error message (should appear)")

            output = captured_output.getvalue()

            # DEBUG should not appear (below INFO level)
            assert "Debug message" not in output, "DEBUG messages should not appear"

            # INFO, WARNING, ERROR should appear
            assert "Info message" in output, "INFO messages should appear"
            assert "WARNING" in output, "WARNING level should appear in output"
            assert "Warning message" in output, "WARNING messages should appear"
            assert "ERROR" in output, "ERROR level should appear in output"
            assert "Error message" in output, "ERROR messages should appear"
        finally:
            # Restore original stream
            handler.stream = original_stream

    def test_logger_with_empty_name(self) -> None:
        """
        Test logger creation with empty string name.

        Validates proper handling of edge case where empty string is provided
        as logger name. Ensures robust parameter validation and graceful
        handling of unusual input scenarios.
        """
        logger = get_logger("")

        assert isinstance(logger, logging.Logger), "Should return Logger instance"
        # Empty string name becomes "root" in Python logging
        assert logger.name == "root", "Empty string should become root logger"
        assert logger.level == logging.INFO, "Logger should have INFO level"

        # The root logger may already have handlers from pytest, so we just check
        # that it has at least one handler and that get_logger didn't break it
        assert len(logger.handlers) >= 1, "Should have at least one handler"

        # For root logger with existing handlers, propagate might not be changed
        # This is correct behavior as per the logger.py implementation
        # (propagate=False is only set when new handlers are added)

        # Test that we can still use the logger normally
        captured_output = io.StringIO()

        # Find if there's a StreamHandler we can test with
        stream_handler = None
        for handler in logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                stream_handler = handler
                break

        if stream_handler:
            # Test logging works with the stream handler
            original_stream = stream_handler.stream
            stream_handler.stream = captured_output
            try:
                logger.info("Test message for empty name logger")
                output = captured_output.getvalue()
                assert "Test message for empty name logger" in output
            finally:
                stream_handler.stream = original_stream

    def test_logger_with_special_characters(self) -> None:
        """
        Test logger creation with special characters in name.

        Validates that logger names containing special characters, dots,
        underscores, and hyphens are properly handled. Essential for supporting
        diverse module naming conventions in enterprise environments.
        """
        special_names = [
            "spark_simplicity.module-with-dashes",
            "spark_simplicity.module_with_underscores",
            "spark_simplicity.module.with.dots",
            "spark_simplicity.module@with@symbols",
            "spark_simplicity.module123with456numbers",
        ]

        for name in special_names:
            logger = get_logger(name)
            assert logger.name == name, f"Logger should accept name '{name}'"
            assert (
                logger.level == logging.INFO
            ), f"Logger '{name}' should have INFO level"
            assert len(logger.handlers) == 1, f"Logger '{name}' should have one handler"

    def test_logger_unicode_support(self) -> None:
        """
        Test logger creation and operation with Unicode characters.

        Validates proper encoding and processing of international characters
        in logger names and log messages, ensuring global compatibility
        and robust character encoding support.
        """
        unicode_names = [
            "spark_simplicity.测试模块",  # Chinese
            "spark_simplicity.тест_модуль",  # Russian
            "spark_simplicity.módulo_prueba",  # Spanish
            "spark_simplicity.🚀_module",  # Emoji
        ]

        for name in unicode_names:
            logger = get_logger(name)
            assert logger.name == name, f"Logger should accept Unicode name '{name}'"
            assert logger.level == logging.INFO, "Unicode logger should have INFO level"
            assert len(logger.handlers) == 1, "Unicode logger should have one handler"

            # Test logging Unicode messages
            captured_output = io.StringIO()
            handler = cast(logging.StreamHandler, logger.handlers[0])
            original_stream = handler.stream
            handler.stream = captured_output

            try:
                logger.info("Unicode test message: {}".format(name))
                output = captured_output.getvalue()
                assert name in output, "Unicode logger name should appear in output"
            finally:
                handler.stream = original_stream

    def test_logger_handler_stream_configuration(self) -> None:
        """
        Test that console handler is properly configured with stdout stream.

        Validates that the StreamHandler is specifically configured to use
        sys.stdout (not stderr) for consistent console output behavior.
        Essential for proper log routing in production environments.
        """
        logger_name = "spark_simplicity.stream_test"
        logger = get_logger(logger_name)

        handler = logger.handlers[0]
        assert isinstance(handler, logging.StreamHandler), "Should be StreamHandler"
        assert handler.stream is sys.stdout, "Handler should use stdout stream"
        assert handler.stream is not sys.stderr, "Handler should not use stderr stream"

    def test_logger_formatter_attributes(self) -> None:
        """
        Test detailed formatter configuration and attributes.

        Validates that the log formatter has correct format string, date format,
        and other configuration attributes needed for consistent log formatting
        across all application modules.
        """
        logger_name = "spark_simplicity.formatter_test"
        logger = get_logger(logger_name)

        handler = logger.handlers[0]
        formatter = handler.formatter

        assert formatter is not None, "Handler should have formatter"
        expected_format = "%(asctime)s %(levelname)s %(name)s: %(message)s"
        assert (
            formatter._fmt == expected_format
        ), f"Format should be '{expected_format}'"

        # Test that formatter produces expected output structure
        import logging

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        formatted_message = formatter.format(record)
        assert "INFO" in formatted_message, "Formatted message should contain level"
        assert (
            "test.logger" in formatted_message
        ), "Formatted message should contain name"
        assert (
            "Test message" in formatted_message
        ), "Formatted message should contain message"

    def test_logger_performance_repeated_calls(self) -> None:
        """
        Test performance characteristics of repeated get_logger calls.

        Validates that multiple calls to get_logger with the same name
        efficiently return the cached logger instance without performance
        degradation. Critical for high-throughput production environments.
        """
        logger_name = "spark_simplicity.performance_test"

        # Clear any existing logger to ensure clean test
        if logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[logger_name]

        # First call creates the logger
        first_logger = get_logger(logger_name)

        # Multiple subsequent calls should return same instance
        loggers = []
        for _ in range(100):
            logger = get_logger(logger_name)
            loggers.append(logger)

        # Validate all returned loggers are the same instance
        for logger in loggers:
            assert (
                logger is first_logger
            ), "All calls should return same logger instance"
            assert len(logger.handlers) == 1, "Should maintain single handler"

    def test_logger_configuration_isolation(self) -> None:
        """
        Test that different loggers have independent configurations.

        Validates that modifying one logger's configuration does not affect
        other logger instances, ensuring proper isolation between different
        modules and preventing configuration conflicts.
        """
        logger1 = get_logger("spark_simplicity.isolation_test1")
        logger2 = get_logger("spark_simplicity.isolation_test2")

        # Modify first logger's level
        original_level1 = logger1.level
        original_level2 = logger2.level
        logger1.setLevel(logging.ERROR)

        # Validate isolation
        assert logger1.level == logging.ERROR, "Logger1 level should be changed"
        assert logger2.level == original_level2, "Logger2 level should be unchanged"

        # Restore original state
        logger1.setLevel(original_level1)

    def test_logger_propagation_disabled(self) -> None:
        """
        Test that logger propagation is properly disabled when handlers are added.

        Validates that logger.propagate is set to False to prevent duplicate
        log entries when using hierarchical logger names. Essential for clean
        log output in production environments.
        """
        # Test with fresh logger names to ensure handlers are added
        logger_name = "spark_simplicity.propagation_test_fresh"
        parent_name = "spark_simplicity.parent_fresh"
        child_name = "spark_simplicity.parent_fresh.child"

        # Clear any existing loggers
        for name in [logger_name, parent_name, child_name]:
            if name in logging.Logger.manager.loggerDict:
                del logging.Logger.manager.loggerDict[name]

        logger = get_logger(logger_name)
        assert logger.propagate is False, "Logger propagation should be disabled"

        # Test with hierarchical logger names
        parent_logger = get_logger(parent_name)
        child_logger = get_logger(child_name)

        assert parent_logger.propagate is False, "Parent logger should not propagate"
        assert child_logger.propagate is False, "Child logger should not propagate"

    def test_logger_handler_level_inheritance(self) -> None:
        """
        Test logger and handler level configuration.

        Validates that the logger is set to INFO level and that the handler
        inherits appropriate level configuration for proper log filtering
        throughout the application.
        """
        logger_name = "spark_simplicity.level_inheritance_test"
        logger = get_logger(logger_name)
        handler = logger.handlers[0]

        assert logger.level == logging.INFO, "Logger should be INFO level"
        # Handler level defaults to NOTSET (0), inheriting from logger
        assert handler.level <= logging.INFO, "Handler should allow INFO messages"

    def test_logger_with_very_long_name(self) -> None:
        """
        Test logger creation with very long names.

        Validates that the logger can handle extremely long module names
        without issues, ensuring robustness for complex enterprise module
        hierarchies and naming conventions.
        """
        long_name = "spark_simplicity." + "very_long_module_name_" * 10 + "end"
        logger = get_logger(long_name)

        assert logger.name == long_name, "Should accept very long names"
        assert logger.level == logging.INFO, "Long name logger should have INFO level"
        assert len(logger.handlers) == 1, "Long name logger should have one handler"
        assert logger.propagate is False, "Long name logger should not propagate"

    def test_logger_thread_safety_simulation(self) -> None:
        """
        Test logger behavior in simulated concurrent scenarios.

        Validates that get_logger function behaves correctly when called
        multiple times in rapid succession, simulating concurrent access
        patterns typical in multi-threaded production environments.
        """
        logger_name = "spark_simplicity.thread_safety_test"

        # Clear any existing logger
        if logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[logger_name]

        # Simulate rapid concurrent calls
        loggers = []
        for i in range(50):
            logger = get_logger(logger_name)
            loggers.append(logger)

            # Verify each call returns properly configured logger
            assert (
                logger.name == logger_name
            ), f"Call {i}: Logger should have correct name"
            assert (
                logger.level == logging.INFO
            ), f"Call {i}: Logger should be INFO level"
            assert (
                len(logger.handlers) == 1
            ), f"Call {i}: Logger should have one handler"

        # Validate all calls returned same instance
        first_logger = loggers[0]
        for i, logger in enumerate(loggers[1:], 1):
            assert logger is first_logger, f"Call {i}: Should return same instance"

    def test_get_logger_return_type_annotation(self) -> None:
        """
        Test that get_logger returns correct type as specified in annotation.

        Validates that the function returns logging.Logger type as specified
        in the type annotation, ensuring type safety and IDE support for
        development and maintenance.
        """
        logger_name = "spark_simplicity.type_test"
        logger = get_logger(logger_name)

        # Type validation
        assert isinstance(
            logger, logging.Logger
        ), "Should return logging.Logger instance"

        # Validate Logger interface methods are available
        assert hasattr(logger, "info"), "Logger should have info method"
        assert hasattr(logger, "warning"), "Logger should have warning method"
        assert hasattr(logger, "error"), "Logger should have error method"
        assert hasattr(logger, "debug"), "Logger should have debug method"
        assert hasattr(logger, "setLevel"), "Logger should have setLevel method"
        assert hasattr(logger, "addHandler"), "Logger should have addHandler method"

    def test_logger_state_persistence(self) -> None:
        """
        Test that logger state persists across multiple get_logger calls.

        Validates that logger configuration, handlers, and other state
        information remain consistent across multiple function calls,
        ensuring reliable logging behavior throughout application lifecycle.
        """
        logger_name = "spark_simplicity.persistence_test"

        # First call - configure logger
        logger1 = get_logger(logger_name)
        original_handler_count = len(logger1.handlers)
        original_level = logger1.level
        original_propagate = logger1.propagate

        # Add a custom attribute for persistence testing
        setattr(logger1, "custom_test_attribute", "test_value")

        # Second call - should return same logger with same state
        logger2 = get_logger(logger_name)

        assert logger1 is logger2, "Should return same logger instance"
        assert (
            len(logger2.handlers) == original_handler_count
        ), "Handler count should persist"
        assert logger2.level == original_level, "Logger level should persist"
        assert (
            logger2.propagate == original_propagate
        ), "Propagate setting should persist"
        assert hasattr(
            logger2, "custom_test_attribute"
        ), "Custom attributes should persist"
        assert (
            getattr(logger2, "custom_test_attribute") == "test_value"
        ), "Custom attribute value should persist"

    def test_logger_with_existing_handlers(self) -> None:
        """
        Test get_logger with a logger that already has handlers.

        Validates that when a logger already has handlers, get_logger
        does not add additional handlers but still configures the logger
        properly. This covers the branch where `if not logger.handlers:`
        evaluates to False.
        """
        logger_name = "spark_simplicity.existing_handlers_test"

        # Create a logger and add a handler manually first
        logger = logging.getLogger(logger_name)
        existing_handler = logging.StreamHandler()
        logger.addHandler(existing_handler)
        initial_handler_count = len(logger.handlers)

        # Now call get_logger, which should not add another handler
        logger_from_get_logger = get_logger(logger_name)

        # Should be the same logger instance
        assert logger is logger_from_get_logger, "Should return same logger instance"

        # Should not have added additional handlers
        assert (
            len(logger_from_get_logger.handlers) == initial_handler_count
        ), "Should not add handler when handlers already exist"

        # But should still configure the logger properties
        assert logger_from_get_logger.level == logging.INFO, "Should set INFO level"

        # For loggers with existing handlers, propagate is not changed
        # This is correct behavior as per the logger.py implementation
        # (propagate=False is only set when new handlers are added)

    def test_logger_propagate_false_when_adding_handler(self) -> None:
        """
        Test that propagate is set to False when get_logger adds a new handler.

        Validates that when get_logger creates a new handler for a logger,
        it correctly sets propagate=False to prevent duplicate log entries.
        This tests the specific branch where handlers are added.
        """
        logger_name = "spark_simplicity.propagate_false_test"

        # Ensure no existing logger
        if logger_name in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict[logger_name]

        # This should create a new logger with new handler
        logger = get_logger(logger_name)

        # Should have propagate=False when handler was added
        assert (
            logger.propagate is False
        ), "Should set propagate=False when adding handler"
        assert len(logger.handlers) == 1, "Should have exactly one handler"
        assert isinstance(
            logger.handlers[0], logging.StreamHandler
        ), "Should be StreamHandler"


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=spark_simplicity.logger",
            "--cov-report=term-missing",
            "--cov-branch",
        ]
    )
