from nptdms import TdmsFile, TdmsWriter, ChannelObject
import numpy as np
from datetime import datetime
import os

def aperture(x, y, y_threshold=0.3, min_sample_rate=0.001):
    """
    Process data using aperture algorithm
    Args:
        x: x values array
        y: y values array
        y_threshold: voltage threshold (default 0.3V)
        min_sample_rate: minimum time between points (default 0.001s / 1kHz)
    Returns:
        x_out, y_out: filtered arrays
    """
    # Pre-allocate max possible size
    x_out = np.zeros_like(x)
    y_out = np.zeros_like(y)
    
    # Always keep first point
    x_out[0] = x[0]
    y_out[0] = y[0]
    
    idx = 0  # Output array index
    last_kept_x = x[0]
    last_kept_y = y[0]
    
    for i in range(1, len(x)):
        # Check if time difference exceeds minimum sample rate
        time_diff = x[i] - last_kept_x
        # Check if voltage difference exceeds threshold
        volt_diff = abs(y[i] - last_kept_y)
        
        if time_diff >= min_sample_rate or volt_diff >= y_threshold:
            idx += 1
            x_out[idx] = x[i]
            y_out[idx] = y[i]
            last_kept_x = x[i]
            last_kept_y = y[i]
    
    # Always keep last point if not already kept
    if x_out[idx] != x[-1]:
        idx += 1
        x_out[idx] = x[-1]
        y_out[idx] = y[-1]
    
    return x_out[:idx+1], y_out[:idx+1]

def process_data(filename="aperture_demo_xy.tdms", chunk_size=100000):
    """
    Process TDMS file in chunks and save filtered data
    """
    with TdmsFile.open(filename) as tdms_file:
        # Get the first group and its channels
        group = tdms_file.groups()[0]
        x_channel = group.channels()[0]
        y_channel = group.channels()[1]
        
        # Process data in chunks
        total_points = len(x_channel)
        chunks = total_points // chunk_size + (1 if total_points % chunk_size else 0)
        
        x_filtered = []
        y_filtered = []
        
        for i in range(chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, total_points)
            
            x_chunk = x_channel[start_idx:end_idx]
            y_chunk = y_channel[start_idx:end_idx]
            
            x_out, y_out = aperture(x_chunk, y_chunk)
            x_filtered.extend(x_out)
            y_filtered.extend(y_out)
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"aperture_{timestamp}.tdms"
    
    # Write filtered data to new TDMS file
    with TdmsWriter(output_filename) as tdms_writer:
        x_channel_filtered = ChannelObject(
            group.name, 
            x_channel.name, 
            np.array(x_filtered)
        )
        y_channel_filtered = ChannelObject(
            group.name, 
            y_channel.name, 
            np.array(y_filtered)
        )
        tdms_writer.write_segment([x_channel_filtered, y_channel_filtered])
    
    # Add statistics
    original_points = total_points
    filtered_points = len(x_filtered)
    reduction_percent = ((original_points - filtered_points) / original_points) * 100
    
    print(f"\nData Reduction Statistics:")
    print(f"Original points: {original_points:,}")
    print(f"Filtered points: {filtered_points:,}")
    print(f"Data reduction: {reduction_percent:.2f}%")
    
    return output_filename

if __name__ == "__main__":
    output_file = process_data()
    print(f"Processed data saved to: {output_file}") 