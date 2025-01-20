from nptdms import TdmsFile
import data_process_func as dpf
import json

# Open TDMS file
tdms_file_path = "C:/Users/yusha/Desktop/test sequencer/utility/data_process/dummy_data.tdms"
measurement_config_path = "measurement1.json"  # Add config file path

# Load measurement config
with open(measurement_config_path) as f:
    config = json.load(f)

tdms_file = TdmsFile(tdms_file_path)

# Process each test requirement
for req in config["test_requirements"]:
    # Get channel names
    y_channel_name = req["channel_name"]
    x_channel_name = f"{y_channel_name}_Time"
    
    # Read channel data from specified group
    group = tdms_file[req["Group"]]
    x_channel = group[x_channel_name]
    y_channel = group[y_channel_name]

    # Convert channel data to lists
    x_data = x_channel[:]
    y_data = y_channel[:]

    # Call the specified function with parameters from config
    if req["func_name"] == "max_check":
        result = dpf.max_check(x_data, y_data,
                             time_begin=req["time_begin"],
                             time_end=req["time_end"],
                             low_limit=req["low_limit"],
                             high_limit=req["high_limit"])
    elif req["func_name"] == "min_check":
        result = dpf.min_check(x_data, y_data,
                             time_begin=req["time_begin"],
                             time_end=req["time_end"],
                             low_limit=req["low_limit"],
                             high_limit=req["high_limit"])
        
    # Print result with requirement ID
    print(f"REQ {req['req_id']}: {'PASS' if result else 'FAIL'}")