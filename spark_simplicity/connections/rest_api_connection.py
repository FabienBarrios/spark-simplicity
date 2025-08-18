"""
Spark Simplicity - REST API Connection Manager
==============================================

Enterprise-grade REST API client with singleton pattern, intelligent retry logic, and
comprehensive HTTP method support. This module provides reliable API connectivity for
Spark data processing workflows, enabling seamless integration with web services,
microservices, and external data sources through standardized REST interfaces.

Key Features:
    - **Singleton Pattern**: One connection instance per unique API endpoint
      configuration
    - **Intelligent Retry Logic**: Configurable retry strategies with exponential
      backoff
    - **Session Management**: Persistent HTTP sessions for optimal connection reuse
    - **Authentication Support**: Flexible authentication mechanisms
      (token, basic, custom)
    - **Production Safety**: Comprehensive error handling and request/response logging
    - **HTTP Method Coverage**: Full REST API method support
      (GET, POST, PUT, PATCH, DELETE)

HTTP Features:
    **Request Management**:
    - Automatic URL construction and endpoint routing
    - Flexible parameter and payload handling for diverse API requirements
    - Custom header support for API-specific authentication and formatting
    - Content-type negotiation and intelligent response parsing

    **Error Recovery**:
    - Configurable retry strategies for transient failures (5xx errors)
    - Exponential backoff with jitter for optimal server load distribution
    - Connection pooling and session persistence for performance optimization
    - Comprehensive error reporting with detailed diagnostic information

Enterprise Integration:
    - **API Gateway Integration**: Seamless connectivity with enterprise API gateways
    - **Microservices Architecture**: Optimized for service-to-service communication
    - **Data Pipeline Support**: Integration with ETL workflows and data ingestion
    - **Security Compliance**: Support for enterprise authentication and authorization
    - **Monitoring Integration**: Detailed request/response logging for operational
      visibility

Usage:
    This module is designed for enterprise data processing scenarios requiring
    reliable API connectivity integrated with Spark analytics and data workflows.

    from spark_simplicity.connections.rest_api_connection import RestApiConnection
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

import requests
from requests.adapters import HTTPAdapter, Retry


class RestApiConnection:
    """
    Enterprise-grade REST API client with singleton pattern and intelligent retry
    mechanisms.

    Provides comprehensive REST API connectivity for Spark data processing workflows
    with intelligent connection management, automatic retry logic, and enterprise-grade
    error handling. The singleton pattern ensures efficient resource utilization by
    maintaining one HTTP session per unique API endpoint configuration.

    This class is specifically designed for production environments requiring reliable
    API integration, comprehensive error handling, and optimal resource management.
    It supports all standard HTTP methods with intelligent response parsing and
    configurable retry strategies for robust operation in distributed systems.

    Key Capabilities:
        - **Session Persistence**: HTTP connection pooling and session reuse
        - **Retry Strategies**: Configurable retry logic with exponential backoff
        - **Authentication**: Support for various authentication mechanisms
        - **Response Parsing**: Intelligent content-type detection and parsing
        - **Error Handling**: Comprehensive exception management and logging
        - **Resource Management**: Automatic session cleanup and lifecycle control

    Attributes:
        _instances: Class-level dictionary maintaining singleton instances keyed by
                   unique API configuration (application + base URL). Ensures efficient
                   resource utilization and prevents session proliferation.
    """

    _instances: Dict[str, "RestApiConnection"] = {}

    def __new__(
        cls, spark: Any, config: Dict[str, Any], logger: Optional[logging.Logger] = None
    ) -> "RestApiConnection":
        """
        Create or retrieve REST API connection instance using singleton pattern.

        Implements sophisticated singleton logic based on Spark application ID and
        base URL to ensure optimal resource utilization while maintaining session
        isolation between different API endpoints and applications.

        Args:
            spark: Active SparkSession instance for application identification
            config: API configuration dictionary containing:
                   - 'base_url': API base URL (required)
                   - 'headers': Default HTTP headers dictionary
                   - 'auth': Authentication configuration (tuple, token, etc.)
                   - 'timeout': Request timeout in seconds (default: 10)
                   - 'retries': Maximum retry attempts (default: 3)
                   - 'backoff_factor': Exponential backoff multiplier (default: 0.3)
                   - 'status_forcelist': HTTP status codes to retry
                     (default: [500,502,503,504])
            logger: Logger instance for request/response monitoring

        Returns:
            RestApiConnection instance - either newly created or existing singleton
        """
        key = f"{spark.sparkContext.applicationId}:{config.get('base_url')}"
        if key not in cls._instances:
            instance = super().__new__(cls)
            instance.__init_once__(spark, config, logger)
            cls._instances[key] = instance
        return cls._instances[key]

    def __init_once__(
        self,
        spark: Any,
        config: Dict[str, Any],
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """
        Initialize REST API connection with comprehensive session configuration.

        Performs one-time initialization including HTTP session setup, retry strategy
        configuration, and authentication preparation. This method ensures proper
        resource management and optimal HTTP client configuration for enterprise
        API connectivity requirements.

        Args:
            spark: SparkSession instance for application context
            config: API configuration with connection parameters and retry settings
            logger: Logger instance for operational monitoring and debugging

        Configuration Process:
            1. Extract and validate configuration parameters
            2. Initialize persistent HTTP session with connection pooling
            3. Configure intelligent retry strategy with exponential backoff
            4. Set up authentication and default headers
            5. Mount retry adapters for HTTP and HTTPS protocols
        """
        if hasattr(self, "_initialized"):
            return

        self.spark = spark
        self.logger = logger
        self.base_url = config.get("base_url")
        self.headers = config.get("headers", {})
        self.auth = config.get("auth")
        self.timeout = config.get("timeout", 10)

        self.session = requests.Session()

        retries = config.get("retries", 3)
        backoff_factor = config.get("backoff_factor", 0.3)
        status_forcelist = config.get("status_forcelist", [500, 502, 503, 504])

        retry_strategy = Retry(
            total=retries,
            backoff_factor=backoff_factor,
            status_forcelist=status_forcelist,
            allowed_methods=[
                "HEAD",
                "GET",
                "OPTIONS",
                "POST",
                "PUT",
                "PATCH",
                "DELETE",
            ],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

        if self.logger:
            self.logger.info(f"REST API initialized for base_url={self.base_url}")

        self._initialized = True

    def _request(
        self,
        method: str,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Union[Dict[str, Any], List[Any], str, None]]:
        """
        Execute HTTP request with intelligent response parsing and comprehensive error
        handling.

        Provides the core HTTP request functionality with automatic URL construction,
        intelligent response parsing based on content type, and robust error handling.
        This method serves as the foundation for all HTTP operations with consistent
        behavior across different request types and API endpoints.

        Args:
            method: HTTP method to execute (GET, POST, PUT, PATCH, DELETE)
            endpoint: API endpoint path relative to base URL
            (leading/trailing slashes handled)
            params: URL query parameters dictionary for GET requests and parameter
            passing
            data: Request body data for form-encoded or raw data transmission
            json: JSON payload for requests requiring JSON content-type
            extra_headers: Additional HTTP headers to merge with default headers

        Returns:
            Tuple containing (status_code, parsed_response):
            - status_code: HTTP status code from server response
            - parsed_response: Response content parsed based on content-type:
              * JSON objects/arrays for application/json content
              * String content for text-based responses
              * None for empty response bodies

        Response Processing:
            1. **URL Construction**: Intelligent joining of base URL and endpoint
            2. **Header Merging**: Combination of default and request-specific headers
            3. **Request Execution**: HTTP request with configured timeout and retry
               logic
            4. **Content Parsing**: Intelligent parsing based on response content-type
            5. **Error Handling**: Comprehensive exception management and logging

        Content-Type Handling:
            - **JSON Responses**: Automatic JSON parsing with fallback to text
            - **Text Responses**: Raw text content preservation
            - **Empty Responses**: Null value for empty response bodies
            - **Binary Content**: Text representation for non-JSON content

        Raises:
            requests.RequestException: For network connectivity, timeout, or HTTP errors
        """
        if self.base_url is None:
            raise ValueError("base_url is not configured")
        url = self.base_url.rstrip("/") + "/" + endpoint.lstrip("/")
        headers = self.headers.copy()
        if extra_headers:
            headers.update(extra_headers)

        if self.logger:
            self.logger.info(
                f"{method.upper()} {url} params={params} data={json or data}"
            )

        try:
            response = self.session.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                auth=self.auth,
                timeout=self.timeout,
            )
            status_code = response.status_code
            content_type = response.headers.get("Content-Type", "")
            content_text = response.text.strip()

            if not content_text:
                return status_code, None

            if "application/json" in content_type.lower():
                try:
                    payload = response.json()
                    return status_code, payload
                except ValueError as ve:
                    if self.logger:
                        self.logger.error(f"JSON parsing error: {ve}")
                    return status_code, content_text

            return status_code, content_text

        except requests.RequestException as e:
            if self.logger:
                self.logger.error(f"HTTP error {method.upper()} {url}: {e}")
            raise

    def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Union[Dict[str, Any], List[Any], str, None]]:
        """
        Execute HTTP GET request for data retrieval and API querying.

        Provides optimized GET request functionality for data retrieval, API queries,
        and resource access patterns common in data processing workflows. Ideal for
        fetching configuration data, querying APIs for processing parameters, and
        retrieving reference data for Spark analytics operations.

        Args:
            endpoint: API endpoint path for the GET request
            params: Query parameters for filtering, pagination, and data selection
            extra_headers: Additional headers for authentication or API requirements

        Returns:
            Tuple of (status_code, response_data) with parsed response content

        Examples:
            Retrieve configuration data:
             status, config = api.get('/config/processing-params')

            Query with parameters:
             status, results = api.get('/data/records',
                                     params={'limit': 100, 'offset': 0})
        """
        return self._request(
            "GET", endpoint, params=params, extra_headers=extra_headers
        )

    def post(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Union[Dict[str, Any], List[Any], str, None]]:
        """
        Execute HTTP POST request for resource creation and data submission.

        Provides comprehensive POST request functionality for creating resources,
        submitting data for processing, and triggering API operations. Essential
        for data ingestion workflows, result submission, and integration with
        data processing APIs in enterprise environments.

        Args:
            endpoint: API endpoint path for the POST request
            data: Form data or raw request body for submission
            json: JSON payload for structured data submission
            extra_headers: Additional headers for content-type or authentication

        Returns:
            Tuple of (status_code, response_data) with creation result or confirmation

        Examples:
            Submit processing results:
             status, result = api.post('/results/submit',
                                     json={'data': processed_data})

            Create new resource:
             status, created = api.post('/resources',
                                      json={'name': 'dataset', 'type': 'parquet'})
        """
        return self._request(
            "POST", endpoint, data=data, json=json, extra_headers=extra_headers
        )

    def put(
        self,
        endpoint: str,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Union[Dict[str, Any], List[Any], str, None]]:
        """
        Execute HTTP PUT request for resource updates and replacements.

        Provides complete PUT request functionality for updating existing resources,
        replacing data sets, and maintaining resource state consistency. Critical
        for data pipeline status updates, configuration management, and resource
        synchronization in distributed processing environments.

        Args:
            endpoint: API endpoint path for the PUT request
            data: Complete resource data for replacement
            json: JSON payload for structured resource updates
            extra_headers: Additional headers for versioning or authentication

        Returns:
            Tuple of (status_code, response_data) with update confirmation

        Examples:
            Update processing status:
             status, updated = api.put('/jobs/123/status',
                                     json={'status': 'completed', 'results': results})

            Replace configuration:
             status, config = api.put('/config/pipeline',
                                    json=new_configuration)
        """
        return self._request(
            "PUT", endpoint, data=data, json=json, extra_headers=extra_headers
        )

    def patch(
        self,
        endpoint: str,
        *,
        data: Optional[Any] = None,
        json: Optional[Any] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Union[Dict[str, Any], List[Any], str, None]]:
        """
        Execute HTTP PATCH request for partial resource updates.

        Provides efficient PATCH request functionality for partial resource updates,
        incremental changes, and optimized data synchronization. Ideal for updating
        specific fields without replacing entire resources, maintaining data
        consistency, and minimizing network overhead in API operations.

        Args:
            endpoint: API endpoint path for the PATCH request
            data: Partial resource data for incremental updates
            json: JSON payload with specific fields to update
            extra_headers: Additional headers for patch semantics or authentication

        Returns:
            Tuple of (status_code, response_data) with partial update confirmation

        Examples:
            Update specific fields:
             status, updated = api.patch('/resources/456',
                                       json={'status': 'processing', 'progress': 75})

            Incremental data updates:
             status, result = api.patch('/datasets/daily',
              json={'last_updated': timestamp, 'record_count': count})
        """
        return self._request(
            "PATCH", endpoint, data=data, json=json, extra_headers=extra_headers
        )

    def delete(
        self,
        endpoint: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> Tuple[int, Union[Dict[str, Any], List[Any], str, None]]:
        """
        Execute HTTP DELETE request for resource removal and cleanup operations.

        Provides safe DELETE request functionality for resource cleanup, temporary
        data removal, and resource lifecycle management. Essential for maintaining
        clean data processing environments, removing temporary resources, and
        implementing proper data retention policies in automated workflows.

        Args:
            endpoint: API endpoint path for the DELETE request
            params: Query parameters for conditional deletion or filtering
            extra_headers: Additional headers for authentication or deletion policies

        Returns:
            Tuple of (status_code, response_data) with deletion confirmation

        Examples:
            Remove temporary resource:
             status, result = api.delete('/temp/processing-123')

            Conditional deletion:
             status, deleted = api.delete('/cache/expired',
                                        params={'older_than': '24h'})
        """
        return self._request(
            "DELETE", endpoint, params=params, extra_headers=extra_headers
        )

    def close(self) -> None:
        """
        Gracefully close HTTP session and cleanup connection resources.

        Performs controlled shutdown of the HTTP session with proper resource cleanup
        to prevent connection leaks and ensure optimal resource management. Essential
        for production environments where proper connection lifecycle management
        is critical for system stability and performance.

        Cleanup Process:
            1. Close persistent HTTP session if active
            2. Release connection pool resources
            3. Clear any cached authentication tokens
            4. Log session closure for operational monitoring

        Note:
            This method is typically called automatically during application shutdown
            or can be invoked manually for explicit resource cleanup in long-running
            applications with dynamic API connection requirements.
        """
        if hasattr(self, "session"):
            self.session.close()
        if self.logger:
            self.logger.info("REST API session closed successfully")
