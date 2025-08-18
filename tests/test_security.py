"""
Security and validation tests.

Tests for security vulnerabilities, input validation,
and secure coding practices.
"""

import threading
import time
from unittest.mock import Mock

from spark_simplicity.connections.database_connection import JdbcSqlServerConnection


class TestSecurityValidation:
    """Security-focused tests for database connections."""

    def setup_method(self):
        """Clear singleton instances before each test."""
        JdbcSqlServerConnection._instances.clear()

    def test_sql_injection_patterns_in_config(self):
        """Test that malicious SQL patterns in config don't break security."""
        # Test various SQL injection patterns
        malicious_inputs = [
            "'; DROP TABLE users; --",
            "admin'--",
            "1' OR '1'='1",
            "'; EXEC xp_cmdshell('dir'); --",
            "admin'; WAITFOR DELAY '00:00:05'--",
        ]

        for i, malicious_input in enumerate(malicious_inputs):
            # Clear instances and use unique app_id for each test
            JdbcSqlServerConnection._instances.clear()

            mock_spark = Mock()
            mock_spark.sparkContext.applicationId = f"security-test-{i}"
            mock_logger = Mock()

            config = {
                "host": f"localhost-{i}",  # Make host unique too
                "database": f"testdb-{i}",  # Make database unique too
                "user": malicious_input,  # Malicious user input
                "password": "testpass",
            }

            # Should not raise any exceptions
            conn = JdbcSqlServerConnection(mock_spark, config, mock_logger)

            # Values should be preserved as-is (not executed)
            assert conn.user == malicious_input
            assert malicious_input in str(conn.base_options)

    def test_password_not_logged_in_plain_text(self):
        """Ensure passwords are not exposed in logs."""
        mock_spark = Mock()
        mock_spark.sparkContext.applicationId = "password-test"
        mock_logger = Mock()

        config = {
            "host": "localhost",
            "database": "testdb",
            "user": "testuser",
            "password": "super_secret_password_123!",
        }

        JdbcSqlServerConnection(mock_spark, config, mock_logger)

        # Check that password is not in log messages
        mock_logger.info.assert_called()
        log_message = mock_logger.info.call_args[0][0]

        # Password should NOT appear in logs
        assert "super_secret_password_123!" not in log_message

        # But other info should be there
        assert "localhost" in log_message
        assert "testdb" in log_message
        assert "testuser" in log_message

    def test_connection_string_escaping(self):
        """Test that special characters in connection parameters are handled safely."""
        mock_spark = Mock()
        mock_spark.sparkContext.applicationId = "escaping-test"
        mock_logger = Mock()

        # Test special characters that could break connection strings
        special_chars_config = {
            "host": "test;host=malicious.com",  # Semicolon injection attempt
            "database": "test_db;InitialCatalog=master",  # Parameter injection
            "user": "test&user",  # Ampersand
            "password": "pass;word",  # Semicolon in password
        }

        conn = JdbcSqlServerConnection(mock_spark, special_chars_config, mock_logger)

        # Values should be preserved
        assert conn.host == "test;host=malicious.com"
        assert conn.database == "test_db;InitialCatalog=master"
        assert conn.user == "test&user"
        assert conn.password == "pass;word"

        # JDBC URL should still be valid format
        assert "jdbc:sqlserver://" in conn.jdbc_url
        assert "databaseName=" in conn.jdbc_url

    def test_long_input_handling(self):
        """Test handling of extremely long inputs (DoS prevention)."""
        mock_spark = Mock()
        mock_spark.sparkContext.applicationId = "dos-test"
        mock_logger = Mock()

        # Create very long strings
        long_host = "a" * 10000
        long_database = "b" * 10000
        long_user = "c" * 10000
        long_password = "d" * 10000

        config = {
            "host": long_host,
            "database": long_database,
            "user": long_user,
            "password": long_password,
        }

        # Should handle long inputs without crashing
        conn = JdbcSqlServerConnection(mock_spark, config, mock_logger)

        # Values should be preserved
        assert conn.host == long_host
        assert conn.database == long_database
        assert conn.user == long_user
        assert conn.password == long_password

    def test_unicode_and_encoding_handling(self):
        """Test handling of Unicode characters and different encodings."""
        mock_spark = Mock()
        mock_spark.sparkContext.applicationId = "unicode-test"
        mock_logger = Mock()

        unicode_config = {
            "host": "测试服务器.example.com",  # Chinese characters
            "database": "тестовая_база_данных",  # Cyrillic
            "user": "usuário_teste",  # Portuguese with accents
            "password": "пароль🔒密码",  # Mixed scripts with emoji
        }

        # Should handle Unicode without issues
        conn = JdbcSqlServerConnection(mock_spark, unicode_config, mock_logger)

        # Values should be preserved correctly
        assert conn.host == "测试服务器.example.com"
        assert conn.database == "тестовая_база_данных"
        assert conn.user == "usuário_teste"
        assert conn.password == "пароль🔒密码"

    def test_empty_and_none_values_handling(self):
        """Test handling of empty strings and None values."""
        mock_spark = Mock()
        mock_spark.sparkContext.applicationId = "empty-test"
        mock_logger = Mock()

        # Test with empty strings (should work)
        empty_config = {"host": "", "database": "", "user": "", "password": ""}

        conn = JdbcSqlServerConnection(mock_spark, empty_config, mock_logger)
        assert conn.host == ""
        assert conn.database == ""
        assert conn.user == ""
        assert conn.password == ""

    def test_concurrent_connection_creation_thread_safety(self):
        """Test thread safety of singleton pattern under concurrent access."""

        mock_spark = Mock()
        mock_spark.sparkContext.applicationId = "thread-safety-test"
        mock_logger = Mock()

        config = {
            "host": "localhost",
            "database": "testdb",
            "user": "testuser",
            "password": "testpass",
        }

        connections = []

        def create_connection():
            """Create connection in thread."""
            time.sleep(0.001)  # Small delay to increase chance of race condition
            connec = JdbcSqlServerConnection(mock_spark, config, mock_logger)
            connections.append(connec)

        # Create multiple threads
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=create_connection)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # All connections should be the same instance (thread-safe singleton)
        first_connection = connections[0]
        for conn in connections[1:]:
            assert conn is first_connection

        # Should still have only one instance
        assert len(JdbcSqlServerConnection._instances) == 1


# SQL Injection patterns for testing
sql_injection_patterns = [
    "'; DROP TABLE users; --",
    "admin'--",
    "1' OR '1'='1",
    "'; EXEC xp_cmdshell('dir'); --",
    "admin'; WAITFOR DELAY '00:00:05'--",
    "1' UNION SELECT * FROM users--",
    "'; INSERT INTO users VALUES ('hacker', 'password'); --",
    "admin' OR 1=1#",
    "admin'/**/OR/**/1=1--",
    "1'; DELETE FROM users WHERE 't'='t",
]
