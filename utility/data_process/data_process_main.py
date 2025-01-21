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
    elif func_name == "edge_time_diff":
        time_str = f"Time Diff: {result_data[1]:.3f}s" if result_data[1] is not None else "No crossing found"
        print(f"REQ {req_id}: {status} ({time_str})")
    elif func_name == "transition_time":
        time_str = f"Transition Time: {result_data[1]:.6f}s" if result_data[1] is not None else "No valid transition found"
        print(f"REQ {req_id}: {status} ({time_str})")
    elif func_name == "pulse_width":
        width_str = f"Pulse Width: {result_data[1]:.6f}s" if result_data[1] is not None else "No valid pulse found"
        print(f"REQ {req_id}: {status} ({width_str})")
    elif func_name == "frequency":
        freq_str = f"Frequency: {result_data[1]:.2f} Hz" if result_data[1] is not None else "No frequency detected"
        print(f"REQ {req_id}: {status} ({freq_str})")
    elif func_name == "duty_cycle":
        duty_str = f"Duty Cycle: {result_data[1]:.1f}" if result_data[1] is not None else "No duty cycle detected"
        print(f"REQ {req_id}: {status} ({duty_str})")
    else:
        print(f"REQ {req_id}: {status}")

# Process each test requirement
for req in config["test_requirements"]:
    try:
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
        result = None
        if req["func_name"] == "max":
            max_value, x_at_max = dpf.max_check(x_data, y_data,
                                              time_begin=req["time_begin"],
                                              time_end=req["time_end"])
            pass_fail, value = dpf.result_check(max_value, 
                                              low_limit=req["low_limit"],
                                              high_limit=req["high_limit"])
            result = (pass_fail, value, x_at_max)
            
        elif req["func_name"] == "min":
            min_value, x_at_min = dpf.min_check(x_data, y_data,
                                              time_begin=req["time_begin"],
                                              time_end=req["time_end"])
            pass_fail, value = dpf.result_check(min_value,
                                              low_limit=req["low_limit"],
                                              high_limit=req["high_limit"])
            result = (pass_fail, value, x_at_min)
            
        elif req["func_name"] == "average":
            avg_value = dpf.average_check(x_data, y_data,
                                        time_begin=req["time_begin"],
                                        time_end=req["time_end"])
            result = dpf.result_check(avg_value,
                                    low_limit=req["low_limit"],
                                    high_limit=req["high_limit"])
        elif req["func_name"] == "threshold_cross":
            cross_time = dpf.threshold_cross(x_data, y_data,
                                           threshold=req["threshold"],
                                           mode=req["mode"],
                                           time_begin=req["time_begin"],
                                           time_end=req["time_end"])
            result = dpf.result_check(cross_time,
                                    low_limit=req["low_limit"],
                                    high_limit=req["high_limit"])
        elif req["func_name"] == "edge_time_diff":
            # Get second channel data
            x2_channel_name = f"{req['channel_name2']}_Time"
            x2_channel = group[x2_channel_name]
            y2_channel = group[req['channel_name2']]
            x2_data = x2_channel[:]
            y2_data = y2_channel[:]
            
            time_diff = dpf.edge_time_diff(x_data, y_data, 
                                         x2_data, y2_data,
                                         threshold1=req["threshold"],
                                         threshold2=req["threshold2"],
                                         mode1=req["mode"],
                                         mode2=req["mode2"],
                                         time_begin1=req["time_begin"],
                                         time_end1=req["time_end"],
                                         time_begin2=req["time_begin2"],
                                         time_end2=req["time_end2"])
            result = dpf.result_check(time_diff,
                                    low_limit=req["low_limit"],
                                    high_limit=req["high_limit"])
        elif req["func_name"] == "transition_time":
            trans_time = dpf.transition_duration(x_data, y_data,
                                          mode=req["mode"],
                                          lower_threshold=req["lower_threshold"],
                                          upper_threshold=req["upper_threshold"],
                                          time_begin=req["time_begin"],
                                          time_end=req["time_end"],
                                          min_level=req["min_level"])
            result = dpf.result_check(trans_time,
                                    low_limit=req["low_limit"],
                                    high_limit=req["high_limit"])
        elif req["func_name"] == "pulse_width":
            width = dpf.pulse_width(x_data, y_data,
                                  threshold=req["threshold"],
                                  mode=req["mode"],
                                  time_begin=req["time_begin"],
                                  time_end=req["time_end"])
            result = dpf.result_check(width,
                                    low_limit=req["low_limit"],
                                    high_limit=req["high_limit"])
        elif req["func_name"] == "frequency":
            frequency = dpf.freq(x_data, y_data,
                               time_begin=req["time_begin"],
                               time_end=req["time_end"])
            result = dpf.result_check(frequency,
                                    low_limit=req["low_limit"],
                                    high_limit=req["high_limit"])
        elif req["func_name"] == "duty_cycle":
            duty = dpf.DutyCycle(x_data, y_data,
                               time_begin=req["time_begin"],
                               time_end=req["time_end"])
            result = dpf.result_check(duty,
                                    low_limit=req["low_limit"],
                                    high_limit=req["high_limit"])
        
        # Print result only if we have a supported function
        if result is not None:
            print_result(req['req_id'], req['func_name'], result)
        else:
            print(f"Skipping {req['req_id']}: Unknown function '{req['func_name']}'")
            
    except Exception as e:
        print(f"Error processing {req['req_id']}: {str(e)}")
        continue