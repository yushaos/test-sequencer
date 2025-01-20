from nptdms import TdmsFile
import data_process_func as dpf

# Open TDMS file
tdms_file_path = "C:/Users/yusha/Desktop/test sequencer/utility/data_process/dummy_data.tdms"
tdms_file = TdmsFile(tdms_file_path)

# Read channel data from Group1
group = tdms_file["Group1"]
x_channel = group["A1_Time"]
y_channel = group["A1"]

# Convert channel data to lists
x_data = x_channel[:]
y_data = y_channel[:]

# Example usage of max function with some sample limits
result = dpf.max_check(x_data, y_data, 
                 time_begin=8.1,    # Start at 2 seconds
                 time_end=9.5,      # End at 5 seconds
                 low_limit=-0.5,     # Minimum acceptable value
                 high_limit=11.0)   # Maximum acceptable value

# Print result
if result:
    print("PASS")
else:
    print("FAIL")