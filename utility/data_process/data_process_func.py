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
    
    # Find first valid transition
    i = 1
    while i < len(y_slice)-1:
        if mode == "rise":
            # Look for local minimum before rise
            if y_slice[i] <= y_slice[i-1] and y_slice[i] <= y_slice[i+1]:
                min_idx = i
                min_val = y_slice[i]
                start_i = i
                
                # Look for next local maximum
                while i < len(y_slice)-1 and y_slice[i] <= y_slice[i+1]:
                    i += 1
                max_idx = i
                max_val = y_slice[i]
                
                # Calculate actual thresholds for this transition
                amplitude = max_val - min_val
                low_thresh = min_val + amplitude * lower_threshold
                high_thresh = min_val + amplitude * upper_threshold
                
                # Check if this rise meets min_level requirement
                if min_level is None or max_val >= min_level:
                    print(f"Found rising transition from {x_slice[min_idx]:.6f}s to {x_slice[max_idx]:.6f}s, "
                          f"amplitude: {min_val:.6f}V to {max_val:.6f}V")
                    print(f"Threshold levels: {low_thresh:.6f}V to {high_thresh:.6f}V")
                    
                    # Create window around transition
                    window_start = max(0, min_idx)
                    window_end = min(len(y_slice), max_idx + 1)
                    
                    x_window = x_slice[window_start:window_end]
                    y_window = y_slice[window_start:window_end]
                    
                    print(f"\nAnalyzing transition window:")
                    print(f"Window time: {x_window[0]:.6f}s to {x_window[-1]:.6f}s")
                    print(f"Looking for crossings at {low_thresh:.6f}V and {high_thresh:.6f}V")
                    
                    # Create interpolation function
                    f = interpolate.interp1d(x_window, y_window, kind='cubic')
                    
                    # Create fine x points for interpolation
                    x_fine = np.linspace(x_window[0], x_window[-1], num=10000)  # Increased resolution
                    y_fine = f(x_fine)
                    
                    try:
                        t1_idx = next(i for i, y in enumerate(y_fine) if y >= low_thresh)
                        t2_idx = next(i for i, y in enumerate(y_fine) if y >= high_thresh)
                        t1 = x_fine[t1_idx]
                        t2 = x_fine[t2_idx]
                        print(f"Found crossings at t1={t1:.6f}s and t2={t2:.6f}s")
                        
                        trans_time = abs(t2 - t1)
                        print(f"Found transition time: {trans_time:.6f}s")
                        return trans_time
                        
                    except StopIteration:
                        print("Could not find both threshold crossings")
                        
        i += 1
    
    print("No valid transitions found")
    return None

