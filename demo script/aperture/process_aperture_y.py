from nptdms import TdmsFile, TdmsWriter, ChannelObject
import numpy as np
from datetime import datetime
import time
import os

def aperture(y, delta_time, T0=0, y_threshold=0.5, min_sample_rate=0.001, burst_points=50):
    """
    Process data using aperture algorithm with uniform time steps
    """
    # Generate x values based on delta_time and T0
    x = np.arange(len(y), dtype=np.float32) * delta_time + T0
    
    x_out = np.zeros_like(x, dtype=np.float32)
    y_out = np.zeros_like(y, dtype=np.float32)
    
    # Convert input to float32
    y = y.astype(np.float32)
    y_threshold = np.float32(y_threshold)
    min_sample_rate = np.float32(min_sample_rate)
    
    # Always keep first point
    x_out[0] = x[0]
    y_out[0] = y[0]
    
    idx = 0
    last_kept_x = x[0]
    last_kept_y = y[0]
    burst_remaining = 0
    
    for i in range(1, len(y)-1):
        time_diff = x[i] - last_kept_x
        volt_diff = abs(y[i] - last_kept_y)
        
        if time_diff >= min_sample_rate or volt_diff >= y_threshold or burst_remaining > 0:
            idx += 1
            x_out[idx] = x[i]
            y_out[idx] = y[i]
            last_kept_x = x[i]
            last_kept_y = y[i]
            
            if volt_diff >= y_threshold:
                burst_remaining = burst_points
            elif burst_remaining > 0:
                burst_remaining -= 1
    
    # Always keep last point
    if x[-1] != x_out[idx]:
        idx += 1
        x_out[idx] = x[-1]
        y_out[idx] = y[-1]
    
    return x_out[:idx+1], y_out[:idx+1]

def process_data(filename="aperture_demo_y.tdms", chunk_size=100000, delta_time=4e-6):
    start_time = time.perf_counter()
    aperture_total_time = 0
    current_T0 = 0  # Track the starting time for each chunk
    
    with TdmsFile.open(filename) as tdms_file:
        group = tdms_file.groups()[0]
        # Get y channel data
        y_chan = group.channels()[0]
        y_channel = y_chan[:].astype(np.float32)
        
        # Process data in chunks
        total_points = len(y_channel)
        chunks = total_points // chunk_size + (1 if total_points % chunk_size else 0)
        
        x_filtered = []
        y_filtered = []
        
        for i in range(chunks):
            start_idx = i * chunk_size
            end_idx = min((i + 1) * chunk_size, total_points)
            
            y_chunk = y_channel[start_idx:end_idx]
            
            chunk_start = time.perf_counter()
            x_out, y_out = aperture(y_chunk, delta_time, T0=current_T0)
            aperture_total_time += time.perf_counter() - chunk_start
            
            x_filtered.extend(x_out)
            y_filtered.extend(y_out)
            
            # Update T0 for next chunk
            current_T0 = (end_idx) * delta_time
    
    # Create output filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"apertureY_{timestamp}.tdms"
    
    # Write filtered data to new TDMS file
    with TdmsWriter(output_filename) as tdms_writer:
        x_channel_filtered = ChannelObject(
            group.name, 
            y_chan.name + "_Time", 
            np.array(x_filtered)
        )
        y_channel_filtered = ChannelObject(
            group.name, 
            y_chan.name, 
            np.array(y_filtered)
        )
        tdms_writer.write_segment([x_channel_filtered, y_channel_filtered])
    
    # Statistics
    total_time = time.perf_counter() - start_time
    avg_aperture_time = aperture_total_time / chunks
    original_points = total_points
    filtered_points = len(x_filtered)
    reduction_percent = ((original_points - filtered_points) / original_points) * 100
    
    print(f"\nData Reduction Statistics:")
    print(f"Original points: {original_points:,}")
    print(f"Filtered points: {filtered_points:,}")
    print(f"Data reduction: {reduction_percent:.2f}%")
    print(f"Number of chunks processed: {chunks}")
    print(f"Average aperture processing time: {avg_aperture_time:.3f} seconds per chunk")
    print(f"Total processing time: {total_time:.3f} seconds")
    print(f"File I/O time: {(total_time - aperture_total_time):.3f} seconds")
    
    return output_filename

if __name__ == "__main__":
    output_file = process_data()
    print(f"Processed data saved to: {output_file}") 