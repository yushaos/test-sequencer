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

def threshold_cross(x_data, y_data, threshold, mode="rise", time_begin=None, time_end=None):
    """
    Find time when signal crosses threshold
    """
    # Find indices for the specified time range
    start_idx = 0
    end_idx = len(x_data)
    
    if time_begin is not None:
        start_idx = next((i for i, x in enumerate(x_data) if x >= time_begin), 0)
    if time_end is not None:
        end_idx = next((i for i, x in enumerate(x_data) if x > time_end), len(x_data))
    
    # Get data slice
    x_slice = x_data[start_idx:end_idx]
    y_slice = y_data[start_idx:end_idx]
    
    # Find crossing
    for i in range(1, len(y_slice)):
        if mode == "rise" and y_slice[i-1] <= threshold < y_slice[i]:
            # Linear interpolation to get precise crossing time
            t_cross = x_slice[i-1] + (threshold - y_slice[i-1]) * \
                     (x_slice[i] - x_slice[i-1]) / (y_slice[i] - y_slice[i-1])
            return t_cross
            
        elif mode == "fall" and y_slice[i-1] >= threshold > y_slice[i]:
            # Linear interpolation to get precise crossing time
            t_cross = x_slice[i-1] + (threshold - y_slice[i-1]) * \
                     (x_slice[i] - x_slice[i-1]) / (y_slice[i] - y_slice[i-1])
            return t_cross
    
    # No crossing found
    return None

def result_check(value, low_limit=None, high_limit=None):
    """
    Generic function to check if value is within limits
    """
    if value is None:
        return False, None
        
    if low_limit is not None and value < low_limit:
        return False, value
    if high_limit is not None and value > high_limit:
        return False, value
        
    return True, value

def edge_time_diff(x1_data, y1_data, x2_data, y2_data, threshold1, threshold2, 
                  mode1="rise", mode2="rise",
                  time_begin1=None, time_end1=None,
                  time_begin2=None, time_end2=None):
    """
    Find time difference between two signal edge crossings
    """
    # Get first signal crossing time
    t1 = threshold_cross(x1_data, y1_data,
                        threshold=threshold1,
                        mode=mode1,
                        time_begin=time_begin1,
                        time_end=time_end1)
    
    # Get second signal crossing time
    t2 = threshold_cross(x2_data, y2_data,
                        threshold=threshold2,
                        mode=mode2,
                        time_begin=time_begin2,
                        time_end=time_end2)
    
    # If either crossing not found, return None
    if t1 is None or t2 is None:
        return None
        
    # Return time difference (t2 - t1)
    return t2 - t1

