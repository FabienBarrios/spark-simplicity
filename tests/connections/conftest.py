"""
Fixtures partagées pour les tests des connections.

Fixtures communes pour les tests des modules de connexion
suivant les bonnes pratiques pytest avec scope appropriés.
"""

import os
import sys
from unittest.mock import Mock

import pytest
from pyspark.sql import DataFrame, SparkSession

# Import direct pour éviter les conflits de dépendances
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))


@pytest.fixture(scope="function")
def mock_spark_session():
    """Mock SparkSession pour les tests connections."""
    mock_spark = Mock(spec=SparkSession)
    mock_context = Mock()
    mock_context.applicationId = "test-connections-app-123"
    mock_spark.sparkContext = mock_context

    # Mock read pour DataFrameReader
    mock_reader = Mock()
    mock_reader.option.return_value = mock_reader
    mock_reader.format.return_value = mock_reader
    mock_reader.load.return_value = Mock(spec=DataFrame)
    mock_spark.read = mock_reader

    return mock_spark


@pytest.fixture(scope="function")
def mock_logger():
    """Mock logger pour les tests."""
    return Mock()


@pytest.fixture(scope="function")
def sample_database_config():
    """Configuration de base de données standard pour les tests."""
    return {
        "host": "localhost",
        "port": "1433",
        "database": "test_database",
        "user": "test_user",
        "password": "test_password",
    }


@pytest.fixture(scope="function")
def minimal_database_config():
    """Configuration minimale de base de données (sans port)."""
    return {
        "host": "testhost",
        "database": "testdb",
        "user": "testuser",
        "password": "testpass",
    }


@pytest.fixture(scope="function")
def production_database_config():
    """Configuration de base de données pour environnement de production."""
    return {
        "host": "prod-server.company.com",
        "port": "1434",
        "database": "production_db",
        "user": "prod_user",
        "password": "super_secure_password_123!",
    }


@pytest.fixture(scope="function")
def config_with_port():
    """Configuration avec port personnalisé."""
    return {
        "host": "db-server",
        "port": "1434",
        "database": "proddb",
        "user": "produser",
        "password": "prodpass",
    }


@pytest.fixture(scope="function")
def mock_dataframe():
    """Mock DataFrame pour les résultats de requête."""
    mock_df = Mock(spec=DataFrame)
    mock_df.count.return_value = 1000
    mock_df.columns = ["id", "name", "email", "created_at"]
    return mock_df


@pytest.fixture(scope="function")
def mock_dataframe_reader():
    """Mock DataFrameReader configuré pour les tests."""
    mock_reader = Mock()
    mock_reader.option.return_value = mock_reader
    mock_reader.format.return_value = mock_reader
    mock_reader.load.return_value = Mock(spec=DataFrame)
    return mock_reader


@pytest.fixture(scope="function")
def sample_sql_queries():
    """Requêtes SQL d'exemple pour les tests."""
    return {
        "simple": "SELECT * FROM users",
        "with_where": "SELECT * FROM users WHERE active = 1",
        "complex": """
            SELECT
                u.id,
                u.name,
                COUNT(o.id) as order_count,
                SUM(o.total) as total_spent
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.created_at >= '2024-01-01'
            GROUP BY u.id, u.name
            HAVING COUNT(o.id) > 0
            ORDER BY total_spent DESC
        """,
        "count": "SELECT COUNT(*) as count FROM users",
        "insert": "INSERT INTO users (name, email) VALUES ('Test', 'test@example.com')",
    }


@pytest.fixture(scope="function")
def sample_partitioning_options():
    """Options de partitioning pour les tests."""
    return {
        "basic": {
            "numPartitions": "4",
            "partitionColumn": "id",
            "lowerBound": "1",
            "upperBound": "1000",
        },
        "with_fetchsize": {
            "numPartitions": "8",
            "partitionColumn": "user_id",
            "lowerBound": "1",
            "upperBound": "10000",
            "fetchsize": "10000",
        },
        "advanced": {
            "numPartitions": "10",
            "partitionColumn": "created_at",
            "lowerBound": "2024-01-01",
            "upperBound": "2024-12-31",
            "fetchsize": "5000",
            "queryTimeout": "300",
        },
    }


