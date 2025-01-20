def max_check(x_data, y_data, time_begin=None, time_end=None, low_limit=None, high_limit=None):
    """
    Find max value in specified range and check if it's within limits
    """
    # Find indices for the specified time range
    start_idx = 0
    end_idx = len(x_data)
    
    if time_begin is not None:
        start_idx = next((i for i, x in enumerate(x_data) if x >= time_begin), 0)
    if time_end is not None:
        end_idx = next((i for i, x in enumerate(x_data) if x > time_end), len(x_data))
    
    # Get the max value in the specified range
    max_value = max(y_data[start_idx:end_idx])
    
    # Check if value is within limits
    if low_limit is not None and max_value < low_limit:
        return False
    if high_limit is not None and max_value > high_limit:
        return False
    
    return True