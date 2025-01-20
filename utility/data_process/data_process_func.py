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
    
    # Get the max value and its index in the specified range
    y_slice = y_data[start_idx:end_idx]
    max_value = y_slice.max()
    max_idx = start_idx + y_slice.argmax()
    x_at_max = x_data[max_idx]
    
    # Check if value is within limits
    if low_limit is not None and max_value < low_limit:
        return False, max_value, x_at_max
    if high_limit is not None and max_value > high_limit:
        return False, max_value, x_at_max
    
    return True, max_value, x_at_max

def min_check(x_data, y_data, time_begin=None, time_end=None, low_limit=None, high_limit=None):
    """
    Find min value in specified range and check if it's within limits
    """
    # Find indices for the specified time range
    start_idx = 0
    end_idx = len(x_data)
    
    if time_begin is not None:
        start_idx = next((i for i, x in enumerate(x_data) if x >= time_begin), 0)
    if time_end is not None:
        end_idx = next((i for i, x in enumerate(x_data) if x > time_end), len(x_data))
    
    # Get the min value and its index in the specified range
    y_slice = y_data[start_idx:end_idx]
    min_value = y_slice.min()
    min_idx = start_idx + y_slice.argmin()
    x_at_min = x_data[min_idx]
    
    # Check if value is within limits
    if low_limit is not None and min_value < low_limit:
        return False, min_value, x_at_min
    if high_limit is not None and min_value > high_limit:
        return False, min_value, x_at_min
    
    return True, min_value, x_at_min

def average_check(x_data, y_data, time_begin=None, time_end=None, low_limit=None, high_limit=None):
    """
    Find average value in specified range and check if it's within limits
    """
    # Find indices for the specified time range
    start_idx = 0
    end_idx = len(x_data)
    
    if time_begin is not None:
        start_idx = next((i for i, x in enumerate(x_data) if x >= time_begin), 0)
    if time_end is not None:
        end_idx = next((i for i, x in enumerate(x_data) if x > time_end), len(x_data))
    
    # Get the average value in the specified range
    data_slice = y_data[start_idx:end_idx]
    avg_value = sum(data_slice) / len(data_slice)
    
    # Check if value is within limits
    if low_limit is not None and avg_value < low_limit:
        return False, avg_value
    if high_limit is not None and avg_value > high_limit:
        return False, avg_value
    
    return True, avg_value

def rise_time(x_data, y_data, time_begin=None, time_end=None, low_limit=None, high_limit=None, 
              threshold=None, percent_low=0.1, percent_high=0.9):
    """
    Calculate rise time between percent_low and percent_high of the signal
    Uses linear interpolation to find precise timing points
    Returns True if rise time is within limits
    """
    # Find indices for the specified time range
    start_idx = 0
    end_idx = len(x_data)
    
    if time_begin is not None:
        start_idx = next((i for i, x in enumerate(x_data) if x >= time_begin), 0)
    if time_end is not None:
        end_idx = next((i for i, x in enumerate(x_data) if x > time_end), len(x_data))
    
    # Get data slice for analysis
    y_slice = y_data[start_idx:end_idx]
    x_slice = x_data[start_idx:end_idx]
    
    # Check threshold requirement
    if threshold is not None:
        max_val = max(y_slice)
        if max_val < threshold:
            return False, 0
    
    # Find min and max values for percentage calculations
    min_val = min(y_slice)
    max_val = max(y_slice)
    range_val = max_val - min_val
    
    # Calculate voltage levels for percent_low and percent_high
    low_voltage = min_val + (range_val * percent_low)
    high_voltage = min_val + (range_val * percent_high)
    
    # Find points around low_voltage crossing
    for i in range(len(y_slice)-1):
        if y_slice[i] <= low_voltage <= y_slice[i+1]:
            # Linear interpolation for low point
            slope = (y_slice[i+1] - y_slice[i]) / (x_slice[i+1] - x_slice[i])
            t_low = x_slice[i] + (low_voltage - y_slice[i]) / slope
            break
    else:
        return False, 0  # Low voltage crossing not found
    
    # Find points around high_voltage crossing
    for i in range(len(y_slice)-1):
        if y_slice[i] <= high_voltage <= y_slice[i+1]:
            # Linear interpolation for high point
            slope = (y_slice[i+1] - y_slice[i]) / (x_slice[i+1] - x_slice[i])
            t_high = x_slice[i] + (high_voltage - y_slice[i]) / slope
            break
    else:
        return False, 0  # High voltage crossing not found
    
    # Calculate rise time
    rise_time_val = t_high - t_low
    
    # Check if rise time is within limits
    if low_limit is not None and rise_time_val < low_limit:
        return False, rise_time_val
    if high_limit is not None and rise_time_val > high_limit:
        return False, rise_time_val
    
    return True, rise_time_val