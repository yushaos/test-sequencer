from scipy import interpolate
import numpy as np
from scipy import signal

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

def MaxLimit(x_data, y_data, time_begin=None, time_end=None, low_limit=None, high_limit=None):
    max_value, x_at_max = max_check(x_data, y_data, time_begin, time_end)
    pass_fail, value = result_check(max_value, low_limit, high_limit)
    return (pass_fail, value, x_at_max)

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

def MinLimit(x_data, y_data, time_begin=None, time_end=None, low_limit=None, high_limit=None):
    min_value, x_at_min = min_check(x_data, y_data, time_begin, time_end)
    pass_fail, value = result_check(min_value, low_limit, high_limit)
    return (pass_fail, value, x_at_min)

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

def AverageLimit(x_data, y_data, time_begin=None, time_end=None, low_limit=None, high_limit=None):
    avg_value = average_check(x_data, y_data, time_begin, time_end)
    pass_fail, value = result_check(avg_value, low_limit, high_limit)
    return (pass_fail, value, None)  # Returns None for timestamp since average doesn't have one

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

def ThresholdCrossLimit(x_data, y_data, threshold, mode="rise", time_begin=None, time_end=None, low_limit=None, high_limit=None):
    cross_time = threshold_cross(x_data, y_data, threshold, mode, time_begin, time_end)
    pass_fail, value = result_check(cross_time, low_limit, high_limit)
    return (pass_fail, value, cross_time)  # Return crossing time as the timestamp

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

def EdgeTimeDiffLimit(x1_data, y1_data, x2_data, y2_data, threshold1, threshold2, 
                     mode1="rise", mode2="rise",
                     time_begin1=None, time_end1=None,
                     time_begin2=None, time_end2=None,
                     low_limit=None, high_limit=None):
    time_diff = edge_time_diff(x1_data, y1_data, x2_data, y2_data,
                             threshold1=threshold1, threshold2=threshold2,
                             mode1=mode1, mode2=mode2,
                             time_begin1=time_begin1, time_end1=time_end1,
                             time_begin2=time_begin2, time_end2=time_end2)
    pass_fail, value = result_check(time_diff, low_limit, high_limit)
    return (pass_fail, value, time_diff)  # Return time difference as timestamp

