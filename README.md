# Spark Simplicity 🚀

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Spark 3.5+](https://img.shields.io/badge/Spark-3.5+-orange.svg)](https://spark.apache.org/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)



**Transform complex PySpark operations into simple, readable code.**

Spark Simplicity is a production-ready Python package that simplifies Apache Spark workflows with an intuitive API. Whether you're building ETL pipelines, analyzing big data, or processing streams, focus on your data logic instead of Spark boilerplate.

## ✨ Key Features

- **🎯 Intuitive API**: Simple, readable functions like `load_csv()`, `write_parquet()`
- **⚡ Optimized Performance**: Built-in broadcast joins, partitioning, and caching strategies
- **🏭 Production-Ready**: Environment-specific configurations for dev, test, and production
- **📊 Rich I/O Support**: CSV, JSON, Parquet, Excel, and fixed-width files with intelligent defaults
- **🔧 Advanced Connections**: Database (JDBC), SFTP, REST API, and email integrations
- **🎚️ Session Management**: Optimized Spark sessions with automatic resource management
- **🛡️ Enterprise Security**: Comprehensive validation, error handling, and logging
- **💻 Windows Compatible**: Automatic Hadoop workarounds for seamless Windows development

## 🚀 Quick Start

### Installation

```bash
pip install spark-simplicity
```

### Basic Usage

```python
from spark_simplicity import get_spark_session, load_csv, write_parquet

# Create optimized Spark session
spark = get_spark_session("my_app")

# Load data with intelligent defaults
customers = load_csv(spark, "customers.csv")
orders = load_csv(spark, "orders.csv")

# Simple DataFrame operations
result = customers.join(orders, "customer_id", "left")

# Write optimized output
write_parquet(result, "customer_orders.parquet")
```

That's it! No complex configurations, no boilerplate code.

## 📚 Core Modules

### 🎛️ Session Management

Create optimized Spark sessions for different environments:

```python
from spark_simplicity import get_spark_session

# Local development (default)
spark = get_spark_session("my_app")

# Production with optimizations
spark = get_spark_session("prod_app", environment="production")

# Testing with minimal resources
spark = get_spark_session("test_app", environment="testing")

# Custom configuration
spark = get_spark_session(
    "custom_app",
    config_overrides={
        "spark.executor.memory": "8g",
        "spark.executor.cores": "4"
    }
)
```

### 📁 I/O Operations

Load and save data with automatic optimizations:

```python
from spark_simplicity import (
    load_csv, load_excel, load_json, load_parquet, load_positional,
    write_csv, write_excel, write_json, write_parquet
)

# Reading data
df = load_csv(spark, "data.csv")  # Intelligent CSV parsing
df = load_excel(spark, "data.xlsx", sheet_name="Sales")  # Excel support
df = load_json(spark, "data.json")  # JSON with schema inference
df = load_parquet(spark, "data.parquet", columns=["id", "name"])  # Column pruning

# Fixed-width files
column_specs = [
    ("id", 0, 10),
    ("name", 10, 50), 
    ("amount", 50, 65)
]
df = load_positional(spark, "fixed_width.txt", column_specs)

# Writing data
write_csv(df, "output.csv", single_file=True)
write_parquet(df, "output.parquet", partition_by=["year", "month"])
write_json(df, "output.json", pretty_print=True)
write_excel(df, "output.xlsx", sheet_name="Results")
```

### 🔗 Enterprise Connections

Robust connection handling for enterprise environments:

```python
from spark_simplicity import (
    JdbcSqlServerConnection, SftpConnection, 
    RestApiConnection, EmailSender
)

# Database connections
db = JdbcSqlServerConnection(
    server="sql-server.company.com",
    database="datawarehouse",
    username="user",
    password="password"
)
df = db.read_table(spark, "sales_data")

# SFTP file operations
sftp = SftpConnection(
    hostname="sftp.company.com",
    username="user",
    private_key_path="/path/to/key"
)
sftp.download_file("/remote/data.csv", "/local/data.csv")

# REST API integration
api = RestApiConnection(base_url="https://api.company.com")
response = api.get("/data/endpoint", headers={"API-Key": "secret"})

# Email notifications
email = EmailSender(
    smtp_server="smtp.company.com",
    smtp_port=587,
    username="notifications@company.com",
    password="password"
)
email.send_email(
    to=["team@company.com"],
    subject="ETL Pipeline Completed",
    body="Your daily ETL pipeline has finished successfully."
)
```

## 🏗️ Advanced Features

### Environment-Specific Configurations

Spark Simplicity provides optimized configurations for different environments:

| Environment | Memory | Cores | Use Case |
|------------|--------|-------|----------|
| **Development** | 2GB | 2 | Interactive development, debugging |
| **Testing** | 512MB | 1 | CI/CD pipelines, unit tests |
| **Production** | 8GB | 4 | Production workloads, batch processing |
| **Local** | Auto-detect | Auto-detect | Single-machine processing |

### Windows Compatibility

Built-in Windows support with automatic Hadoop workarounds:

- ✅ Automatic Hadoop configuration bypass
- ✅ Windows-safe file system operations  
- ✅ Suppressed Hadoop native library warnings
- ✅ Python executable path configuration
- ✅ In-memory catalog by default

### Comprehensive Logging

Integrated logging system with multiple levels:

```python
from spark_simplicity import get_logger

# Get specialized logger
logger = get_logger("my_application")

# Different log levels
logger.info("Processing started")
logger.warning("Data quality issue detected")
logger.error("Processing failed")
```

## 📖 Architecture

```
spark-simplicity/
├── session.py              # Spark session management
├── io/                     # I/O operations
│   ├── readers/            # CSV, JSON, Parquet, Excel readers
│   ├── writers/            # Optimized writers with compression
│   ├── utils/              # File utilities and format detection
│   └── validation/         # Path validation and mount checking
├── connections/            # Enterprise integrations
│   ├── database_connection.py    # JDBC SQL Server
│   ├── sftp_connection.py        # SFTP with retry logic
│   ├── rest_api_connection.py    # REST API client
│   └── email_connection.py       # SMTP email sender
├── logger.py               # Centralized logging
├── utils.py                # DataFrame utilities
├── exceptions.py           # Custom exceptions
└── notification_service.py # Notification management
```

## 🛠️ Development

### Prerequisites

- Python 3.8+
- Java 8, 11, or 17 (for Spark)
- Apache Spark 3.5+

### Development Setup

```bash
# Clone the repository
git clone https://github.com/FabienBarrios/spark-simplicity.git
cd spark-simplicity

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ -v

# Run code quality checks
black spark_simplicity/
isort spark_simplicity/
flake8 spark_simplicity/
mypy spark_simplicity/
```

### Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest -m "not slow"        # Skip slow tests

# Run with coverage
pytest --cov=spark_simplicity --cov-report=html
```

### Code Quality

The project maintains high code quality standards:

- **Black**: Code formatting (88 character line length)
- **isort**: Import sorting
- **Flake8**: Linting with additional plugins
- **Mypy**: Type checking
- **Bandit**: Security analysis
- **Pre-commit**: Automated quality checks

## 📊 Performance & Best Practices

### Optimized Session Management

```python
# Use environment-specific configurations
spark = get_spark_session("app", environment="production")

# Monitor session resources
from spark_simplicity import get_session_info, print_session_summary

info = get_session_info(spark)
print(f"Available executors: {info['executor_count']}")
print_session_summary(spark)
```

### Efficient I/O Operations

```python
# Leverage column pruning
df = load_parquet(spark, "large_file.parquet", columns=["id", "name"])

# Use partitioning for large datasets
write_parquet(df, "output.parquet", partition_by=["year", "month"])

# Optimize file output
write_csv(df, "output.csv", single_file=True, compression="gzip")
```

### Connection Pooling

```python
# Reuse connections efficiently
db = JdbcSqlServerConnection(server="...", database="...")

# Read multiple tables with same connection
customers = db.read_table(spark, "customers")
orders = db.read_table(spark, "orders")
products = db.read_table(spark, "products")
```

## 🧪 Testing Strategy

Comprehensive testing with multiple levels:

- **Unit Tests**: Fast, isolated component testing
- **Integration Tests**: Real Spark cluster testing  
- **Performance Tests**: Benchmark and profiling
- **Security Tests**: Vulnerability and penetration testing
- **Property-Based Tests**: Hypothesis-driven testing

Coverage targets:
- **Minimum**: 90% overall coverage
- **Target**: 95%+ for core modules

## 🔒 Security

Security-first design with comprehensive protections:

- **Input Validation**: All user inputs validated and sanitized
- **SQL Injection Protection**: Parameterized queries and prepared statements
- **Path Traversal Prevention**: Secure file path validation
- **Credential Management**: Secure storage and transmission
- **Audit Logging**: Comprehensive activity logging
- **Error Handling**: Secure error messages without sensitive data exposure

## 🌟 Contributing

We welcome contributions! Please see our contributing guidelines:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature-name`
3. **Write** tests for your changes
4. **Ensure** all tests pass: `pytest`
5. **Follow** code style: `black` and `isort`
6. **Add** documentation for new features
7. **Submit** a pull request

### Areas for Contribution

- 🧪 **More test cases** - Help us achieve 100% coverage across all modules
- 📚 **Documentation** - Examples, tutorials, API documentation
- ⚡ **Performance optimizations** - New caching strategies, join algorithms
- 🔌 **Integrations** - Support for more databases, cloud storage, file formats
- 🐛 **Bug fixes** - Report and fix issues
- 💡 **Feature requests** - Suggest new functionality

## 🗺️ Roadmap & Future Development

Spark Simplicity is actively evolving to meet the growing needs of the data engineering community. We're committed to continuous improvement and regularly adding new features based on user feedback and industry best practices.

### 🚀 Upcoming Features (v1.1.x)

- **🔄 Advanced Join Operations**
  - Window joins for time-series data
  - Fuzzy matching joins
  - Multi-table join optimization
  - Join performance analysis tools

- **📊 Enhanced DataFrame Utilities**
  - Data profiling and quality metrics
  - Automated schema validation
  - Smart partitioning recommendations
  - Performance bottleneck detection

- **🌊 Streaming Support**
  - Simplified Kafka integration
  - Real-time data processing utilities
  - Stream-to-batch conversion helpers
  - Monitoring and alerting for streams

### 🎯 Future Versions (v1.2.x+)

- **🤖 Machine Learning Integration**
  - MLlib workflow simplification
  - Feature engineering utilities
  - Model deployment helpers
  - Pipeline automation tools

- **☁️ Cloud Platform Support**
  - AWS S3/EMR optimizations
  - Azure Data Lake integration
  - Google Cloud Platform support
  - Multi-cloud deployment tools

- **📈 Advanced Analytics**
  - SQL query builder with type safety
  - Data lineage tracking
  - Performance benchmarking suite
  - Cost optimization recommendations

### 🌟 Long-term Vision (v2.0+)

- **🏗️ Next-Generation Architecture**
  - Spark 4.0 compatibility
  - Async operations support
  - Plugin architecture for extensibility
  - Advanced monitoring dashboard

- **🔗 Extended Ecosystem**
  - Delta Lake deep integration
  - Apache Iceberg support
  - Kubernetes-native operations
  - GraphQL API for metadata

### 🤝 Community-Driven Development

We actively listen to our community and prioritize features based on:
- **User feedback** and feature requests
- **Industry trends** and emerging technologies
- **Performance improvements** and optimization opportunities
- **Security enhancements** and compliance requirements

**Want to influence our roadmap?** 
- 💡 Submit feature requests in [GitHub Issues](https://github.com/FabienBarrios/spark-simplicity/issues)
- 🗣️ Join discussions in [GitHub Discussions](https://github.com/FabienBarrios/spark-simplicity/discussions)
- 🤝 Contribute code and become a collaborator

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Apache Spark** community for the powerful distributed computing framework
- **PySpark** developers for the Python API
- **Contributors** who help make this package better

## 📞 Support

- 🐛 **Bug Reports**: [GitHub Issues](https://github.com/FabienBarrios/spark-simplicity/issues)
- 💬 **Discussions**: [GitHub Discussions](https://github.com/FabienBarrios/spark-simplicity/discussions)
- 📧 **Contact**: fabienbarrios@gmail.com
- 📖 **Documentation**: [Read the Docs](https://spark-simplicity.readthedocs.io)

---

**Made with ❤️ for the Spark community**

*Spark Simplicity - Because data engineering should be simple, not complicated.*