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

def print_result(req_id, func_name, result_data):
    """Print test results based on function type"""
    passed = result_data[0]
    status = 'PASS' if passed else 'FAIL'
    
    if func_name == "max":
        print(f"REQ {req_id}: {status} (Max: {result_data[1]:.3f}, Time: {result_data[2]:.3f}s)")
    elif func_name == "min":
        print(f"REQ {req_id}: {status} (Min: {result_data[1]:.3f}, Time: {result_data[2]:.3f}s)")
    elif func_name == "average":
        print(f"REQ {req_id}: {status} (Average: {result_data[1]:.3f})")
    elif func_name == "rise":
        print(f"REQ {req_id}: {status} (Rise Time: {result_data[1]:.3f}s)")
    elif func_name == "threshold_cross":
        time_str = f"Time: {result_data[1]:.3f}s" if result_data[1] is not None else "No crossing found"
        print(f"REQ {req_id}: {status} ({time_str})")
    else:
        print(f"REQ {req_id}: {status}")

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
    if req["func_name"] == "max":
        result = dpf.max_check(x_data, y_data,
                             time_begin=req["time_begin"],
                             time_end=req["time_end"],
                             low_limit=req["low_limit"],
                             high_limit=req["high_limit"])
    elif req["func_name"] == "min":
        result = dpf.min_check(x_data, y_data,
                             time_begin=req["time_begin"],
                             time_end=req["time_end"],
                             low_limit=req["low_limit"],
                             high_limit=req["high_limit"])
    elif req["func_name"] == "average":
        result = dpf.average_check(x_data, y_data,
                                 time_begin=req["time_begin"],
                                 time_end=req["time_end"],
                                 low_limit=req["low_limit"],
                                 high_limit=req["high_limit"])
    elif req["func_name"] == "rise":
        result = dpf.rise_time(x_data, y_data,
                             time_begin=req["time_begin"],
                             time_end=req["time_end"],
                             low_limit=req["low_limit"],
                             high_limit=req["high_limit"],
                             threshold=req["threshold"],
                             percent_low=req["percent_low"],
                             percent_high=req["percent_high"])
    elif req["func_name"] == "threshold_cross":
        result = dpf.threshold_cross(x_data, y_data,
                                   threshold=req["threshold"],
                                   mode=req["mode"],
                                   time_begin=req["time_begin"],
                                   time_end=req["time_end"],
                                   low_limit=req["low_limit"],
                                   high_limit=req["high_limit"])
        
    # Print result with requirement ID and additional info
    print_result(req['req_id'], req['func_name'], result)