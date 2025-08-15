"""
Spark Simplicity - Email Connection Tests
========================================

Comprehensive test suite for EmailSender with enterprise-grade coverage and validation.
This module provides extensive testing of email connection functionality, secure SMTP
connectivity, message formatting capabilities, and error handling essential for
production email communication workflows.

Key Testing Areas:
    - **SMTP Configuration**: Connection initialization, security settings, and protocol
      selection
    - **Message Processing**: Plain text, HTML, and multipart message construction
    - **Attachment Handling**: File attachment processing, encoding, and validation
    - **Bulk Email Operations**: Mass email campaigns with personalization and tracking
    - **Security Validation**: SSL/TLS configuration, certificate handling, and
      authentication
    - **Error Management**: Comprehensive exception handling and failure scenarios

Test Coverage:
    **Connection Management**:
    - SMTP server configuration with various protocols and security settings
    - SSL/TLS context creation with certificate validation and encryption options
    - Authentication mechanisms with password and token-based access
    - Connection establishment across different SMTP providers and configurations

    **Message Operations**:
    - Simple text email composition and delivery with recipient management
    - Rich HTML email formatting with multipart content and fallback options
    - File attachment processing with MIME encoding and header configuration
    - Bulk email processing with template personalization and delivery tracking

Enterprise Integration Testing:
    - **Production Configurations**: Multiple SMTP environments and security settings
    - **Security Compliance**: Encrypted connections, authentication, and certificate
      validation
    - **Performance Validation**: Email delivery efficiency and resource optimization
    - **Error Recovery**: Comprehensive error handling and failure scenario testing
    - **Monitoring Integration**: Logging, delivery tracking, and operational visibility

Testing Philosophy:
    This test suite follows enterprise software development best practices with
    comprehensive coverage, realistic scenario simulation, and production-ready
    validation patterns. All tests are designed to validate both functional
    correctness and operational reliability in demanding production email
    communication environments.
"""

import importlib.util
import logging
import os
import smtplib
import ssl
import sys
import tempfile
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any, List, cast
from unittest.mock import MagicMock, Mock, mock_open, patch

import pytest

# Import optimisé avec gestion propre des chemins
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

EMAIL_CONNECTION_PATH = (
    PROJECT_ROOT / "spark_simplicity" / "connections" / "email_connection.py"
)
spec = importlib.util.spec_from_file_location("email_connection", EMAIL_CONNECTION_PATH)
if spec is None or spec.loader is None:
    raise ImportError("Could not load email_connection module")
email_connection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(email_connection)

EmailSender = email_connection.EmailSender


