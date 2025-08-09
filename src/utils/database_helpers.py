"""
Database helper functions for SQL operations and data manipulation.
"""

from sqlalchemy import func
from typing import Any
from .logger import logger


def safe_sum_boolean(column):
    """
    Helper function to safely sum boolean columns across different databases.
    
    Args:
        column: SQLAlchemy column representing a boolean field
        
    Returns:
        SQLAlchemy function that counts True values in the boolean column
    """
    # Cách đơn giản và an toàn: đếm các giá trị True
    return func.count(func.nullif(column, False))


def safe_cast_to_int(column, database_type: str = "postgresql"):
    """
    Safely cast a column to integer based on database type.
    
    Args:
        column: SQLAlchemy column to cast
        database_type: Type of database ('postgresql', 'sqlite', 'mysql')
        
    Returns:
        SQLAlchemy cast expression
    """
    logger.debug(f"Casting column to int using database type: {database_type}")
    if database_type == "postgresql":
        return func.cast(column, 'integer')
    elif database_type == "sqlite":
        return func.cast(column, 'integer')
    else:
        # Default fallback
        return func.cast(column, 'signed')


def get_completion_percentage(completed_count: int, total_count: int) -> float:
    """
    Calculate completion percentage safely.
    
    Args:
        completed_count: Number of completed items
        total_count: Total number of items
        
    Returns:
        Percentage as float (0-100)
    """
    if total_count == 0:
        logger.debug("get_completion_percentage called with total_count=0, returning 0.0")
        return 0.0
    return (completed_count / total_count) * 100


def safe_average(values: list) -> float:
    """
    Calculate average safely handling empty lists.
    
    Args:
        values: List of numeric values
        
    Returns:
        Average as float, 0.0 if empty list
    """
    if not values:
        logger.debug("safe_average called with empty list, returning 0.0")
        return 0.0
    return sum(values) / len(values)
