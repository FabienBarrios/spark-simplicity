"""
Spark Simplicity - Logging Configuration
=========================================

Centralized logging configuration for Spark Simplicity applications.
This module provides consistent logging setup across all modules with
standardized formatting and output handling.

Key Features:
    - Consistent log formatting across all modules
    - Prevents duplicate handler creation
    - Console output with timestamp and level information
    - Module-specific logger instances
    - INFO level logging by default

Usage:
    from spark_simplicity.logger import get_logger

    logger = get_logger("spark_simplicity.my_module")
    logger.info("Processing started")
    logger.error("An error occurred")
"""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance with standardized configuration.

    Creates a logger with consistent formatting and console output.
    Prevents duplicate handler creation for the same logger name.

    Args:
        name: Logger name, typically module name (e.g., "spark_simplicity.session")

    Returns:
        Configured Logger instance

    Example:
         logger = get_logger("spark_simplicity.utils")
         logger.info("Operation completed successfully")
         logger.warning("Configuration issue detected")
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding multiple handlers
    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.propagate = False

    return logger