def transition_duration(x_data, y_data, min_level, mode="rise", lower_threshold=0.1, upper_threshold=0.9, time_begin=None, time_end=None):
    """Calculate rise/fall time between specified thresholds"""    
    # Find the time when signal crosses min_level
    t_cross = threshold_cross(x_data, y_data, min_level, mode, time_begin, time_end)
    if t_cross is None:
        print(f"Could not find crossing at min_level={min_level} between t={time_begin} and t={time_end}")
        return None
    
    #print(f"Found min_level crossing at t = {t_cross:.6f}")
    
    # Find indices for the specified time range
    start_idx = 0
    end_idx = len(x_data)
    
    if time_begin is not None:
        start_idx = next((i for i, x in enumerate(x_data) if x >= time_begin), 0)
    if time_end is not None:
        end_idx = next((i for i, x in enumerate(x_data) if x > time_end), len(x_data))
    
    # Verify we have enough data points in range
    if end_idx - start_idx < 2:
        print(f"Not enough data points between t={time_begin} and t={time_end}")
        return None
        
    # Find the index closest to crossing time
    try:
        cross_idx = next(i for i, x in enumerate(x_data[start_idx:end_idx]) if x >= t_cross) + start_idx
        #print(f"Cross index found at t = {x_data[cross_idx]:.6f}")
    except StopIteration:
        print(f"Could not find index for crossing time t={t_cross}")
        return None
    
    # Function to calculate moving average
    def moving_average(data, idx, window=10, backwards=False):
        if backwards:
            start = max(0, idx - window + 1)
            points = [float(data[i]) for i in range(start, idx + 1)]
        else:
            end = min(len(data), idx + window)
            points = [float(data[i]) for i in range(idx, end)]
        return sum(points) / len(points)
    
    if mode == "rise":
        # Look backwards for minimum
        min_idx = cross_idx
        prev_avg = moving_average(y_data, min_idx, backwards=True)
        
        for i in range(cross_idx - 1, start_idx, -1):
            curr_avg = moving_average(y_data, i, backwards=True)
            if curr_avg >= prev_avg:  # Stop when signal stops decreasing
                break
            min_idx = i
            prev_avg = curr_avg
                
        # Look forwards for maximum
        max_idx = cross_idx
        prev_avg = moving_average(y_data, max_idx)
        
        for i in range(cross_idx + 1, end_idx):
            curr_avg = moving_average(y_data, i)
            if curr_avg <= prev_avg:  # Stop when signal stops increasing
                break
            max_idx = i
            prev_avg = curr_avg
            
    else:  # mode == "fall"
        # Look backwards for maximum
        max_idx = cross_idx
        prev_avg = moving_average(y_data, max_idx, backwards=True)
        
        for i in range(cross_idx - 1, start_idx, -1):
            curr_avg = moving_average(y_data, i, backwards=True)
            if curr_avg <= prev_avg:  # Stop when signal stops increasing
                break
            max_idx = i
            prev_avg = curr_avg
                
        # Look forwards for minimum
        min_idx = cross_idx
        prev_avg = moving_average(y_data, min_idx)
        
        for i in range(cross_idx + 1, end_idx):
            curr_avg = moving_average(y_data, i)
            if curr_avg >= prev_avg:  # Stop when signal stops decreasing
                break
            min_idx = i
            prev_avg = curr_avg
    
    #print(f"Found min at t = {x_data[min_idx]:.6f}, y = {float(y_data[min_idx]):.6f}")
    #print(f"Found max at t = {x_data[max_idx]:.6f}, y = {float(y_data[max_idx]):.6f}")
    
    # Calculate reference levels
    y_min = float(y_data[min_idx])
    y_max = float(y_data[max_idx])
    y_range = y_max - y_min
    
    # Calculate threshold levels
    y_lower = y_min + lower_threshold * y_range
    y_upper = y_min + upper_threshold * y_range
    #print(f"Calculated threshold levels: lower = {y_lower:.3f}, upper = {y_upper:.3f}")
    
    # Handle case where transition happens between adjacent points
    if abs(max_idx - min_idx) <= 1:
        x0, x1 = x_data[min_idx], x_data[max_idx]
        y0, y1 = float(y_data[min_idx]), float(y_data[max_idx])
        
        # Linear interpolation: t = t0 + (y_target - y0) * (t1 - t0)/(y1 - y0)
        if mode == "rise":
            t_lower = x0 + (y_lower - y0) * (x1 - x0)/(y1 - y0)
            t_upper = x0 + (y_upper - y0) * (x1 - x0)/(y1 - y0)
        else:  # fall
            t_lower = x0 + (y_upper - y0) * (x1 - x0)/(y1 - y0)
            t_upper = x0 + (y_lower - y0) * (x1 - x0)/(y1 - y0)
            
        trans_time = abs(t_upper - t_lower)
        #print(f"Interpolated transition time = {trans_time:.6f}")
        return trans_time
    
    # Find times at threshold levels using interpolation within min_idx to max_idx range
    x_segment = x_data[min_idx:max_idx+1]
    y_segment = y_data[min_idx:max_idx+1]
    
    t_lower = threshold_cross(x_segment, y_segment, y_lower, mode)
    t_upper = threshold_cross(x_segment, y_segment, y_upper, mode)
    
    if t_lower is None or t_upper is None:
        print("Could not find threshold crossings within min-max range")
        return None
        
    #print(f"Found threshold crossings at t_lower = {t_lower:.6f}, t_upper = {t_upper:.6f}")
    
    # Calculate transition time
    trans_time = abs(t_upper - t_lower)
    #print(f"Calculated transition time = {trans_time:.6f}")
    
    return trans_time

def TransitionDurationLimit(x_data, y_data, min_level, mode="rise", lower_threshold=0.1, upper_threshold=0.9, 
                          time_begin=None, time_end=None, low_limit=None, high_limit=None):
    trans_time = transition_duration(x_data, y_data, min_level, mode, 
                                   lower_threshold, upper_threshold,
                                   time_begin, time_end)
    pass_fail, value = result_check(trans_time, low_limit, high_limit)
    return (pass_fail, value, trans_time)  # Return transition time as timestamp

def pulse_width(x_data, y_data, threshold, mode="rise", time_begin=None, time_end=None):
    """
    Calculate pulse width by finding time between rising and falling edges (or vice versa)
    at specified threshold level.
    """
    # Find first edge
    t1 = threshold_cross(x_data, y_data, threshold, mode, time_begin, time_end)
    if t1 is None:
        print(f"First edge not found at threshold={threshold}")
        return None
    
    # Find second edge with opposite mode, starting from t1
    opposite_mode = "fall" if mode == "rise" else "rise"
    t2 = threshold_cross(x_data, y_data, threshold, opposite_mode, time_begin=t1, time_end=time_end)
    if t2 is None:
        print(f"Second edge not found at threshold={threshold}")
        return None
    
    #print(f"First edge at t1={t1:.6f}s, Second edge at t2={t2:.6f}s")
    return t2 - t1

