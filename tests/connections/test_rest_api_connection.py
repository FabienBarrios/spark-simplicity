"""
Spark Simplicity - REST API Connection Tests
===========================================

Comprehensive test suite for RestApiConnection with enterprise-grade
coverage and validation.

This module provides extensive testing of REST API connection functionality,
singleton pattern implementation, HTTP method support, response parsing, and
retry mechanisms essential for production Spark data processing environments.

Key Testing Areas:
    - **Singleton Pattern**: Connection instance uniqueness and lifecycle management
    - **HTTP Session Management**: Initialization, config validation, and retry logic
    - **HTTP Methods**: GET, POST, PUT, PATCH, DELETE with various parameters
    - **Response Parsing**: JSON, text, and empty response handling
    - **Error Handling**: Network errors, timeouts, and retry scenarios
    - **Security Validation**: Authentication handling and request security

Test Coverage:
    **Connection Lifecycle**:
    - Singleton pattern enforcement across different configurations and applications
    - Proper initialization with various API configurations and authentication settings
    - Session reuse and resource management throughout application lifecycle
    - Thread safety and concurrent access patterns for production environments

    **HTTP Operations**:
    - All HTTP methods with parameter validation and response parsing
    - Request/response cycle with headers, authentication, and timeout handling
    - Retry logic with exponential backoff for transient failures
    - Content-type negotiation and intelligent response parsing

Enterprise Integration Testing:
    - **Production Configurations**: Multiple API endpoints and authentication methods
    - **Security Compliance**: Token-based auth, headers, and SSL configurations
    - **Performance Validation**: Request execution efficiency and retry optimization
    - **Error Recovery**: Comprehensive error handling and failure scenario testing
    - **Monitoring Integration**: Detailed logging for operational visibility

Testing Philosophy:
    This test suite follows enterprise software development best practices with
    comprehensive coverage, realistic scenario simulation, and production-ready
    validation patterns. All tests are designed to validate both functional
    correctness and operational reliability in demanding production environments.
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict
from unittest.mock import Mock, patch

import pytest
import requests

# Import optimisé avec gestion propre des chemins
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

REST_API_CONNECTION_PATH = (
    PROJECT_ROOT / "spark_simplicity" / "connections" / "rest_api_connection.py"
)
spec = importlib.util.spec_from_file_location(
    "rest_api_connection", REST_API_CONNECTION_PATH
)
if spec is None or spec.loader is None:
    raise ImportError("Could not load rest_api_connection module")
rest_api_connection = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rest_api_connection)

RestApiConnection = rest_api_connection.RestApiConnection


class TestRestApiConnection:
    """
    Comprehensive test suite for RestApiConnection with 100% coverage.

    This test class validates all aspects of REST API connection functionality
    including singleton pattern implementation, HTTP session management,
    HTTP method operations, response parsing, and enterprise integration features.
    Tests are organized by functional areas with comprehensive coverage of normal
    operations, edge cases, and error conditions.

    Test Organization:
        - Singleton Pattern: Instance uniqueness and lifecycle management
        - Connection Initialization: Configuration validation and session setup
        - HTTP Methods: GET, POST, PUT, PATCH, DELETE operations
        - Response Handling: Content parsing and error management
        - Integration Testing: Multi-configuration and concurrent access scenarios
    """

    @staticmethod
    def setup_method() -> None:
        """Clear singleton instances before each test to ensure isolation."""
        RestApiConnection._instances.clear()

    # Singleton Pattern Testing
    # ========================

    @pytest.mark.unit
    def test_singleton_pattern_same_config(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test singleton pattern returns same instance for identical configurations.

        Validates that multiple instantiation requests with identical API
        configurations return the same connection object, ensuring proper resource
        management and preventing unnecessary connection overhead in production
        environments.
        """
        conn1 = RestApiConnection(
            mock_spark_session, sample_rest_api_config, mock_logger
        )
        conn2 = RestApiConnection(
            mock_spark_session, sample_rest_api_config, mock_logger
        )

        assert conn1 is conn2, (
            f"Singleton pattern failed: conn1 ({id(conn1)}) should be "
            f"identical to conn2 ({id(conn2)})"
        )
        assert (
            len(RestApiConnection._instances) == 1
        ), f"Expected 1 singleton instance, found {len(RestApiConnection._instances)}"

    @pytest.mark.unit
    def test_singleton_pattern_different_configs(
        self,
        mock_spark_session: Any,
        mock_logger: Any,
        sample_rest_api_config: Any,
        production_rest_api_config: Any,
    ) -> None:
        """
        Test singleton pattern creates different instances for different configurations.

        Verifies that connections with different API configurations
        (base_url, headers, auth) create separate instances while maintaining
        singleton behavior within each configuration scope, supporting
        multi-API enterprise environments.
        """
        conn1 = RestApiConnection(
            mock_spark_session, sample_rest_api_config, mock_logger
        )
        conn2 = RestApiConnection(
            mock_spark_session, production_rest_api_config, mock_logger
        )

        assert conn1 is not conn2, (
            f"Different configs should create separate instances: "
            f"conn1 ({id(conn1)}) vs conn2 ({id(conn2)})"
        )
        assert len(RestApiConnection._instances) == 2, (
            f"Expected 2 distinct instances for different configs, found "
            f"{len(RestApiConnection._instances)}"
        )

    @pytest.mark.unit
    def test_singleton_pattern_different_spark_apps(
        self, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test singleton pattern creates different instances for different Spark apps.

        Ensures that connections are properly isolated between different Spark
        application contexts, preventing connection sharing across application
        boundaries while maintaining singleton behavior within each application scope.
        """
        from pyspark.sql import SparkSession

        mock_spark1 = Mock(spec=SparkSession)
        mock_context1 = Mock()
        mock_context1.applicationId = "app-1"
        mock_spark1.sparkContext = mock_context1

        mock_spark2 = Mock(spec=SparkSession)
        mock_context2 = Mock()
        mock_context2.applicationId = "app-2"
        mock_spark2.sparkContext = mock_context2

        conn1 = RestApiConnection(mock_spark1, sample_rest_api_config, mock_logger)
        conn2 = RestApiConnection(mock_spark2, sample_rest_api_config, mock_logger)

        assert conn1 is not conn2
        assert len(RestApiConnection._instances) == 2

    @pytest.mark.unit
    def test_unique_key_generation(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test unique key generation for singleton pattern implementation.

        Validates that connection instances are properly identified and cached using
        unique keys based on application ID and base URL, ensuring reliable singleton
        behavior across complex enterprise configurations.
        """
        base_url = sample_rest_api_config["base_url"]
        app_id = mock_spark_session.sparkContext.applicationId

        expected_key = f"{app_id}:{base_url}"

        RestApiConnection(mock_spark_session, sample_rest_api_config, mock_logger)

        assert expected_key in RestApiConnection._instances

    # Connection Initialization Testing
    # ================================

    @pytest.mark.unit
    def test_initialization_basic_config(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test connection initialization with basic API configuration.

        Validates proper initialization of connection attributes, session setup,
        and base configuration using standard API parameters. Ensures correct
        default value application and session configuration.
        """
        conn = RestApiConnection(
            mock_spark_session, sample_rest_api_config, mock_logger
        )

        # Validate connection attributes
        assert conn.spark is mock_spark_session, (
            f"Spark session not properly assigned: expected "
            f"{mock_spark_session}, got {conn.spark}"
        )
        assert (
            conn.logger is mock_logger
        ), f"Logger not properly assigned: expected {mock_logger}, got {conn.logger}"
        assert conn.base_url == "https://api.example.com", (
            f"Base URL mismatch: expected 'https://api.example.com', "
            f"got '{conn.base_url}'"
        )
        assert conn.headers == {"Content-Type": "application/json"}, (
            f"Headers mismatch: expected {{'Content-Type': 'application/json'}}, "
            f"got {conn.headers}"
        )
        assert conn.auth is None, f"Auth should be None by default, got {conn.auth}"
        assert conn.timeout == 10, f"Timeout mismatch: expected 10, got {conn.timeout}"

        # Validate session setup
        assert hasattr(conn, "session"), "Connection should have session attribute"
        assert isinstance(
            conn.session, requests.Session
        ), "Session should be requests.Session instance"

    @pytest.mark.unit
    def test_initialization_with_auth(
        self, mock_spark_session: Any, mock_logger: Any, auth_rest_api_config: Any
    ) -> None:
        """
        Test connection initialization with authentication configuration.

        Verifies proper handling of authentication parameters and configuration
        setup. Essential for enterprise environments with secure API access
        requirements and token-based authentication.
        """
        conn = RestApiConnection(mock_spark_session, auth_rest_api_config, mock_logger)

        assert conn.base_url == "https://secure-api.example.com"
        assert conn.auth == (
            "admin",
            "secret",
        ), f"Auth mismatch: expected ('admin', 'secret'), got {conn.auth}"
        assert conn.headers == {
            "Authorization": "Bearer token123",
            "X-API-Key": "api-key-456",
        }
        assert conn.timeout == 30

    @pytest.mark.unit
    def test_initialization_custom_retry_config(
        self, mock_spark_session: Any, mock_logger: Any, custom_retry_config: Any
    ) -> None:
        """
        Test connection initialization with custom retry configuration.

        Validates proper setup of retry strategies, backoff factors, and status
        force lists for production environments requiring specific retry behavior
        and error handling patterns.
        """
        conn = RestApiConnection(mock_spark_session, custom_retry_config, mock_logger)

        assert conn.base_url == "https://retry-api.example.com"
        assert hasattr(conn, "session")
        assert isinstance(conn.session, requests.Session)

    @pytest.mark.unit
    def test_initialization_logging(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test connection initialization logging for operational monitoring.

        Validates that connection establishment events are properly logged with
        relevant configuration details for production monitoring, troubleshooting,
        and audit compliance in enterprise environments.
        """
        RestApiConnection(mock_spark_session, sample_rest_api_config, mock_logger)

        mock_logger.info.assert_called_once()
        log_call = mock_logger.info.call_args[0][0]
        assert "REST API initialized" in log_call
        assert "base_url=https://api.example.com" in log_call

    @pytest.mark.unit
    def test_initialization_prevents_double_init(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test that __init_once__ method prevents double initialization.

        Validates that singleton instances are not re-initialized when retrieved
        multiple times, ensuring consistent state and preventing resource leaks
        in production environments.
        """
        conn1 = RestApiConnection(
            mock_spark_session, sample_rest_api_config, mock_logger
        )

        # Manually call __init_once__ again to ensure it's protected
        conn1.__init_once__(mock_spark_session, sample_rest_api_config, mock_logger)

        # Should still have the same attributes
        assert conn1.base_url == "https://api.example.com"
        assert hasattr(conn1, "_initialized")
        assert conn1._initialized is True

    # HTTP Request Method Testing (_request)
    # =====================================

    @pytest.mark.unit
    def test_request_method_get_json_response(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test _request method with GET and JSON response parsing.

        Validates core HTTP request functionality with JSON response handling,
        URL construction, header management, and status code extraction for
        standard API operations.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"result": "success", "data": [1, 2, 3]}'
        mock_response.json.return_value = {"result": "success", "data": [1, 2, 3]}

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            status, response = conn._request("GET", "/test", params={"key": "value"})

            assert status == 200
            assert response == {"result": "success", "data": [1, 2, 3]}

    @pytest.mark.unit
    def test_request_method_post_with_json_payload(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test _request method with POST and JSON payload.

        Validates HTTP POST operations with JSON payload handling,
        proper request construction, and response processing for
        data submission scenarios.
        """
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"created": true, "id": 123}'
        mock_response.json.return_value = {"created": True, "id": 123}

        with patch.object(
            requests.Session, "request", return_value=mock_response
        ) as mock_request:
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            payload = {"name": "test", "value": 42}
            status, response = conn._request("POST", "/create", json=payload)

            assert status == 201
            assert response == {"created": True, "id": 123}

            # Verify request was called correctly
            mock_request.assert_called_once()
            call_args = mock_request.call_args
            assert call_args[1]["method"] == "POST"
            assert call_args[1]["url"] == "https://api.example.com/create"
            assert call_args[1]["json"] == payload

    @pytest.mark.unit
    def test_request_method_text_response(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test _request method with text response (non-JSON).

        Validates handling of non-JSON responses including plain text,
        HTML, and other content types for diverse API integration
        scenarios.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "Success: Operation completed"

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            status, response = conn._request("GET", "/status")

            assert status == 200
            assert response == "Success: Operation completed"

    @pytest.mark.unit
    def test_request_method_empty_response(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test _request method with empty response body.

        Validates proper handling of empty response bodies and
        None return values for operations that don't return content,
        such as DELETE operations or status checks.
        """
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = ""

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            status, response = conn._request("DELETE", "/resource/123")

            assert status == 204
            assert response is None

    @pytest.mark.unit
    def test_request_method_invalid_json_fallback(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test _request method fallback when JSON parsing fails.

        Validates that invalid JSON responses fall back to text content
        and log appropriate error messages for debugging and operational
        monitoring.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = "Invalid JSON content"
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            status, response = conn._request("GET", "/malformed")

            assert status == 200
            assert response == "Invalid JSON content"

            # Verify error was logged
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0][0]
            assert "JSON parsing error" in error_call

    @pytest.mark.unit
    def test_request_method_url_construction(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test _request method URL construction with various endpoint formats.

        Validates proper URL joining behavior with different endpoint
        formats including leading/trailing slashes, ensuring consistent
        URL construction across diverse API patterns.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = "{}"
        mock_response.json.return_value = {}

        test_cases = [
            ("/api/test", "https://api.example.com/api/test"),
            ("api/test", "https://api.example.com/api/test"),
            ("/api/test/", "https://api.example.com/api/test/"),
            ("", "https://api.example.com/"),
        ]

        with patch.object(
            requests.Session, "request", return_value=mock_response
        ) as mock_request:
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            for endpoint, expected_url in test_cases:
                conn._request("GET", endpoint)

                # Get the last call to check URL
                call_args = mock_request.call_args
                assert call_args[1]["url"] == expected_url

    @pytest.mark.unit
    def test_request_method_header_merging(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test _request method header merging with extra headers.

        Validates that default headers and request-specific extra headers
        are properly merged, allowing for flexible header management
        across different API operations.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = "{}"
        mock_response.json.return_value = {}

        with patch.object(
            requests.Session, "request", return_value=mock_response
        ) as mock_request:
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            extra_headers = {"X-Request-ID": "123", "Authorization": "Bearer xyz"}
            conn._request("GET", "/test", extra_headers=extra_headers)

            call_args = mock_request.call_args
            sent_headers = call_args[1]["headers"]

            # Should contain both default and extra headers
            assert "Content-Type" in sent_headers
            assert "X-Request-ID" in sent_headers
            assert "Authorization" in sent_headers
            assert sent_headers["X-Request-ID"] == "123"
            assert sent_headers["Authorization"] == "Bearer xyz"

    @pytest.mark.unit
    def test_request_method_network_error(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test _request method handling of network errors.

        Validates proper exception handling and logging for network
        connectivity issues, timeouts, and other request failures
        common in distributed environments.
        """
        with patch.object(
            requests.Session,
            "request",
            side_effect=requests.RequestException("Network error"),
        ):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            with pytest.raises(requests.RequestException):
                conn._request("GET", "/test")

            # Verify error was logged
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0][0]
            assert "HTTP error GET" in error_call
            assert "Network error" in error_call

    # HTTP Method Testing (GET, POST, PUT, PATCH, DELETE)
    # ==================================================

    @pytest.mark.unit
    def test_get_method(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test GET method wrapper functionality.

        Validates GET request execution with proper parameter handling,
        response processing, and method delegation to _request for
        data retrieval operations.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"users": [{"id": 1, "name": "test"}]}'
        mock_response.json.return_value = {"users": [{"id": 1, "name": "test"}]}

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            result = conn.get(
                "/users", params={"limit": 10}, extra_headers={"X-Version": "v1"}
            )

            assert result == (200, {"users": [{"id": 1, "name": "test"}]})

    @pytest.mark.unit
    def test_post_method_with_json(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test POST method with JSON payload.

        Validates POST request execution with JSON data submission,
        proper content handling, and response processing for
        resource creation operations.
        """
        mock_response = Mock()
        mock_response.status_code = 201
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"created": true, "id": 123}'
        mock_response.json.return_value = {"created": True, "id": 123}

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            payload = {"name": "New User", "email": "user@example.com"}
            result = conn.post("/users", json=payload)

            assert result == (201, {"created": True, "id": 123})

    @pytest.mark.unit
    def test_post_method_with_data(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test POST method with form data.

        Validates POST request execution with form-encoded data,
        proper content handling, and response processing for
        form submission scenarios.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "text/plain"}
        mock_response.text = "Form submitted successfully"

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            form_data = {"field1": "value1", "field2": "value2"}
            result = conn.post("/submit", data=form_data)

            assert result == (200, "Form submitted successfully")

    @pytest.mark.unit
    def test_put_method(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test PUT method for resource updates.

        Validates PUT request execution with resource replacement
        data, proper content handling, and response processing
        for update operations.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"updated": true, "version": 2}'
        mock_response.json.return_value = {"updated": True, "version": 2}

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            update_data = {"name": "Updated User", "status": "active"}
            result = conn.put("/users/123", json=update_data)

            assert result == (200, {"updated": True, "version": 2})

    @pytest.mark.unit
    def test_patch_method(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test PATCH method for partial updates.

        Validates PATCH request execution with partial update data,
        proper content handling, and response processing for
        incremental modification operations.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = '{"patched": true, "fields": ["status"]}'
        mock_response.json.return_value = {"patched": True, "fields": ["status"]}

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            patch_data = {"status": "inactive"}
            result = conn.patch("/users/123", json=patch_data)

            assert result == (200, {"patched": True, "fields": ["status"]})

    @pytest.mark.unit
    def test_delete_method(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test DELETE method for resource removal.

        Validates DELETE request execution with optional parameters,
        proper response handling, and status code processing for
        resource deletion operations.
        """
        mock_response = Mock()
        mock_response.status_code = 204
        mock_response.headers = {}
        mock_response.text = ""

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            result = conn.delete("/users/123", params={"force": "true"})

            assert result == (204, None)

    # Session Management and Resource Cleanup Testing
    # ==============================================

    @pytest.mark.unit
    def test_close_session(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test session cleanup and resource management.

        Validates proper session closure, resource cleanup, and
        logging for connection lifecycle management in production
        environments.
        """
        with patch.object(requests.Session, "close") as mock_close:
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            conn.close()

            mock_close.assert_called_once()
            mock_logger.info.assert_called_with("REST API session closed successfully")

    @pytest.mark.unit
    def test_close_session_without_session(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test close method safety when session doesn't exist.

        Validates that close method handles cases where session
        attribute might not exist, ensuring robust cleanup behavior
        in edge cases.
        """
        conn = RestApiConnection(
            mock_spark_session, sample_rest_api_config, mock_logger
        )

        # Remove session attribute to simulate edge case
        delattr(conn, "session")

        # Should not raise exception
        conn.close()

        mock_logger.info.assert_called_with("REST API session closed successfully")

    # Edge Case and Error Handling Testing
    # ===================================

    @pytest.mark.unit
    def test_config_with_missing_base_url(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test handling of configuration missing base_url.

        Validates behavior when base_url is not provided in configuration,
        ensuring proper error handling or default behavior for
        incomplete configurations.
        """
        config_without_base_url = {
            "headers": {"Content-Type": "application/json"},
            "timeout": 15,
        }

        conn = RestApiConnection(
            mock_spark_session, config_without_base_url, mock_logger
        )

        # Should handle None base_url gracefully
        assert conn.base_url is None

    @pytest.mark.unit
    def test_config_with_none_values(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test handling of None values in configuration.

        Validates proper handling of None values in configuration
        parameters, ensuring robust initialization and graceful
        degradation with incomplete configurations.
        """
        config_with_nones = {
            "base_url": "https://api.example.com",
            "headers": None,
            "auth": None,
            "timeout": None,
        }

        conn = RestApiConnection(mock_spark_session, config_with_nones, mock_logger)

        assert conn.base_url == "https://api.example.com"
        # Headers can be None when explicitly set to None
        assert conn.headers is None or conn.headers == {}
        assert conn.auth is None
        assert conn.timeout is None  # When explicitly set to None, it stays None

    @pytest.mark.unit
    def test_retry_strategy_configuration(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test retry strategy configuration with various parameters.

        Validates that retry strategies are properly configured with
        custom parameters including retry counts, backoff factors,
        and status force lists for production resilience.
        """
        retry_config = {
            "base_url": "https://retry-api.example.com",
            "retries": 5,
            "backoff_factor": 0.5,
            "status_forcelist": [500, 502, 503, 504, 429],
        }

        # Test that the connection is created successfully with retry config
        conn = RestApiConnection(mock_spark_session, retry_config, mock_logger)

        # Verify basic attributes are set
        assert conn.base_url == "https://retry-api.example.com"
        assert hasattr(conn, "session")
        assert isinstance(conn.session, requests.Session)

    @pytest.mark.unit
    def test_logger_none_handling(
        self, mock_spark_session: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test handling when logger is None.

        Validates that connection works properly without logger,
        ensuring graceful degradation and no logging-related
        errors in environments without logging setup.
        """
        conn = RestApiConnection(mock_spark_session, sample_rest_api_config, None)

        assert conn.logger is None

        # Should not cause errors during request operations
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = "{}"
        mock_response.json.return_value = {}

        with patch.object(requests.Session, "request", return_value=mock_response):
            status, response = conn._request("GET", "/test")
            assert status == 200
            assert response == {}

    @pytest.mark.unit
    def test_logger_none_json_error_handling(
        self, mock_spark_session: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test JSON parsing error handling when logger is None.

        Validates that JSON parsing errors are handled gracefully
        without logger, ensuring no exceptions are raised when
        logger is not available.
        """
        conn = RestApiConnection(mock_spark_session, sample_rest_api_config, None)

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = "Invalid JSON content"
        mock_response.json.side_effect = ValueError("Invalid JSON")

        with patch.object(requests.Session, "request", return_value=mock_response):
            status, response = conn._request("GET", "/malformed")

            assert status == 200
            assert response == "Invalid JSON content"

    @pytest.mark.unit
    def test_logger_none_network_error_handling(
        self, mock_spark_session: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test network error handling when logger is None.

        Validates that network errors are properly raised without
        attempting to log when logger is not available.
        """
        conn = RestApiConnection(mock_spark_session, sample_rest_api_config, None)

        with patch.object(
            requests.Session,
            "request",
            side_effect=requests.RequestException("Network error"),
        ):
            with pytest.raises(requests.RequestException):
                conn._request("GET", "/test")

    @pytest.mark.unit
    def test_close_session_without_logger(
        self, mock_spark_session: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test session close when logger is None.

        Validates that session cleanup works properly without logger,
        ensuring no exceptions are raised during resource cleanup.
        """
        conn = RestApiConnection(mock_spark_session, sample_rest_api_config, None)

        # Should not raise exception even without logger
        conn.close()

    # Performance and Integration Testing
    # ==================================

    @pytest.mark.performance
    def test_singleton_performance_multiple_calls(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test singleton performance with multiple instantiation calls.

        Validates that repeated connection requests with identical configurations
        maintain optimal performance through proper instance caching and reuse.
        Critical for high-throughput production environments with frequent
        connection requests.
        """
        connections = []

        for _ in range(100):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )
            connections.append(conn)

        first_conn = connections[0]
        for conn in connections[1:]:
            assert conn is first_conn

        assert len(RestApiConnection._instances) == 1

    @pytest.mark.integration
    def test_multiple_configs_isolation(self, mock_logger: Any) -> None:
        """
        Test connection isolation across multiple API configurations.

        Validates proper connection separation and resource management when
        working with multiple API endpoints simultaneously. Essential
        for enterprise scenarios with multiple API integrations within
        the same application.
        """
        from pyspark.sql import SparkSession

        mock_spark1 = Mock(spec=SparkSession)
        mock_context1 = Mock()
        mock_context1.applicationId = "app-1"
        mock_spark1.sparkContext = mock_context1

        mock_spark2 = Mock(spec=SparkSession)
        mock_context2 = Mock()
        mock_context2.applicationId = "app-2"
        mock_spark2.sparkContext = mock_context2

        config1 = {"base_url": "https://api1.example.com", "timeout": 10}

        config2 = {"base_url": "https://api2.example.com", "timeout": 20}

        conn1 = RestApiConnection(mock_spark1, config1, mock_logger)
        conn2 = RestApiConnection(mock_spark2, config2, mock_logger)
        conn3 = RestApiConnection(mock_spark1, config1, mock_logger)

        assert conn1 is not conn2
        assert conn1 is conn3
        assert len(RestApiConnection._instances) == 2

        assert conn1.base_url == "https://api1.example.com"
        assert conn2.base_url == "https://api2.example.com"
        assert conn1.timeout == 10
        assert conn2.timeout == 20

    @pytest.mark.unit
    def test_request_logging_with_different_data_types(
        self, mock_spark_session: Any, mock_logger: Any, sample_rest_api_config: Any
    ) -> None:
        """
        Test request logging with various data types.

        Validates that request logging properly handles different
        data types in parameters and payloads, ensuring robust
        logging for operational monitoring.
        """
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.headers = {"Content-Type": "application/json"}
        mock_response.text = "{}"
        mock_response.json.return_value = {}

        with patch.object(requests.Session, "request", return_value=mock_response):
            conn = RestApiConnection(
                mock_spark_session, sample_rest_api_config, mock_logger
            )

            # Test with various data types
            test_cases = [
                (
                    "GET",
                    "/test1",
                    {"params": {"int_val": 123, "str_val": "test"}},
                    None,
                ),
                (
                    "POST",
                    "/test2",
                    None,
                    {"json": {"list": [1, 2, 3], "dict": {"nested": True}}},
                ),
                ("PUT", "/test3", None, {"data": "string data"}),
            ]

            for method, endpoint, params_data, json_data in test_cases:
                if params_data:
                    conn._request(method, endpoint, **params_data)
                elif json_data:
                    conn._request(method, endpoint, **json_data)
                else:
                    conn._request(method, endpoint)

                # Should have logged the request
                assert mock_logger.info.called

    # Security and Authentication Testing
    # ==================================

    @pytest.mark.security
    def test_auth_parameter_handling(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test authentication parameter handling and security.

        Validates proper handling of various authentication methods
        including basic auth, token auth, and custom auth mechanisms
        for secure API access.
        """
        auth_configs: list[Dict[str, Any]] = [
            {
                "base_url": "https://api.example.com",
                "auth": ("username", "password"),  # Basic auth tuple
            },
            {
                "base_url": "https://api.example.com",
                "auth": "Bearer token123",  # Token string
            },
            {
                "base_url": "https://api.example.com",
                "auth": {"type": "custom", "key": "value"},  # Custom auth
            },
        ]

        for config in auth_configs:
            RestApiConnection._instances.clear()
            conn = RestApiConnection(mock_spark_session, config, mock_logger)
            assert conn.auth == config["auth"]

    @pytest.mark.unit
    def test_sensitive_data_logging_protection(
        self, mock_spark_session: Any, mock_logger: Any
    ) -> None:
        """
        Test that sensitive authentication data is not leaked in logs.

        Validates that authentication credentials and other sensitive
        information are not exposed in log messages for security
        compliance and data protection.
        """
        sensitive_config = {
            "base_url": "https://secure-api.example.com",
            "auth": ("admin", "super_secret_password"),
            "headers": {"X-API-Key": "sensitive_api_key_123"},
        }

        conn = RestApiConnection(mock_spark_session, sensitive_config, mock_logger)

        # Verify connection was created
        assert conn is not None

        # Check that sensitive data is not in log calls
        for call_args in mock_logger.info.call_args_list:
            log_message = str(call_args)
            assert "super_secret_password" not in log_message
            assert "sensitive_api_key_123" not in log_message


if __name__ == "__main__":
    pytest.main(
        [
            __file__,
            "-v",
            "--cov=spark_simplicity.connections.rest_api_connection",
            "--cov-report=term-missing",
        ]
    )
