"""
Date and time helper functions for handling datetime operations.
"""

from datetime import datetime, timedelta, timezone
from typing import Tuple

def get_date_range(days_back: int) -> Tuple[datetime, datetime]:
    """
    Get date range for analysis.
    
    Args:
        days_back: Number of days to go back from now
        
    Returns:
        Tuple of (start_date, end_date)
    """
    if days_back < 0:
        raise ValueError("days_back must be >= 0")
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=days_back)
    return start_date, end_date

def get_weekday_name(weekday_num: int, language: str = "vi") -> str:
    """
    Get weekday name from number.
    
    Args:
        weekday_num: Weekday number (0=Sunday, 1=Monday, etc.)
        language: Language for weekday names ('vi' or 'en')
        
    Returns:
        Weekday name
    """
    weekdays_vi = ['Chủ nhật', 'Thứ 2', 'Thứ 3', 'Thứ 4', 'Thứ 5', 'Thứ 6', 'Thứ 7']
    weekdays_en = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']
    
    weekdays = weekdays_vi if language == "vi" else weekdays_en
    
    if 0 <= weekday_num < len(weekdays):
        return weekdays[weekday_num]
    return "Unknown"

def get_hour_range_string(hour: int) -> str:
    """
    Get hour range string for display.
    
    Args:
        hour: Hour in 24-hour format
        
    Returns:
        Hour range string like "09:00-10:00"
    """
    if not 0 <= hour <= 23:
        raise ValueError("hour must be between 0 and 23 inclusive")
    end_hour = (hour + 1) % 24
    return f"{hour:02d}:00-{end_hour:02d}:00"   