def PulseWidthLimit(x_data, y_data, threshold, mode="rise", time_begin=None, time_end=None, low_limit=None, high_limit=None):
    width = pulse_width(x_data, y_data, threshold, mode, time_begin, time_end)
    pass_fail, value = result_check(width, low_limit, high_limit)
    return (pass_fail, value, width)  # Return pulse width as timestamp

def freq(x_data, y_data, time_begin=None, time_end=None):
    """
    Calculate the dominant frequency of the signal using Welch's method
    """
    # Find indices for the specified time range
    start_idx = 0
    end_idx = len(x_data)
    
    if time_begin is not None:
        start_idx = next((i for i, x in enumerate(x_data) if x >= time_begin), 0)
    if time_end is not None:
        end_idx = next((i for i, x in enumerate(x_data) if x > time_end), len(x_data))
    
    # Get data slice
    y_slice = y_data[start_idx:end_idx]
    
    # Calculate sampling frequency
    dt = x_data[1] - x_data[0]  # Assuming uniform sampling
    fs = 1/dt
    
    # Calculate power spectral density using Welch's method
    frequencies, psd = signal.welch(y_slice, fs=fs, nperseg=min(len(y_slice), 1024))
    
    # Find frequency with maximum power
    dominant_freq = frequencies[psd.argmax()]
    
    #print(f"Dominant frequency: {dominant_freq:.2f} Hz")
    return dominant_freq

def FreqLimit(x_data, y_data, time_begin=None, time_end=None, low_limit=None, high_limit=None):
    frequency = freq(x_data, y_data, time_begin, time_end)
    pass_fail, value = result_check(frequency, low_limit, high_limit)
    return (pass_fail, value, None)  # Return None for timestamp since frequency is a rate

def DutyCycle(x_data, y_data, time_begin=None, time_end=None):
    """
    Calculate duty cycle of a digital signal
    """
    # Find indices for the specified time range
    start_idx = 0
    end_idx = len(x_data)
    if time_begin is not None:
        start_idx = next((i for i, x in enumerate(x_data) if x >= time_begin), 0)
    if time_end is not None:
        end_idx = next((i for i, x in enumerate(x_data) if x > time_end), len(x_data))
    # Get data slice
    y_slice = y_data[start_idx:end_idx]
    # Calculate mean of signal
    y_min = np.min(y_slice)
    y_max = np.max(y_slice)
    # Normalize signal between 0 and 1
    if y_max == y_min:
        return None  
    y_normalized = (y_slice - y_min) / (y_max - y_min)
    # Calculate duty cycle (mean of normalized signal)
    duty_cycle = np.mean(y_normalized)
    return duty_cycle

def DutyCycleLimit(x_data, y_data, time_begin=None, time_end=None, low_limit=None, high_limit=None):
    duty = DutyCycle(x_data, y_data, time_begin, time_end)
    pass_fail, value = result_check(duty, low_limit, high_limit)
    return (pass_fail, value, None)  # Return None for timestamp since duty cycle is a ratio

def PulseCount(x_data, y_data, threshold, time_begin=None, time_end=None):
    """
    Count number of pulses by detecting rising edges crossing the threshold
    """
    # Find indices for the specified time range
    start_idx = 0
    end_idx = len(x_data)
    
    if time_begin is not None:
        start_idx = next((i for i, x in enumerate(x_data) if x >= time_begin), 0)
    if time_end is not None:
        end_idx = next((i for i, x in enumerate(x_data) if x > time_end), len(x_data))
    
    # Get data slice
    y_slice = y_data[start_idx:end_idx]
    
    # Convert signal to binary (above/below threshold)
    binary_signal = (y_slice > threshold).astype(int)
    
    # Detect edges using diff
    edges = np.diff(binary_signal)
    
    # Count rising edges (transitions from 0 to 1)
    pulse_count = np.sum(edges == 1)
    
    return pulse_count

def PulseCountLimit(x_data, y_data, threshold, time_begin=None, time_end=None, low_limit=None, high_limit=None):
    count = PulseCount(x_data, y_data, threshold, time_begin, time_end)
    pass_fail, value = result_check(count, low_limit, high_limit)
    return (pass_fail, value, None)  # Return None for timestamp since count is not a time
