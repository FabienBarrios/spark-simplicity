"""
Custom exceptions for Spark Simplicity.

This module defines specific exceptions for better error handling
and debugging in production environments.
"""

from typing import Optional


class SparkSimplicityError(Exception):
    """Base exception for all Spark Simplicity errors."""

    def __init__(self, message: str, details: Optional[dict] = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class DataValidationError(SparkSimplicityError):
    """Raised when data validation fails."""

    pass


class DataFrameValidationError(DataValidationError):
    """Raised when DataFrame validation fails."""

    pass


class SchemaValidationError(DataValidationError):
    """Raised when schema validation fails."""

    pass


class CorruptDataError(DataValidationError):
    """Raised when corrupt data is detected."""

    pass


class SparkIOError(SparkSimplicityError):
    """Base exception for I/O operations."""

    pass


class FileReadError(SparkIOError):
    """Raised when file reading fails."""

    pass


class FileWriteError(SparkIOError):
    """Raised when file writing fails."""

    pass


class FormatError(SparkIOError):
    """Raised when file format is invalid or unsupported."""

    pass


class SparkConnectionError(SparkSimplicityError):
    """Base exception for connection-related errors."""

    pass


class DatabaseConnectionError(SparkConnectionError):
    """Raised when database connection fails."""

    pass


class SftpConnectionError(SparkConnectionError):
    """Raised when SFTP connection fails."""

    pass


class EmailConnectionError(SparkConnectionError):
    """Raised when email connection fails."""

    pass


class ApiConnectionError(SparkConnectionError):
    """Raised when API connection fails."""

    pass


class ConfigurationError(SparkSimplicityError):
    """Raised when configuration is invalid."""

    pass


class SessionError(SparkSimplicityError):
    """Raised when Spark session operations fail."""

    pass


class JoinError(SparkSimplicityError):
    """Raised when join operations fail."""

    pass


class TransformationError(SparkSimplicityError):
    """Raised when data transformations fail."""

    pass


class PerformanceError(SparkSimplicityError):
    """Raised when performance issues are detected."""

    pass
