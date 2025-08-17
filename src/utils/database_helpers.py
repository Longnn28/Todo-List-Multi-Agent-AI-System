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
        return 0.0
    return sum(values) / len(values)