@pytest.fixture(scope="function")
def malicious_sql_patterns():
    """Patterns SQL malicieux pour tests de sécurité."""
    return [
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


@pytest.fixture(scope="function")
def unicode_test_data():
    """Données Unicode pour tests d'internationalisation."""
    return {
        "chinese": "测试服务器.example.com",
        "cyrillic": "тестовая_база_данных",
        "portuguese": "usuário_teste",
        "emoji": "пароль🔒密码",
        "mixed": "Hello世界🌍Test",
    }


@pytest.fixture(scope="function")
def email_config():
    """Configuration email pour les tests."""
    return {
        "smtp_host": "smtp.gmail.com",
        "smtp_port": 587,
        "email": "test@example.com",
        "password": "test_password",
        "use_tls": True,
    }


@pytest.fixture(scope="function")
def bulk_recipients():
    """Recipients data for bulk email testing."""
    return [
        {
            "email": "user1@example.com",
            "name": "User One",
            "company": "Company A",
            "balance": "1000",
        },
        {
            "email": "user2@example.com",
            "name": "User Two",
            "company": "Company B",
            "balance": "2500",
        },
        {
            "email": "user3@example.com",
            "name": "User Three",
            "company": "Company C",
            "balance": "750",
        },
    ]


@pytest.fixture(scope="function")
def sftp_config():
    """Configuration SFTP pour les tests."""
    return {
        "host": "sftp.example.com",
        "port": 22,
        "username": "test_user",
        "password": "test_password",
        "remote_path": "/data/",
    }


@pytest.fixture(scope="function")
def rest_api_config():
    """Configuration API REST pour les tests."""
    return {
        "base_url": "https://api.example.com",
        "api_key": "test_api_key",
        "timeout": 30,
        "max_retries": 3,
    }


@pytest.fixture(scope="function")
def sample_rest_api_config():
    """Configuration de base pour REST API."""
    return {
        "base_url": "https://api.example.com",
        "headers": {"Content-Type": "application/json"},
        "timeout": 10,
    }


@pytest.fixture(scope="function")
def production_rest_api_config():
    """Configuration REST API pour environnement de production."""
    return {
        "base_url": "https://prod-api.company.com",
        "headers": {"Content-Type": "application/json", "X-Environment": "production"},
        "timeout": 30,
        "retries": 5,
    }


@pytest.fixture(scope="function")
def auth_rest_api_config():
    """Configuration REST API avec authentification."""
    return {
        "base_url": "https://secure-api.example.com",
        "headers": {"Authorization": "Bearer token123", "X-API-Key": "api-key-456"},
        "auth": ("admin", "secret"),
        "timeout": 30,
    }


@pytest.fixture(scope="function")
def custom_retry_config():
    """Configuration REST API avec retry personnalisé."""
    return {
        "base_url": "https://retry-api.example.com",
        "retries": 5,
        "backoff_factor": 0.5,
        "status_forcelist": [500, 502, 503, 504, 429],
        "timeout": 20,
    }


@pytest.fixture(scope="function")
def connection_error_scenarios():
    """Scénarios d'erreurs de connexion pour les tests."""
    return {
        "timeout": "Connection timeout after 30 seconds",
        "refused": "Connection refused by server",
        "auth_failed": "Authentication failed",
        "host_unreachable": "Host unreachable",
        "ssl_error": "SSL certificate verification failed",
        "permission_denied": "Permission denied",
    }


@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Répertoire temporaire pour les données de test au niveau session."""
    return tmp_path_factory.mktemp("connections_test_data")


@pytest.fixture(autouse=True)
def setup_connections_test_environment():
    """Configuration automatique de l'environnement de test pour connections."""
    # Configuration qui s'applique à tous les tests connections
    # Par exemple, variables d'environnement, logging, etc.
    yield
    # Nettoyage après chaque test si nécessaire


# Fixtures spécifiques aux différents types de connections


@pytest.fixture(scope="function")
def database_connections_configs():
    """Multiples configurations de base de données pour tests avancés."""
    return {
        "dev": {
            "host": "dev-db.company.com",
            "port": "1433",
            "database": "dev_database",
            "user": "dev_user",
            "password": "dev_password",
        },
        "staging": {
            "host": "staging-db.company.com",
            "port": "1433",
            "database": "staging_database",
            "user": "staging_user",
            "password": "staging_password",
        },
        "prod": {
            "host": "prod-db.company.com",
            "port": "1434",
            "database": "production_database",
            "user": "prod_user",
            "password": "prod_password",
        },
    }


@pytest.fixture(scope="function")
def jdbc_url_variations():
    """Variations d'URL JDBC pour tests."""
    return {
        "basic": (
            "jdbc:sqlserver://localhost:1433;databaseName=testdb;"
            "encrypt=true;trustServerCertificate=true"
        ),
        "with_custom_port": (
            "jdbc:sqlserver://server.com:1434;databaseName=proddb;"
            "encrypt=true;trustServerCertificate=true"
        ),
        "with_ip": (
            "jdbc:sqlserver://192.168.1.100:1433;databaseName=mydb;"
            "encrypt=true;trustServerCertificate=true"
        ),
        "with_instance": (
            "jdbc:sqlserver://server\\SQLEXPRESS:1433;databaseName=testdb;"
            "encrypt=true;trustServerCertificate=true"
        ),
    }


@pytest.fixture(scope="function")
def base_options_variations():
    """Variations d'options de base pour tests."""
    return {
        "standard": {
            "user": "testuser",
            "password": "testpass",
            "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
            "fetchsize": "5000",
        },
        "large_fetchsize": {
            "user": "testuser",
            "password": "testpass",
            "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
            "fetchsize": "50000",
        },
        "with_timeout": {
            "user": "testuser",
            "password": "testpass",
            "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver",
            "fetchsize": "5000",
            "queryTimeout": "300",
        },
    }


@pytest.fixture(scope="function")
def invalid_configurations():
    """Configurations invalides pour tests d'erreur."""
    return {
        "missing_host": {"database": "test", "user": "test", "password": "test"},
        "missing_database": {"host": "test", "user": "test", "password": "test"},
        "missing_user": {"host": "test", "database": "test", "password": "test"},
        "missing_password": {"host": "test", "database": "test", "user": "test"},
        "empty_values": {"host": "", "database": "", "user": "", "password": ""},
        "none_values": {"host": None, "database": None, "user": None, "password": None},
    }


@pytest.fixture(scope="function")
def performance_test_configs():
    """Configurations pour tests de performance."""
    return {
        "high_volume": {
            "host": "high-volume-db.company.com",
            "port": "1433",
            "database": "analytics_db",
            "user": "analytics_user",
            "password": "analytics_password",
        },
        "concurrent_access": {
            "host": "concurrent-db.company.com",
            "port": "1434",
            "database": "concurrent_db",
            "user": "concurrent_user",
            "password": "concurrent_password",
        },
    }


@pytest.fixture(scope="function")
def stress_test_data():
    """Données pour tests de stress et de charge."""
    return {
        "large_query": (
            "SELECT * FROM very_large_table WHERE complex_condition = 'value'"
        ),
        "concurrent_queries": [
            "SELECT COUNT(*) as count FROM table1",
            "SELECT AVG(value) as avg FROM table2",
            "SELECT MAX(timestamp) as max FROM table3",
        ],
        "partitioning_scenarios": [
            {
                "numPartitions": "10",
                "partitionColumn": "id",
                "lowerBound": "1",
                "upperBound": "1000000",
            },
            {
                "numPartitions": "20",
                "partitionColumn": "date",
                "lowerBound": "2020-01-01",
                "upperBound": "2024-12-31",
            },
        ],
    }