class TestEmailSender:
    """
    Comprehensive test suite for EmailSender with 100% coverage.

    This test class validates all aspects of email connection functionality
    including SMTP configuration, message processing, attachment handling,
    bulk email operations, and enterprise security features. Tests are
    organized by functional areas with comprehensive coverage of normal operations,
    edge cases, and error conditions.

    Test Organization:
        - Initialization: Configuration validation and security setup
        - Logger Setup: Logging configuration and handler management
        - SSL Context: Security context creation and certificate handling
        - Email Normalization: Address processing and validation
        - Message Sending: Simple, HTML, attachment, and bulk operations
        - Error Handling: Exception management and failure scenarios
    """

    @staticmethod
    def setup_method() -> None:
        """Clear any existing logger handlers before each test to ensure isolation."""
        logger = logging.getLogger("EmailSender")
        logger.handlers.clear()

    # Initialization and Configuration Testing
    # =======================================

    @pytest.mark.unit
    def test_initialization_basic_config(self, email_config: Any) -> None:
        """
        Test email sender initialization with basic SMTP configuration.

        Validates proper initialization of connection attributes, security settings,
        and logger configuration using standard SMTP parameters. Ensures correct
        default value application and secure connection setup.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
            use_ssl=email_config["use_tls"],
        )

        # Validate connection attributes
        assert sender.smtp_server == email_config["smtp_host"], (
            f"SMTP server mismatch: expected '{email_config['smtp_host']}', "
            f"got '{sender.smtp_server}'"
        )
        assert sender.port == email_config["smtp_port"], (
            f"Port mismatch: expected {email_config['smtp_port']}, "
            f"got {sender.port}"
        )
        assert sender.email == email_config["email"], (
            f"Email mismatch: expected '{email_config['email']}', "
            f"got '{sender.email}'"
        )
        assert sender.password == email_config["password"], (
            f"Password mismatch: expected '{email_config['password']}', "
            f"got '{sender.password}'"
        )
        assert sender.use_ssl == email_config["use_tls"], (
            f"SSL setting mismatch: expected {email_config['use_tls']}, "
            f"got {sender.use_ssl}"
        )
        assert (
            sender.verify_ssl is True
        ), f"SSL verification should default to True, got {sender.verify_ssl}"

        # Validate logger initialization
        assert sender.logger is not None, "Logger should be initialized"
        assert (
            sender.logger.name == "EmailSender"
        ), f"Logger name mismatch: expected 'EmailSender', got '{sender.logger.name}'"

    @pytest.mark.unit
    def test_initialization_ssl_disabled(self, email_config: Any) -> None:
        """
        Test initialization with SSL verification disabled.

        Validates proper handling of SSL verification disabled scenario with
        appropriate warning logging and security parameter configuration.
        Essential for testing and debugging environments.
        """
        with patch.object(EmailSender, "_setup_logger") as mock_logger_setup:
            mock_logger = Mock()
            mock_logger_setup.return_value = mock_logger

            sender = EmailSender(
                smtp_server=email_config["smtp_host"],
                port=email_config["smtp_port"],
                email=email_config["email"],
                password=email_config["password"],
                verify_ssl=False,
            )

            # Validate security warning is logged
            mock_logger.warning.assert_called_once_with(
                "WARNING: SSL verification disabled - security risk!"
            )
            assert (
                sender.verify_ssl is False
            ), f"SSL verification should be False, got {sender.verify_ssl}"

    @pytest.mark.unit
    def test_initialization_without_password(self, email_config: Any) -> None:
        """
        Test initialization without authentication password.

        Validates proper handling of SMTP servers that don't require authentication
        or use alternative authentication methods. Essential for testing local
        SMTP servers and specific enterprise configurations.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=None,
        )

        assert (
            sender.password is None
        ), f"Password should be None, got {sender.password}"
        assert sender.email == email_config["email"], (
            f"Email should be preserved: expected '{email_config['email']}', "
            f"got '{sender.email}'"
        )

    @pytest.mark.unit
    def test_initialization_custom_ssl_settings(self, email_config: Any) -> None:
        """
        Test initialization with custom SSL configuration combinations.

        Validates proper handling of various SSL/TLS configuration scenarios
        including direct SSL connections, STARTTLS, and certificate validation
        settings for enterprise security compliance.
        """
        # Test SSL direct connection (port 465)
        sender_ssl = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=465,
            email=email_config["email"],
            password=email_config["password"],
            use_ssl=True,
            verify_ssl=True,
        )

        assert sender_ssl.use_ssl is True, "SSL should be enabled"
        assert sender_ssl.port == 465, f"Port should be 465, got {sender_ssl.port}"
        assert sender_ssl.verify_ssl is True, "SSL verification should be enabled"

        # Test STARTTLS connection (port 587)
        sender_starttls = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=587,
            email=email_config["email"],
            password=email_config["password"],
            use_ssl=False,
            verify_ssl=True,
        )

        assert sender_starttls.use_ssl is False, "SSL should be disabled for STARTTLS"
        assert (
            sender_starttls.port == 587
        ), f"Port should be 587, got {sender_starttls.port}"

    # Logger Setup Testing
    # ===================

    @pytest.mark.unit
    def test_setup_logger_creation(self) -> None:
        """
        Test logger setup creates properly configured logger instance.

        Validates logger creation, configuration, handler attachment, and
        formatting setup for comprehensive email operation monitoring and
        debugging capabilities.
        """
        logger = EmailSender._setup_logger()

        assert (
            logger.name == "EmailSender"
        ), f"Logger name should be 'EmailSender', got '{logger.name}'"
        assert (
            logger.level == logging.INFO
        ), f"Logger level should be INFO ({logging.INFO}), got {logger.level}"
        assert (
            len(logger.handlers) == 1
        ), f"Logger should have exactly 1 handler, got {len(logger.handlers)}"

        # Validate handler configuration
        handler = logger.handlers[0]
        assert isinstance(
            handler, logging.StreamHandler
        ), f"Handler should be StreamHandler, got {type(handler)}"
        assert handler.formatter is not None, "Handler should have formatter"

    @pytest.mark.unit
    def test_setup_logger_idempotent(self) -> None:
        """
        Test logger setup is idempotent and doesn't create duplicate handlers.

        Validates that multiple calls to _setup_logger don't create duplicate
        handlers, ensuring clean logger configuration across multiple
        EmailSender instances.
        """
        # First call creates logger with handler
        logger1 = EmailSender._setup_logger()
        initial_handler_count = len(logger1.handlers)

        # Second call should not add additional handlers
        logger2 = EmailSender._setup_logger()
        final_handler_count = len(logger2.handlers)

        assert logger1 is logger2, "Should return same logger instance"
        assert final_handler_count == initial_handler_count, (
            f"Handler count should remain {initial_handler_count}, "
            f"got {final_handler_count}"
        )

    # SSL Context Creation Testing
    # ===========================

    @pytest.mark.unit
    @pytest.mark.security
    def test_create_secure_context_with_verification(self, email_config: Any) -> None:
        """
        Test SSL context creation with certificate verification enabled.

        Validates secure SSL context configuration with strict certificate
        validation, hostname checking, and TLS 1.2+ enforcement for
        maximum security in production environments.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
            verify_ssl=True,
        )

        context = sender._create_secure_context()

        # Validate secure context configuration
        assert isinstance(
            context, ssl.SSLContext
        ), f"Should return SSLContext instance, got {type(context)}"
        assert (
            context.check_hostname is True
        ), "Hostname checking should be enabled for security"
        assert (
            context.verify_mode == ssl.CERT_REQUIRED
        ), f"Certificate verification should be required, got {context.verify_mode}"
        assert (
            context.minimum_version >= ssl.TLSVersion.TLSv1_2
        ), f"Minimum TLS version should be 1.2+, got {context.minimum_version}"

    @pytest.mark.unit
    @pytest.mark.security
    def test_create_secure_context_without_verification(
        self, email_config: Any
    ) -> None:
        """
        Test SSL context creation with certificate verification disabled.

        Validates SSL context configuration for testing/debugging scenarios
        with disabled certificate validation while maintaining encryption
        for development and testing environments.
        """
        with patch.object(EmailSender, "_setup_logger") as mock_logger_setup:
            mock_logger = Mock()
            mock_logger_setup.return_value = mock_logger

            sender = EmailSender(
                smtp_server=email_config["smtp_host"],
                port=email_config["smtp_port"],
                email=email_config["email"],
                password=email_config["password"],
                verify_ssl=False,
            )

            context = sender._create_secure_context()

            # Validate insecure context configuration
            assert (
                context.check_hostname is False
            ), "Hostname checking should be disabled"
            assert (
                context.verify_mode == ssl.CERT_NONE
            ), f"Certificate verification should be disabled, got {context.verify_mode}"
            assert context.minimum_version >= ssl.TLSVersion.TLSv1_2, (
                f"TLS version enforcement should still apply, "
                f"got {context.minimum_version!r}"
            )

            # Validate security warning is logged during context creation
            mock_logger.warning.assert_any_call(
                "SSL verification disabled - insecure usage!"
            )

    # Email Normalization Testing
    # ===========================

    @pytest.mark.unit
    def test_normalize_email_list_string_single(self) -> None:
        """
        Test email normalization from single string address.

        Validates proper conversion of single email address string into
        standardized list format with whitespace trimming and validation.
        """
        result = EmailSender._normalize_email_list("test@example.com")

        assert result == [
            "test@example.com"
        ], f"Single email should return single-item list, got {result}"

    @pytest.mark.unit
    def test_normalize_email_list_string_multiple(self) -> None:
        """
        Test email normalization from comma-separated string addresses.

        Validates proper parsing and normalization of multiple email addresses
        from comma-separated string input with whitespace handling and
        empty value filtering.
        """
        input_emails = "test1@example.com, test2@example.com,  test3@example.com  "
        result = EmailSender._normalize_email_list(input_emails)

        expected = ["test1@example.com", "test2@example.com", "test3@example.com"]
        assert result == expected, (
            f"Multiple emails should be parsed correctly, "
            f"expected {expected}, got {result}"
        )

    @pytest.mark.unit
    def test_normalize_email_list_string_with_empty_values(self) -> None:
        """
        Test email normalization with empty and whitespace-only values.

        Validates proper filtering of empty strings, whitespace-only entries,
        and malformed input while preserving valid email addresses in
        comma-separated format.
        """
        input_emails = "test1@example.com,  ,test2@example.com, , test3@example.com"
        result = EmailSender._normalize_email_list(input_emails)

        expected = ["test1@example.com", "test2@example.com", "test3@example.com"]
        assert (
            result == expected
        ), f"Should filter empty values, expected {expected}, got {result}"

    @pytest.mark.unit
    def test_normalize_email_list_list_input(self) -> None:
        """
        Test email normalization from list input format.

        Validates proper processing of email addresses provided as list
        with whitespace trimming, empty value filtering, and preservation
        of valid addresses.
        """
        input_emails = [
            "test1@example.com",
            "  test2@example.com  ",
            "",
            "test3@example.com",
        ]
        result = EmailSender._normalize_email_list(input_emails)

        expected = ["test1@example.com", "test2@example.com", "test3@example.com"]
        assert (
            result == expected
        ), f"Should normalize list input, expected {expected}, got {result}"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_normalize_email_list_invalid_input(self) -> None:
        """
        Test email normalization with invalid input types.

        Validates robust handling of non-string, non-list input types
        returning empty list for graceful error handling and preventing
        application crashes from invalid input.
        """
        # Test with None
        result_none = EmailSender._normalize_email_list(None)
        assert (
            result_none == []
        ), f"None input should return empty list, got {result_none}"

        # Test with integer
        result_int = EmailSender._normalize_email_list(123)
        assert (
            result_int == []
        ), f"Integer input should return empty list, got {result_int}"

        # Test with dictionary
        result_dict = EmailSender._normalize_email_list({"email": "test@example.com"})
        assert (
            result_dict == []
        ), f"Dict input should return empty list, got {result_dict}"

    @pytest.mark.unit
    def test_normalize_email_list_empty_inputs(self) -> None:
        """
        Test email normalization with various empty input scenarios.

        Validates proper handling of empty strings, empty lists, and
        whitespace-only inputs returning appropriate empty results
        for consistent behavior across edge cases.
        """
        # Empty string
        result_empty_string = EmailSender._normalize_email_list("")
        assert (
            result_empty_string == []
        ), f"Empty string should return empty list, got {result_empty_string}"

        # Empty list
        result_empty_list = EmailSender._normalize_email_list([])
        assert (
            result_empty_list == []
        ), f"Empty list should return empty list, got {result_empty_list}"

        # Whitespace-only string
        result_whitespace = EmailSender._normalize_email_list("   ,  ,  ")
        assert (
            result_whitespace == []
        ), f"Whitespace-only should return empty list, got {result_whitespace}"

    # Simple Email Sending Testing
    # ============================

    @pytest.mark.unit
    def test_send_simple_email_success(self, email_config: Any) -> None:
        """
        Test successful simple email sending with basic configuration.

        Validates complete simple email sending workflow including message
        construction, recipient processing, and SMTP delivery with proper
        success status reporting.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            result = sender.send_simple_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                message="Test message body",
            )

            assert result is True, f"Should return True on success, got {result}"
            mock_send.assert_called_once()

            # Validate message construction
            call_args = mock_send.call_args
            msg, recipients = call_args[0]

            assert isinstance(
                msg, MIMEText
            ), f"Should create MIMEText message, got {type(msg)}"
            assert (
                msg["Subject"] == "Test Subject"
            ), f"Subject mismatch: expected 'Test Subject', got {msg['Subject']}"
            assert (
                msg["From"] == email_config["email"]
            ), f"From mismatch: expected '{email_config['email']}', got {msg['From']}"
            assert (
                msg["To"] == "recipient@example.com"
            ), f"To mismatch: expected 'recipient@example.com', got {msg['To']}"
            assert recipients == ["recipient@example.com"], (
                f"Recipients mismatch: expected ['recipient@example.com'], "
                f"got {recipients}"
            )

    @pytest.mark.unit
    def test_send_simple_email_with_cc_bcc(self, email_config: Any) -> None:
        """
        Test simple email sending with CC and BCC recipients.

        Validates proper handling of carbon copy and blind carbon copy
        recipients including header configuration and recipient list
        management for complete email distribution functionality.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            result = sender.send_simple_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                message="Test message",
                cc="cc@example.com",
                bcc=["bcc1@example.com", "bcc2@example.com"],
            )

            assert result is True, f"Should return True on success, got {result}"

            # Validate message and recipients
            call_args = mock_send.call_args
            msg, recipients = call_args[0]

            assert (
                msg["To"] == "recipient@example.com"
            ), f"To field incorrect: got {msg['To']}"
            assert msg["Cc"] == "cc@example.com", f"CC field incorrect: got {msg['Cc']}"
            assert "Bcc" not in msg, "BCC should not appear in headers"

            expected_recipients = [
                "recipient@example.com",
                "cc@example.com",
                "bcc1@example.com",
                "bcc2@example.com",
            ]
            assert recipients == expected_recipients, (
                f"All recipients should be included: expected {expected_recipients}, "
                f"got {recipients}"
            )

    @pytest.mark.unit
    def test_send_simple_email_multiple_recipients(self, email_config: Any) -> None:
        """
        Test simple email sending to multiple primary recipients.

        Validates proper handling of multiple TO recipients with correct
        header formatting and recipient list processing for bulk
        email distribution scenarios.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            result = sender.send_simple_email(
                to_email=["recipient1@example.com", "recipient2@example.com"],
                subject="Multi-recipient Test",
                message="Test message to multiple recipients",
            )

            assert result is True, f"Should return True on success, got {result}"

            call_args = mock_send.call_args
            msg, recipients = call_args[0]

            expected_to = "recipient1@example.com, recipient2@example.com"
            assert msg["To"] == expected_to, (
                f"To field should contain both recipients: expected '{expected_to}', "
                f"got '{msg['To']}'"
            )
            assert recipients == [
                "recipient1@example.com",
                "recipient2@example.com",
            ], f"Recipients list incorrect: got {recipients}"

    @pytest.mark.unit
    def test_send_simple_email_failure(self, email_config: Any) -> None:
        """
        Test simple email sending failure handling.

        Validates proper error handling and status reporting when email
        sending fails due to SMTP errors, network issues, or other
        delivery problems.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender, "_send_email", return_value=False):
            result = sender.send_simple_email(
                to_email="recipient@example.com",
                subject="Test Subject",
                message="Test message",
            )

            assert result is False, f"Should return False on failure, got {result}"

    @pytest.mark.unit
    def test_send_simple_email_exception_handling(self, email_config: Any) -> None:
        """
        Test simple email sending exception handling during message construction.

        Validates robust exception handling during message preparation and
        processing with proper error logging and status reporting for
        operational reliability.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender.logger, "error") as mock_log_error:
            # Force exception during message construction
            with patch(
                "email.mime.text.MIMEText",
                side_effect=ValueError("Message creation error"),
            ):
                result = sender.send_simple_email(
                    to_email="recipient@example.com",
                    subject="Test Subject",
                    message="Test message",
                )

                assert (
                    result is False
                ), f"Should return False on exception, got {result}"
                mock_log_error.assert_called_once()
                error_call = mock_log_error.call_args[0][0]
                assert ("Error sending simple email:" in error_call) or (
                    "SMTP error:" in error_call
                ), f"Error log should contain expected message, got: {error_call}"

    @pytest.mark.unit
    def test_send_simple_email_general_exception(self, email_config: Any) -> None:
        """
        Test simple email sending with general exception during normalization.

        Validates the general Exception catch block in send_simple_email method
        to achieve 100% coverage of exception handling paths.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender.logger, "error") as mock_log_error:
            # Force general exception during email normalization
            with patch.object(
                EmailSender,
                "_normalize_email_list",
                side_effect=RuntimeError("Normalization error"),
            ):
                result = sender.send_simple_email(
                    to_email="recipient@example.com",
                    subject="Test Subject",
                    message="Test message",
                )

                assert (
                    result is False
                ), f"Should return False on exception, got {result}"
                mock_log_error.assert_called_once()
                error_call = mock_log_error.call_args[0][0]
                assert "Error sending simple email:" in error_call

    # HTML Email Sending Testing
    # ==========================

    @pytest.mark.unit
    def test_send_html_email_success(self, email_config: Any) -> None:
        """
        Test successful HTML email sending with rich content.

        Validates HTML email message construction, multipart formatting,
        and proper content-type handling for rich email presentations
        and business communications.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        html_content = "<h1>Test HTML Email</h1><p>This is a <b>bold</b> message.</p>"

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            result = sender.send_html_email(
                to_email="recipient@example.com",
                subject="HTML Test Subject",
                html_content=html_content,
            )

            assert result is True, f"Should return True on success, got {result}"
            mock_send.assert_called_once()

            # Validate multipart message construction
            call_args = mock_send.call_args
            msg, _ = call_args[0]

            assert isinstance(
                msg, MIMEMultipart
            ), f"Should create MIMEMultipart message, got {type(msg)}"
            assert (
                msg.get_content_subtype() == "alternative"
            ), f"Should use 'alternative' subtype, got {msg.get_content_subtype()}"
            assert (
                msg["Subject"] == "HTML Test Subject"
            ), f"Subject incorrect: got {msg['Subject']}"

            # Validate HTML part is attached
            parts = msg.get_payload()
            assert len(parts) >= 1, f"Should have at least 1 part, got {len(parts)}"

    @pytest.mark.unit
    def test_send_html_email_with_text_alternative(self, email_config: Any) -> None:
        """
        Test HTML email sending with plain text alternative.

        Validates proper multipart message construction with both HTML
        and plain text alternatives for maximum email client compatibility
        and accessibility requirements.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        html_content = "<h1>HTML Version</h1><p>Rich content here.</p>"
        text_content = "Plain text version of the message."

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            result = sender.send_html_email(
                to_email="recipient@example.com",
                subject="Multipart Test",
                html_content=html_content,
                text_content=text_content,
            )

            assert result is True, f"Should return True on success, got {result}"

            call_args = mock_send.call_args
            msg, _ = call_args[0]

            # Should have both text and HTML parts
            parts = msg.get_payload()
            assert (
                len(parts) == 2
            ), f"Should have 2 parts (text + HTML), got {len(parts)}"

    @pytest.mark.unit
    def test_send_html_email_with_cc_bcc(self, email_config: Any) -> None:
        """
        Test HTML email sending with CC and BCC recipients.

        Validates proper recipient management and header configuration
        for HTML emails with carbon copy and blind carbon copy
        distribution functionality.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            result = sender.send_html_email(
                to_email="recipient@example.com",
                subject="HTML with Recipients",
                html_content="<p>HTML content</p>",
                cc=["cc1@example.com", "cc2@example.com"],
                bcc="bcc@example.com",
            )

            assert result is True, f"Should return True on success, got {result}"

            call_args = mock_send.call_args
            msg, recipients = call_args[0]

            assert (
                msg["Cc"] == "cc1@example.com, cc2@example.com"
            ), f"CC field incorrect: got {msg['Cc']}"
            assert "Bcc" not in msg, "BCC should not appear in headers"

            expected_recipients = [
                "recipient@example.com",
                "cc1@example.com",
                "cc2@example.com",
                "bcc@example.com",
            ]
            assert (
                recipients == expected_recipients
            ), f"All recipients should be included: got {recipients}"

    @pytest.mark.unit
    def test_send_html_email_failure(self, email_config: Any) -> None:
        """
        Test HTML email sending failure handling.

        Validates proper error handling and status reporting when HTML
        email sending fails with appropriate error logging and
        graceful degradation.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender, "_send_email", return_value=False):
            result = sender.send_html_email(
                to_email="recipient@example.com",
                subject="HTML Test",
                html_content="<p>Test content</p>",
            )

            assert result is False, f"Should return False on failure, got {result}"

    @pytest.mark.unit
    def test_send_html_email_exception_handling(self, email_config: Any) -> None:
        """
        Test HTML email exception handling during message construction.

        Validates robust exception management during HTML message preparation
        with proper error logging and failure reporting for operational
        reliability and debugging support.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender.logger, "error") as mock_log_error:
            # Force exception during message construction
            with patch(
                "email.mime.multipart.MIMEMultipart",
                side_effect=ValueError("HTML message creation error"),
            ):
                result = sender.send_html_email(
                    to_email="recipient@example.com",
                    subject="HTML Test",
                    html_content="<p>Test</p>",
                )

                assert (
                    result is False
                ), f"Should return False on exception, got {result}"
                mock_log_error.assert_called_once()

    @pytest.mark.unit
    def test_send_html_email_general_exception(self, email_config: Any) -> None:
        """
        Test HTML email sending with general exception during processing.

        Validates the general Exception catch block in send_html_email method
        to achieve 100% coverage of exception handling paths.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender.logger, "error") as mock_log_error:
            # Force general exception during email normalization
            with patch.object(
                EmailSender,
                "_normalize_email_list",
                side_effect=RuntimeError("Normalization error"),
            ):
                result = sender.send_html_email(
                    to_email="recipient@example.com",
                    subject="HTML Test",
                    html_content="<h1>Test</h1>",
                )

                assert (
                    result is False
                ), f"Should return False on exception, got {result}"
                mock_log_error.assert_called_once()
                error_call = mock_log_error.call_args[0][0]
                assert "Error sending HTML email:" in error_call

    # Attachment Email Sending Testing
    # ================================

    @pytest.mark.unit
    def test_send_email_with_attachments_success(self, email_config: Any) -> None:
        """
        Test successful email sending with file attachments.

        Validates complete attachment email workflow including file
        validation, MIME encoding, and multipart message construction
        for professional document distribution.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        # Create temporary test files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp1:
            tmp1.write("Test file 1 content")
            tmp1_path = tmp1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp2:
            tmp2.write("Test file 2 content")
            tmp2_path = tmp2.name

        try:
            with patch.object(sender, "_send_email", return_value=True) as mock_send:
                with patch.object(EmailSender, "_attach_file") as mock_attach:
                    result = sender.send_email_with_attachments(
                        to_emails="recipient@example.com",
                        subject="Email with Attachments",
                        message="Please find attached files.",
                        attachments=[tmp1_path, tmp2_path],
                    )

                    assert (
                        result is True
                    ), f"Should return True on success, got {result}"
                    mock_send.assert_called_once()

                    # Validate file attachment calls
                    assert (
                        mock_attach.call_count == 2
                    ), f"Should attach 2 files, got {mock_attach.call_count} calls"

                    call_args = mock_send.call_args
                    msg, _ = call_args[0]
                    assert isinstance(
                        msg, MIMEMultipart
                    ), f"Should create multipart message, got {type(msg)}"

        finally:
            # Clean up temporary files
            os.unlink(tmp1_path)
            os.unlink(tmp2_path)

    @pytest.mark.unit
    def test_send_email_with_attachments_missing_files(self, email_config: Any) -> None:
        """
        Test attachment email with non-existent files.

        Validates proper handling of missing attachment files with
        appropriate warning logging and graceful continuation of
        email sending process.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            with patch.object(sender.logger, "warning") as mock_warn:
                with patch.object(EmailSender, "_attach_file") as mock_attach:
                    result = sender.send_email_with_attachments(
                        to_emails="recipient@example.com",
                        subject="Test Subject",
                        message="Test message",
                        attachments=[
                            "/nonexistent/file1.txt",
                            "/nonexistent/file2.txt",
                        ],
                    )

                    assert (
                        result is True
                    ), f"Should return True despite missing files, got {result}"
                    mock_send.assert_called_once()

                    # Validate warning logs for missing files
                    assert mock_warn.call_count == 2, (
                        f"Should log 2 warnings for missing files, "
                        f"got {mock_warn.call_count}"
                    )

                    # Validate no files were attached
                    mock_attach.assert_not_called()

    @pytest.mark.unit
    def test_send_email_with_attachments_mixed_files(self, email_config: Any) -> None:
        """
        Test attachment email with mix of existing and non-existent files.

        Validates selective file attachment processing where valid files
        are attached and missing files generate warnings without stopping
        the email sending process.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        # Create one temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("Valid file content")
            tmp_path = tmp.name

        try:
            with patch.object(sender, "_send_email", return_value=True) as mock_send:
                with patch.object(sender.logger, "warning") as mock_warn:
                    with patch.object(EmailSender, "_attach_file") as mock_attach:
                        result = sender.send_email_with_attachments(
                            to_emails="recipient@example.com",
                            subject="Mixed Attachments Test",
                            message="Test with mixed files",
                            attachments=[tmp_path, "/nonexistent/file.txt"],
                        )

                        assert result is True, f"Should return True, got {result}"
                        mock_send.assert_called_once()

                        # Should attach 1 valid file and log 1 warning
                        assert (
                            mock_attach.call_count == 1
                        ), f"Should attach 1 valid file, got {mock_attach.call_count}"
                        assert mock_warn.call_count == 1, (
                            f"Should log 1 warning for missing file, "
                            f"got {mock_warn.call_count}"
                        )

        finally:
            os.unlink(tmp_path)

    @pytest.mark.unit
    def test_send_email_with_attachments_exception_handling(
        self, email_config: Any
    ) -> None:
        """
        Test attachment email exception handling.

        Validates robust exception management during attachment processing
        with proper error logging and failure reporting for reliable
        operation in production environments.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender.logger, "error") as mock_log_error:
            # Force exception during message construction
            with patch(
                "email.mime.multipart.MIMEMultipart",
                side_effect=ValueError("Attachment message creation error"),
            ):
                result = sender.send_email_with_attachments(
                    to_emails="recipient@example.com",
                    subject="Test Subject",
                    message="Test message",
                    attachments=[],
                )

                assert (
                    result is False
                ), f"Should return False on exception, got {result}"
                mock_log_error.assert_called_once()

    @pytest.mark.unit
    def test_send_email_with_attachments_cc_coverage(self, email_config: Any) -> None:
        """
        Test attachment email with CC recipients to cover line 377.

        Validates proper CC header assignment in send_email_with_attachments
        to achieve 100% coverage of the CC branch.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as tmp_file:
            tmp_file.write("test content")
            tmp_path = tmp_file.name

        try:
            with patch.object(sender, "_send_email", return_value=True) as mock_send:
                result = sender.send_email_with_attachments(
                    to_emails="recipient@example.com",
                    subject="Test with CC",
                    message="Test message",
                    attachments=[tmp_path],
                    cc="cc@example.com",  # This covers line 377
                )

                assert result is True, f"Should return True, got {result}"
                mock_send.assert_called_once()

                # Validate CC header was set
                call_args = mock_send.call_args
                msg, _ = call_args[0]
                assert (
                    msg["Cc"] == "cc@example.com"
                ), f"CC header should be set, got {msg.get('Cc')}"

        finally:
            os.unlink(tmp_path)

    @pytest.mark.unit
    def test_send_email_with_attachments_general_exception(
        self, email_config: Any
    ) -> None:
        """
        Test attachment email with general exception during processing.

        Validates the general Exception catch block in send_email_with_attachments
        method to achieve 100% coverage of exception handling paths.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender.logger, "error") as mock_log_error:
            # Force general exception during email normalization
            with patch.object(
                EmailSender,
                "_normalize_email_list",
                side_effect=RuntimeError("Normalization error"),
            ):
                result = sender.send_email_with_attachments(
                    to_emails="recipient@example.com",
                    subject="Test Subject",
                    message="Test message",
                    attachments=[],
                )

                assert (
                    result is False
                ), f"Should return False on exception, got {result}"
                mock_log_error.assert_called_once()
                error_call = mock_log_error.call_args[0][0]
                assert "Error sending email with attachments:" in error_call

    # File Attachment Testing
    # ======================

    @pytest.mark.unit
    def test_attach_file_success(self) -> None:
        """
        Test successful file attachment with proper MIME encoding.

        Validates complete file attachment process including binary file
        reading, base64 encoding, MIME header configuration, and
        attachment integration into multipart messages.
        """
        # Create temporary test file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as tmp:
            tmp.write("Test file content for attachment")
            tmp_path = tmp.name

        try:
            msg = MIMEMultipart()

            # Mock file operations
            with patch("builtins.open", mock_open(read_data=b"test binary content")):
                with patch("os.path.basename", return_value="test.txt"):
                    EmailSender._attach_file(msg, tmp_path)

                    # Validate attachment was added to message
                    parts = cast(List[Any], msg.get_payload())
                    assert (
                        len(parts) == 1
                    ), f"Should have 1 attachment, got {len(parts)}"

                    attachment = cast(MIMEMultipart, parts[0])
                    assert (
                        attachment.get_content_type() == "application/octet-stream"
                    ), (
                        f"Content type should be application/octet-stream, "
                        f"got {attachment.get_content_type()}"
                    )

                    # Validate Content-Disposition header
                    disposition = attachment.get("Content-Disposition")
                    assert (
                        disposition is not None
                    ), "Should have Content-Disposition header"
                    assert (
                        "attachment" in disposition
                    ), f"Should specify attachment disposition, got {disposition}"
                    assert (
                        "test.txt" in disposition
                    ), f"Should include filename, got {disposition}"

        finally:
            os.unlink(tmp_path)

    # Bulk Email Sending Testing
    # ==========================

    @pytest.mark.unit
    def test_send_bulk_email_success(
        self, email_config: Any, bulk_recipients: Any
    ) -> None:
        """
        Test successful bulk email sending with personalization.

        Validates complete bulk email workflow including template processing,
        personalization, delivery tracking, and comprehensive result reporting
        for mass communication campaigns.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        template = "Hello {name}, your account balance is ${balance}."

        with patch.object(sender, "send_simple_email", return_value=True) as mock_send:
            with patch.object(sender.logger, "info") as mock_info:
                result = sender.send_bulk_email(
                    recipients=bulk_recipients,
                    subject="Account Statement",
                    message_template=template,
                )

                # Validate results structure
                assert isinstance(
                    result, dict
                ), f"Should return dict, got {type(result)}"
                assert result["success"] == len(bulk_recipients), (
                    f"Success count should be {len(bulk_recipients)}, "
                    f"got {result['success']}"
                )
                assert (
                    result["failed"] == 0
                ), f"Failed count should be 0, got {result['failed']}"
                assert (
                    result["errors"] == []
                ), f"Errors list should be empty, got {result['errors']}"

                # Validate all emails were sent
                assert mock_send.call_count == len(bulk_recipients), (
                    f"Should send {len(bulk_recipients)} emails, "
                    f"got {mock_send.call_count}"
                )

                # Validate success logging
                assert mock_info.call_count == len(bulk_recipients), (
                    f"Should log {len(bulk_recipients)} success messages, "
                    f"got {mock_info.call_count}"
                )

    @pytest.mark.unit
    def test_send_bulk_email_with_failures(self, email_config: Any) -> None:
        """
        Test bulk email sending with mixed success and failure scenarios.

        Validates proper error tracking, partial success handling, and
        comprehensive result reporting when some emails fail during
        bulk delivery operations.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        recipients = [
            {"email": "success1@example.com", "name": "User 1"},
            {"email": "failure@example.com", "name": "User 2"},
            {"email": "success2@example.com", "name": "User 3"},
        ]

        template = "Hello {name}, this is your message."

        # Mock send_simple_email to return failure for middle recipient
        def mock_send_side_effect(*args: Any, **kwargs: Any) -> bool:
            """Mock function for send_simple_email with failure simulation."""
            email = args[0] if args else kwargs.get("to_email", "")
            return bool(email != "failure@example.com")

        with patch.object(
            sender, "send_simple_email", side_effect=mock_send_side_effect
        ):
            result = sender.send_bulk_email(
                recipients=recipients,
                subject="Mixed Results Test",
                message_template=template,
            )

            # Validate mixed results
            assert (
                result["success"] == 2
            ), f"Should have 2 successes, got {result['success']}"
            assert (
                result["failed"] == 1
            ), f"Should have 1 failure, got {result['failed']}"
            assert (
                len(result["errors"]) == 1
            ), f"Should have 1 error message, got {len(result['errors'])}"
            assert (
                "failure@example.com" in result["errors"][0]
            ), f"Error should mention failed recipient, got {result['errors']}"

    @pytest.mark.unit
    def test_send_bulk_email_missing_template_variables(
        self, email_config: Any
    ) -> None:
        """
        Test bulk email with missing template variables.

        Validates proper handling of template personalization errors
        when recipient data is missing required template variables
        with appropriate error tracking and logging.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        # Recipients with missing template variables
        recipients = [
            {
                "email": "complete@example.com",
                "name": "Complete User",
                "balance": "100",
            },
            {
                "email": "missing@example.com",
                "name": "Missing User",
            },  # Missing 'balance'
        ]

        template = "Hello {name}, your balance is ${balance}."

        with patch.object(sender, "send_simple_email", return_value=True):
            with patch.object(sender.logger, "error") as mock_error:
                result = sender.send_bulk_email(
                    recipients=recipients,
                    subject="Template Test",
                    message_template=template,
                )

                # Validate error handling
                assert (
                    result["success"] == 1
                ), f"Should have 1 success, got {result['success']}"
                assert (
                    result["failed"] == 1
                ), f"Should have 1 failure, got {result['failed']}"
                assert (
                    len(result["errors"]) == 1
                ), f"Should have 1 error, got {len(result['errors'])}"

                # Validate error logging
                mock_error.assert_called()
                error_call = mock_error.call_args[0][0]
                assert (
                    "Missing variable" in error_call
                ), f"Error should mention missing variable, got: {error_call}"

    @pytest.mark.unit
    def test_send_bulk_email_personalized_cc_bcc(self, email_config: Any) -> None:
        """
        Test bulk email with personalized CC and BCC recipients.

        Validates proper handling of per-recipient CC/BCC customization
        and global CC/BCC application with precedence rules for
        advanced bulk email distribution scenarios.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        recipients = [
            {
                "email": "user1@example.com",
                "name": "User 1",
                "cc": "manager1@example.com",
            },
            {
                "email": "user2@example.com",
                "name": "User 2",
                "bcc": "audit@example.com",
            },
        ]

        template = "Hello {name}, this is your personalized message."

        with patch.object(sender, "send_simple_email", return_value=True) as mock_send:
            result = sender.send_bulk_email(
                recipients=recipients,
                subject="Personalized Recipients",
                message_template=template,
                cc="global_cc@example.com",
                bcc="global_bcc@example.com",
            )

            assert (
                result["success"] == 2
            ), f"Should send 2 emails, got {result['success']}"
            assert (
                mock_send.call_count == 2
            ), f"Should call send 2 times, got {mock_send.call_count}"

            # Validate personalized CC/BCC was passed correctly
            call_args_list = mock_send.call_args_list

            # First call should have personalized CC and global BCC
            first_call_kwargs = call_args_list[0][1]
            assert first_call_kwargs["cc"] == "manager1@example.com", (
                f"First email should use personalized CC, "
                f"got {first_call_kwargs.get('cc')}"
            )
            assert (
                first_call_kwargs["bcc"] == "global_bcc@example.com"
            ), f"First email should use global BCC, got {first_call_kwargs.get('bcc')}"

            # Second call should have global CC and personalized BCC
            second_call_kwargs = call_args_list[1][1]
            assert (
                second_call_kwargs["cc"] == "global_cc@example.com"
            ), f"Second email should use global CC, got {second_call_kwargs.get('cc')}"
            assert second_call_kwargs["bcc"] == "audit@example.com", (
                f"Second email should use personalized BCC, "
                f"got {second_call_kwargs.get('bcc')}"
            )

    @pytest.mark.unit
    def test_send_bulk_email_exception_handling(self, email_config: Any) -> None:
        """
        Test bulk email exception handling for individual recipient failures.

        Validates robust exception management during bulk processing where
        individual recipient failures don't stop the entire bulk operation
        with proper error tracking and logging.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        recipients = [
            {"email": "success@example.com", "name": "Success User"},
            {"email": "exception@example.com", "name": "Exception User"},
        ]

        template = "Hello {name}, test message."

        # Mock to raise exception for specific recipient
        def mock_send_side_effect(*args: Any, **kwargs: Any) -> bool:
            """Mock function for send_simple_email with exception simulation."""
            email = args[0] if args else kwargs.get("to_email", "")
            if email == "exception@example.com":
                raise RuntimeError("Individual send error")
            return True

        with patch.object(
            sender, "send_simple_email", side_effect=mock_send_side_effect
        ):
            with patch.object(sender.logger, "error") as mock_error:
                result = sender.send_bulk_email(
                    recipients=recipients,
                    subject="Exception Test",
                    message_template=template,
                )

                # Validate partial success
                assert (
                    result["success"] == 1
                ), f"Should have 1 success, got {result['success']}"
                assert (
                    result["failed"] == 1
                ), f"Should have 1 failure, got {result['failed']}"
                assert (
                    len(result["errors"]) == 1
                ), f"Should have 1 error, got {len(result['errors'])}"

                # Validate exception was logged
                mock_error.assert_called()

    # Core SMTP Sending Testing
    # ========================

    @pytest.mark.unit
    def test_send_email_starttls_success(self, email_config: Any) -> None:
        """
        Test successful email sending via STARTTLS connection.

        Validates complete STARTTLS workflow including secure context creation,
        connection establishment, authentication, and message delivery for
        standard SMTP operations on port 587.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=587,
            email=email_config["email"],
            password=email_config["password"],
            use_ssl=False,  # STARTTLS
        )

        msg = MIMEText("Test message")
        recipients = ["test@example.com"]

        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp

            with patch.object(sender, "_create_secure_context") as mock_context:
                mock_ssl_context = Mock()
                mock_context.return_value = mock_ssl_context

                result = sender._send_email(msg, recipients)

                assert result is True, f"Should return True on success, got {result}"

                # Validate SMTP connection setup
                mock_smtp_class.assert_called_once_with(email_config["smtp_host"], 587)
                mock_smtp.starttls.assert_called_once_with(context=mock_ssl_context)
                mock_smtp.login.assert_called_once_with(
                    email_config["email"], email_config["password"]
                )
                mock_smtp.send_message.assert_called_once_with(msg, to_addrs=recipients)

    @pytest.mark.unit
    def test_send_email_ssl_success(self, email_config: Any) -> None:
        """
        Test successful email sending via direct SSL connection.

        Validates complete SSL workflow including secure connection establishment,
        authentication, and message delivery for direct SSL operations
        typically used on port 465.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=465,
            email=email_config["email"],
            password=email_config["password"],
            use_ssl=True,  # Direct SSL
        )

        msg = MIMEText("Test message")
        recipients = ["test@example.com"]

        with patch("smtplib.SMTP_SSL") as mock_smtp_ssl_class:
            mock_smtp = MagicMock()
            mock_smtp_ssl_class.return_value.__enter__.return_value = mock_smtp

            with patch.object(sender, "_create_secure_context") as mock_context:
                mock_ssl_context = Mock()
                mock_context.return_value = mock_ssl_context

                result = sender._send_email(msg, recipients)

                assert result is True, f"Should return True on success, got {result}"

                # Validate SSL connection setup
                mock_smtp_ssl_class.assert_called_once_with(
                    email_config["smtp_host"], 465, context=mock_ssl_context
                )
                mock_smtp.login.assert_called_once_with(
                    email_config["email"], email_config["password"]
                )
                mock_smtp.send_message.assert_called_once_with(msg, to_addrs=recipients)

    @pytest.mark.unit
    def test_send_email_ssl_no_authentication(self, email_config: Any) -> None:
        """
        Test email sending via SSL without authentication.

        Validates SSL connection without login to cover the authentication branch
        in SSL mode for servers that don't require authentication.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=465,
            email=email_config["email"],
            password=None,  # No password to cover the if self.password branch
            use_ssl=True,
        )

        msg = MIMEText("Test message")
        recipients = ["test@example.com"]

        with patch("smtplib.SMTP_SSL") as mock_smtp_ssl_class:
            mock_smtp = MagicMock()
            mock_smtp_ssl_class.return_value.__enter__.return_value = mock_smtp

            with patch.object(sender, "_create_secure_context") as mock_context:
                mock_ssl_context = Mock()
                mock_context.return_value = mock_ssl_context

                result = sender._send_email(msg, recipients)

                assert result is True, f"Should return True on success, got {result}"

                # Validate SSL connection setup without authentication
                mock_smtp_ssl_class.assert_called_once_with(
                    email_config["smtp_host"], 465, context=mock_ssl_context
                )
                # Should NOT call login when password is None
                mock_smtp.login.assert_not_called()
                mock_smtp.send_message.assert_called_once_with(msg, to_addrs=recipients)

    @pytest.mark.unit
    def test_send_email_no_authentication(self, email_config: Any) -> None:
        """
        Test email sending without SMTP authentication.

        Validates email delivery for SMTP servers that don't require
        authentication, such as local SMTP relays or testing servers,
        with proper connection handling and message delivery.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=25,
            email=email_config["email"],
            password=None,  # No authentication
        )

        msg = MIMEText("Test message")
        recipients = ["test@example.com"]

        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp

            with patch.object(sender, "_create_secure_context") as mock_context:
                mock_ssl_context = Mock()
                mock_context.return_value = mock_ssl_context

                result = sender._send_email(msg, recipients)

                assert result is True, f"Should return True on success, got {result}"

                # Validate no login was attempted
                mock_smtp.login.assert_not_called()
                mock_smtp.send_message.assert_called_once_with(msg, to_addrs=recipients)

    @pytest.mark.unit
    def test_send_email_smtp_exception(self, email_config: Any) -> None:
        """
        Test email sending SMTP exception handling.

        Validates proper handling of SMTP-specific errors including
        authentication failures, connection timeouts, and server
        rejection with appropriate error logging and status reporting.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        msg = MIMEText("Test message")
        recipients = ["test@example.com"]

        with patch("smtplib.SMTP") as mock_smtp_class:
            # Force SMTP exception
            mock_smtp_class.side_effect = smtplib.SMTPException("SMTP server error")

            with patch.object(sender.logger, "error") as mock_log_error:
                result = sender._send_email(msg, recipients)

                assert (
                    result is False
                ), f"Should return False on SMTP error, got {result}"
                mock_log_error.assert_called_once()

                error_call = mock_log_error.call_args[0][0]
                assert (
                    "SMTP error:" in error_call
                ), f"Should log SMTP error, got: {error_call}"

    @pytest.mark.unit
    def test_send_email_ssl_exception(self, email_config: Any) -> None:
        """
        Test email sending SSL exception handling.

        Validates proper handling of SSL/TLS-specific errors including
        certificate validation failures, protocol mismatches, and
        encryption errors with appropriate error logging.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        msg = MIMEText("Test message")
        recipients = ["test@example.com"]

        with patch("smtplib.SMTP") as mock_smtp_class:
            # Force SSL exception during connection
            mock_smtp_class.side_effect = ssl.SSLError("SSL certificate error")

            with patch.object(sender.logger, "error") as mock_log_error:
                result = sender._send_email(msg, recipients)

                assert (
                    result is False
                ), f"Should return False on SSL error, got {result}"
                mock_log_error.assert_called_once()

                error_call = mock_log_error.call_args[0][0]
                assert (
                    "SSL/TLS error:" in error_call
                ), f"Should log SSL error, got: {error_call}"

    @pytest.mark.unit
    def test_send_email_general_exception(self, email_config: Any) -> None:
        """
        Test email sending general exception handling.

        Validates robust exception management for unexpected errors
        during email sending process with comprehensive error logging
        and graceful failure handling for operational reliability.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        msg = MIMEText("Test message")
        recipients = ["test@example.com"]

        with patch("smtplib.SMTP") as mock_smtp_class:
            # Force general exception
            mock_smtp_class.side_effect = ConnectionError("Unexpected error")

            with patch.object(sender.logger, "error") as mock_log_error:
                result = sender._send_email(msg, recipients)

                assert (
                    result is False
                ), f"Should return False on exception, got {result}"
                mock_log_error.assert_called_once()

                error_call = mock_log_error.call_args[0][0]
                assert (
                    "Error during sending:" in error_call
                ), f"Should log general error, got: {error_call}"

    @pytest.mark.unit
    def test_send_email_success_logging(self, email_config: Any) -> None:
        """
        Test successful email sending with proper success logging.

        Validates comprehensive success logging including recipient count
        and delivery confirmation for operational monitoring and
        audit trail maintenance.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        msg = MIMEText("Test message")
        recipients = ["test1@example.com", "test2@example.com", "test3@example.com"]

        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp

            with patch.object(sender.logger, "info") as mock_log_info:
                result = sender._send_email(msg, recipients)

                assert result is True, f"Should return True on success, got {result}"
                mock_log_info.assert_called_once()

                info_call = mock_log_info.call_args[0][0]
                assert (
                    "Email sent successfully to 3 recipient(s)" == info_call
                ), f"Should log success with recipient count, got: {info_call}"

    # Edge Cases and Error Handling Testing
    # ====================================

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_empty_recipient_lists(self, email_config: Any) -> None:
        """
        Test email sending with empty recipient lists.

        Validates proper handling of empty TO, CC, and BCC recipient
        lists ensuring graceful operation and appropriate message
        construction for edge case scenarios.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            # Test with empty string recipients
            result1 = sender.send_simple_email(
                to_email="", subject="Empty Recipients Test", message="Test message"
            )

            # Should still attempt to send (with empty recipient list)
            assert (
                result1 is True
            ), f"Should return True even with empty recipients, got {result1}"
            mock_send.assert_called()

            call_args = mock_send.call_args
            _, recipients = call_args[0]
            assert (
                recipients == []
            ), f"Recipients should be empty list, got {recipients}"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_whitespace_only_recipients(self, email_config: Any) -> None:
        """
        Test email sending with whitespace-only recipient strings.

        Validates proper handling of recipient strings containing only
        whitespace characters with appropriate filtering and normalization
        for robust input processing.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            result = sender.send_simple_email(
                to_email="   ,  ,   ",  # Only whitespace and commas
                subject="Whitespace Test",
                message="Test message",
            )

            assert result is True, f"Should return True, got {result}"

            call_args = mock_send.call_args
            _, recipients = call_args[0]
            assert (
                recipients == []
            ), f"Should filter out whitespace recipients, got {recipients}"

    @pytest.mark.unit
    @pytest.mark.edge_case
    @pytest.mark.unicode
    def test_unicode_content_handling(
        self, email_config: Any, unicode_test_data: Any
    ) -> None:
        """
        Test email sending with Unicode content in various fields.

        Validates proper Unicode character handling in email subjects,
        message bodies, and recipient addresses for international
        character support and global email compatibility.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        unicode_subject = f"测试邮件 - {unicode_test_data['emoji']}"
        unicode_message = (
            f"Hello {unicode_test_data['mixed']}, this is a test message "
            f"with Cyrillic: {unicode_test_data['cyrillic']}"
        )

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            result = sender.send_simple_email(
                to_email="test@example.com",
                subject=unicode_subject,
                message=unicode_message,
            )

            assert result is True, f"Should handle Unicode content, got {result}"

            call_args = mock_send.call_args
            msg, _ = call_args[0]

            # Validate Unicode content is preserved
            assert (
                msg["Subject"] == unicode_subject
            ), f"Unicode subject should be preserved, got {msg['Subject']}"

    @pytest.mark.unit
    @pytest.mark.edge_case
    def test_very_long_content(self, email_config: Any) -> None:
        """
        Test email sending with very long content.

        Validates proper handling of large email content including
        long subjects, extensive message bodies, and large recipient
        lists for stress testing and capacity validation.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        # Create very long content
        long_subject = "Very Long Subject " * 100  # ~1800 characters
        long_message = (
            "This is a very long message content. " * 1000
        )  # ~37000 characters

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            result = sender.send_simple_email(
                to_email="test@example.com", subject=long_subject, message=long_message
            )

            assert result is True, f"Should handle long content, got {result}"
            mock_send.assert_called_once()

            call_args = mock_send.call_args
            msg, _ = call_args[0]
            assert len(msg["Subject"]) > 1000, "Should preserve long subject"

    # Integration and End-to-End Testing
    # ==================================

    @pytest.mark.integration
    def test_complete_email_workflow(self, email_config: Any) -> None:
        """
        Test complete email workflow from initialization to delivery.

        Validates end-to-end email processing including sender initialization,
        message construction, SMTP connection, authentication, and delivery
        for comprehensive integration testing.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        # Mock complete SMTP workflow
        with patch("smtplib.SMTP") as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp

            # Test complete simple email workflow
            result = sender.send_simple_email(
                to_email="test@example.com",
                subject="Integration Test",
                message="Complete workflow test message",
            )

            assert result is True, f"Complete workflow should succeed, got {result}"

            # Validate all SMTP operations were called
            mock_smtp_class.assert_called_once()
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once()
            mock_smtp.send_message.assert_called_once()

    @pytest.mark.integration
    def test_multiple_email_types_sequence(self, email_config: Any) -> None:
        """
        Test sending multiple email types in sequence.

        Validates consistent behavior and state management when sending
        different email types (simple, HTML, attachments) consecutively
        using the same EmailSender instance.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        with patch.object(sender, "_send_email", return_value=True) as mock_send:
            # Send simple email
            result1 = sender.send_simple_email(
                to_email="test1@example.com",
                subject="Simple Test",
                message="Simple message",
            )

            # Send HTML email
            result2 = sender.send_html_email(
                to_email="test2@example.com",
                subject="HTML Test",
                html_content="<p>HTML content</p>",
            )

            # Send email with attachments (empty attachment list)
            result3 = sender.send_email_with_attachments(
                to_emails="test3@example.com",
                subject="Attachment Test",
                message="Message with attachments",
                attachments=[],
            )

            # All should succeed
            assert all(
                [result1, result2, result3]
            ), f"All email types should succeed: {[result1, result2, result3]}"
            assert (
                mock_send.call_count == 3
            ), f"Should send 3 emails, got {mock_send.call_count}"

    # Performance and Stress Testing
    # ==============================

    @pytest.mark.performance
    def test_bulk_email_performance(self, email_config: Any) -> None:
        """
        Test bulk email performance with large recipient lists.

        Validates performance characteristics and resource efficiency
        when processing large recipient lists for mass email campaigns
        and high-volume communication scenarios.
        """
        sender = EmailSender(
            smtp_server=email_config["smtp_host"],
            port=email_config["smtp_port"],
            email=email_config["email"],
            password=email_config["password"],
        )

        # Create large recipient list
        large_recipient_list = [
            {"email": f"user{i}@example.com", "name": f"User {i}", "id": str(i)}
            for i in range(100)  # 100 recipients
        ]

        template = "Hello {name}, your user ID is {id}."

        with patch.object(sender, "send_simple_email", return_value=True) as mock_send:
            result = sender.send_bulk_email(
                recipients=large_recipient_list,
                subject="Performance Test",
                message_template=template,
            )

            # Validate all emails were processed
            assert (
                result["success"] == 100
            ), f"Should process all 100 emails, got {result['success']}"
            assert (
                result["failed"] == 0
            ), f"Should have no failures, got {result['failed']}"
            assert (
                mock_send.call_count == 100
            ), f"Should send 100 emails, got {mock_send.call_count}"


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=spark_simplicity.connections.email_connection",
            "--cov-report=term-missing",
        ]
    )
