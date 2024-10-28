import numpy as np
from nptdms import TdmsWriter, ChannelObject
import os
from datetime import datetime

def write_tdms():
    # Your TDMS writing logic here
    print("Writing TDMS file...")
    return True

def run(config, argument):
    # Create the base result directory if it doesn't exist
    base_result_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'result TDMS')
    os.makedirs(base_result_dir, exist_ok=True)

    # Generate a unique filename using the current timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_name = f"random_data_{timestamp}"
    
    # Create a new directory with the same name as the file
    result_dir = os.path.join(base_result_dir, file_name)
    os.makedirs(result_dir, exist_ok=True)

    # Set the full file path
    file_path = os.path.join(result_dir, f"{file_name}.tdms")

    # Generate random data for three channels
    num_samples = 1000
    time = np.linspace(0, 10, num_samples)
    voltage = np.random.normal(0, 1, num_samples)
    current = np.random.normal(0, 0.1, num_samples)
    temperature = np.random.uniform(20, 30, num_samples)

    # Create channel objects
    channel_time = ChannelObject("Group", "Time", time)
    channel_voltage = ChannelObject("Group", "Voltage", voltage)
    channel_current = ChannelObject("Group", "Current", current)
    channel_temperature = ChannelObject("Group", "Temperature", temperature)

    # Write data to TDMS file
    with TdmsWriter(file_path) as tdms_writer:
        tdms_writer.write_segment([
            channel_time,
            channel_voltage,
            channel_current,
            channel_temperature
        ])

    print(f"TDMS file created: {file_path}")
    return True

if __name__ == "__main__":
    result = run({}, "")
    print(f"The function returned: {result}")
