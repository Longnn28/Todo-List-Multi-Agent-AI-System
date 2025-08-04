"""
Utils package for hackathon project.
Contains helper functions, utilities, and common tools.
"""

from .database_helpers import (
    safe_sum_boolean,
    safe_cast_to_int,
    get_completion_percentage,
    safe_average
)
from .analytics_helpers import (
    analyze_productivity,
    analyze_patterns, 
    analyze_completion_rate,
    analyze_workload,
    get_analytics_summary
)
from .date_helpers import (
    get_date_range,
    get_weekday_name,
    get_hour_range_string
)

__all__ = [
    # Database helpers
    'safe_sum_boolean',
    'safe_cast_to_int', 
    'get_completion_percentage',
    'safe_average',
    
    # Analytics helpers
    'analyze_productivity',
    'analyze_patterns',
    'analyze_completion_rate', 
    'analyze_workload',
    'get_analytics_summary',
    
    # Date helpers
    'get_date_range',
    'get_weekday_name',
    'get_hour_range_string',
]
