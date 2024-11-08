from nptdms import TdmsWriter, ChannelObject, RootObject, GroupObject
import numpy as np

# Create time and data arrays
def generate_channel_data(num_points, time_range=(0,10)):
    time = np.linspace(time_range[0], time_range[1], num_points)
    data = np.random.randn(num_points)
    return time, data

# Generate data for each channel pair
a1_points = 100_000
a2_points = 200_000 
a3_points = 1_000_000

a1_time, a1_data = generate_channel_data(a1_points)
a2_time, a2_data = generate_channel_data(a2_points)
a3_time, a3_data = generate_channel_data(a3_points)

# Create and write TDMS file
with TdmsWriter("test_data.tdms") as tdms_writer:
    # Create root object with some properties
    root_obj = RootObject(properties={
        "Created By": "generate_tdms.py",
        "Description": "Test data file"
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
    ])

print("TDMS file generated successfully!") 