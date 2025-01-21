from scipy import interpolate
import numpy as np

def max_check(x_data, y_data, time_begin=None, time_end=None):
    """
    Find max value in specified range
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
    
    return max_value, x_at_max

def min_check(x_data, y_data, time_begin=None, time_end=None):
    """
    Find min value in specified range
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
    
    return min_value, x_at_min

def average_check(x_data, y_data, time_begin=None, time_end=None):
    """
    Find average value in specified range
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
    
    return avg_value

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

def transition_time(x_data, y_data, mode="rise", lower_threshold=0.1, upper_threshold=0.9, 
                   time_begin=None, time_end=None, min_level=None):
    """
    Find signal transition (rise/fall) time between thresholds
    """
    print(f"\nStarting transition_time analysis:")
    print(f"Mode: {mode}, Min Level: {min_level}")
    print(f"Thresholds: {lower_threshold*100}% to {upper_threshold*100}%")
    
    # Find indices for the specified time range
    start_idx = 0
    end_idx = len(x_data)
    
    if time_begin is not None:
        start_idx = next((i for i, x in enumerate(x_data) if x >= time_begin), 0)
    if time_end is not None:
        end_idx = next((i for i, x in enumerate(x_data) if x > time_end), len(x_data))
    
    print(f"Analysis window: {x_data[start_idx]:.6f}s to {x_data[end_idx-1]:.6f}s")
    
    # Get data slice
    x_slice = x_data[start_idx:end_idx]
    y_slice = y_data[start_idx:end_idx]
    
    # Find transition points
    for i in range(1, len(y_slice)):
        if mode == "rise" and y_slice[i] > y_slice[i-1]:  # Rising edge
            y1, y2 = y_slice[i-1], y_slice[i]
            x1, x2 = x_slice[i-1], x_slice[i]
            
            # Check min_level requirement
            if min_level is not None and max(y1, y2) < min_level:
                continue
                
            # Calculate actual threshold values
            amplitude = y2 - y1
            low_thresh = y1 + amplitude * lower_threshold
            high_thresh = y1 + amplitude * upper_threshold
            
            print(f"Found rising edge from ({x1:.6f}s, {y1:.6f}V) to ({x2:.6f}s, {y2:.6f}V)")
            print(f"Threshold levels: {low_thresh:.6f}V and {high_thresh:.6f}V")
            
            # Linear interpolation for both thresholds
            t1 = x1 + (low_thresh - y1) * (x2 - x1) / (y2 - y1)
            t2 = x1 + (high_thresh - y1) * (x2 - x1) / (y2 - y1)
            
        elif mode == "fall" and y_slice[i] < y_slice[i-1]:  # Falling edge
            y1, y2 = y_slice[i-1], y_slice[i]
            x1, x2 = x_slice[i-1], x_slice[i]
            
            # Check min_level requirement
            if min_level is not None and max(y1, y2) < min_level:
                continue
                
            # Calculate actual threshold values for falling edge
            amplitude = y1 - y2  # Note: y1 is higher than y2 for falling edge
            # Swap thresholds for falling edge
            high_thresh = y1 - amplitude * lower_threshold  # 90% of initial value
            low_thresh = y1 - amplitude * upper_threshold   # 10% of initial value
            
            print(f"Found falling edge from ({x1:.6f}s, {y1:.6f}V) to ({x2:.6f}s, {y2:.6f}V)")
            print(f"Threshold levels: {high_thresh:.6f}V and {low_thresh:.6f}V")
            
            # Linear interpolation for both thresholds
            t1 = x1 + (high_thresh - y1) * (x2 - x1) / (y2 - y1)  # Time at 90%
            t2 = x1 + (low_thresh - y1) * (x2 - x1) / (y2 - y1)   # Time at 10%
            
        else:
            continue
            
        print(f"Found crossings at t1={t1:.6f}s and t2={t2:.6f}s")
        trans_time = t2 - t1
        print(f"Found transition time: {trans_time:.6f}s")
        return trans_time
                
    print("No valid transitions found")
    return None

