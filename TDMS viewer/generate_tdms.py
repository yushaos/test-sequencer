from nptdms import TdmsWriter, ChannelObject, RootObject, GroupObject
import numpy as np
import os

# Create time and data arrays
def generate_channel_data(num_points, time_range=(0,10)):
    time = np.linspace(time_range[0], time_range[1], num_points)
    data = np.random.randn(num_points)
    return time, data

# Function to get unique filename
def get_unique_filename(base_filename):
    if not os.path.exists(base_filename):
        return base_filename
    
    base, ext = os.path.splitext(base_filename)
    counter = 1
    while True:
        new_filename = f"{base}_{counter}{ext}"
        if not os.path.exists(new_filename):
            return new_filename
        counter += 1

# Generate data for each channel pair
a1_points = 100_000
a2_points = 200_000 
a3_points = 1_000_000
a4_points = 100_000
a5_points = 100_000
a6_points = 100_000
a7_points = 6_000_000
a8_points = 6_000_000
a9_points = 6_000_000

a1_time, a1_data = generate_channel_data(a1_points)
a2_time, a2_data = generate_channel_data(a2_points)
a3_time, a3_data = generate_channel_data(a3_points)
a4_data = np.random.randn(a4_points)
a5_data = np.random.randn(a5_points)
a6_time, a6_data = generate_channel_data(a6_points, time_range=(0, 8))

# Generate new signals
# For A7 (0-10 range)
a7_time = np.linspace(0, 10, a7_points)
a7_data = np.random.uniform(0, 1, a7_points)

# For A8 (0-10 range)
a8_time = np.linspace(0, 10, a8_points)
a8_data = np.random.uniform(9, 10, a8_points)

# For A9 (0-10 range)
a9_time = np.linspace(0, 10, a9_points)
a9_data = np.random.uniform(-10, 10, a9_points)

# Get unique filename
filename = get_unique_filename("test_data.tdms")

# Create and write TDMS file
with TdmsWriter(filename) as tdms_writer:
    # Create root object with some properties
    root_obj = RootObject(properties={
        "Created By": "generate_tdms.py",
        "Description": "Test data file with multiple signals"
    })
    
    # Create group
    group = "digitizer"
    
    # Write channel pairs
    tdms_writer.write_segment([
        root_obj,
        GroupObject(group, properties={}),
        ChannelObject(group, "A1", a1_data),
        ChannelObject(group, "A1_Time", a1_time),
        ChannelObject(group, "A2", a2_data),
        ChannelObject(group, "A2_Time", a2_time),
        ChannelObject(group, "A3", a3_data),
        ChannelObject(group, "A3_Time", a3_time),
        ChannelObject(group, "A4", a4_data),
        ChannelObject(group, "A5", a5_data),
        ChannelObject(group, "A6", a6_data),
        ChannelObject(group, "A6_Time", a6_time),
        ChannelObject(group, "A7", a7_data),
        ChannelObject(group, "A7_Time", a7_time),
        ChannelObject(group, "A8", a8_data),
        ChannelObject(group, "A8_Time", a8_time),
        ChannelObject(group, "A9", a9_data),
        ChannelObject(group, "A9_Time", a9_time),
    ])

print(f"TDMS file generated successfully: {filename}")