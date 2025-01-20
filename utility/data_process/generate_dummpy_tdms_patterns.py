import numpy as np
from nptdms import TdmsWriter, RootObject, GroupObject, ChannelObject

# Set the total number of points and time range
n_points = 100000
time = np.linspace(0, 10, n_points)

# Generate A1 signal
A1 = np.zeros(n_points)

# Pulse signal (10000-20000 points)
pulse_start = 10000
pulse_end = 20000
A1[pulse_start:pulse_end] = 5.0

# Ramp signal (30000-40000 points)
ramp_start = 30000
ramp_end = 40000
ramp_points = ramp_end - ramp_start
half_ramp = ramp_points // 2
ramp_up = np.linspace(0, 3, half_ramp)
ramp_down = np.linspace(3, 0, half_ramp)
A1[ramp_start:ramp_start+half_ramp] = ramp_up
A1[ramp_start+half_ramp:ramp_end] = ramp_down

# Random noise around 2V (50000-60000 points)
noise_start_1 = 50000
noise_end_1 = 60000
A1[noise_start_1:noise_end_1] = 2.0 + np.random.uniform(-0.5, 0.5, noise_end_1-noise_start_1)

# Random noise around -2V (70000-80000 points)
noise_start_2 = 70000
noise_end_2 = 80000
A1[noise_start_2:noise_end_2] = -2.0 + np.random.uniform(-0.3, 0.3, noise_end_2-noise_start_2)

# EMP-like waveform (90000-100000 points)
emp_start = 90000
emp_end = 100000
t_emp = np.linspace(0, 1, emp_end-emp_start)
emp_wave = 10 * np.sin(2*np.pi*5*t_emp) * np.exp(-5*t_emp)
A1[emp_start:emp_end] = emp_wave

# Generate A2 signal
A2 = np.zeros(n_points)

# Square wave from 1s to 9s
square_start = int(1 * n_points/10)
square_end = int(9 * n_points/10)
period = 1000  # points per period
num_periods = (square_end - square_start) // period

for i in range(num_periods):
    start_idx = square_start + i * period
    half_period = period // 2
    
    # First half of period: high
    A2[start_idx:start_idx+half_period] = 10
    # Second half of period: low 
    A2[start_idx+half_period:start_idx+period] = -10

# Add pulse at 9.5-9.6s
pulse_start = int(9.5 * n_points/10)
pulse_end = int(9.6 * n_points/10)
A2[pulse_start:pulse_end] = 50.0

# Create TDMS file
file_path = 'dummy_data.tdms'
with TdmsWriter(file_path) as tdms_writer:
    # Create root object
    root_object = RootObject(properties={
        "Description": "Dummy TDMS file with test signals"
    })
    
    # Create group
    group = GroupObject("Group1", properties={
        "Sample Rate": f"{n_points/10} Hz"
    })
    
    # Create channels
    channel_A1 = ChannelObject("Group1", "A1", A1, properties={
        "Unit": "Volts"
    })
    channel_A1_Time = ChannelObject("Group1", "A1_Time", time, properties={
        "Unit": "Seconds"
    })
    channel_A2 = ChannelObject("Group1", "A2", A2, properties={
        "Unit": "Volts"
    })
    channel_A2_Time = ChannelObject("Group1", "A2_Time", time, properties={
        "Unit": "Seconds"
    })
    
    # Write to file
    tdms_writer.write_segment([
        root_object,
        group,
        channel_A1,
        channel_A1_Time,
        channel_A2,
        channel_A2_Time
    ])

print("TDMS file generated successfully!")