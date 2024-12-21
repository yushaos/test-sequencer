import numpy as np
from nptdms import TdmsWriter, RootObject, GroupObject, ChannelObject

# Generate time array
total_points = 1_000_000
t = np.arange(total_points)

# Initialize signal array
signal = np.zeros(total_points)

# Generate square wave for first 100,000 points
points_per_cycle = 2300  # 1000 + 100 + 1000 + 200 points
num_cycles = 100000 // points_per_cycle
for i in range(num_cycles):
    start_idx = i * points_per_cycle
    # 0 value for 1000 points
    # Ramp up to 5 in 100 points
    signal[start_idx+1000:start_idx+1100] = np.linspace(0, 5, 100)
    # Stay at 5 for 1000 points
    signal[start_idx+1100:start_idx+2100] = 5
    # Ramp down to -5 in 200 points
    signal[start_idx+2100:start_idx+2300] = np.linspace(5, -5, 200)
    if start_idx + 2300 < 100000:
        # Stay at -5 for remaining points until next cycle
        signal[start_idx+2300:start_idx+points_per_cycle] = -5

# Generate pulse in 3rd 100,000 points (200,000 to 300,000)
pulse_start = 200000
# Ramp up from 0 to 10
signal[pulse_start:pulse_start+100] = np.linspace(0, 10, 100)
# Stay at 10
signal[pulse_start+100:pulse_start+60100] = 10
# Ramp down to 0
signal[pulse_start+60100:pulse_start+60300] = np.linspace(10, 0, 200)

# Generate sine wave in 5th 100,000 points (400,000 to 500,000)
sine_start = 400000
points_per_sine_cycle = 10000
num_sine_cycles = 10
t_sine = np.linspace(0, 2*np.pi*num_sine_cycles, points_per_sine_cycle*num_sine_cycles)
signal[sine_start:sine_start+len(t_sine)] = 5 * np.sin(t_sine)

# Add random noise to entire signal
noise = np.random.uniform(-0.2, 0.2, total_points)
signal += noise

# Create TDMS file
file_path = 'waveform_data.tdms'
with TdmsWriter(file_path) as tdms_writer:
    root_object = RootObject(properties={
        "Description": "Waveform data with square wave, pulse, and sine patterns"
    })
    group_object = GroupObject("Waveforms", properties={})
    channel_object = ChannelObject("Waveforms", "A1", signal)
    
    tdms_writer.write_segment([
        root_object,
        group_object,
        channel_object
    ])

print(f"TDMS file has been generated: {file_path}") 