from nptdms import TdmsFile
import data_process_func as dpf
import json
from multiprocessing import Pool, cpu_count

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
    elif func_name == "pulse_count":
        count_str = f"Pulse Count: {result_data[1]}" if result_data[1] is not None else "No pulses detected"
        print(f"REQ {req_id}: {status} ({count_str})")
    else:
        print(f"REQ {req_id}: {status}")

def process_requirement(req):
    """Process a single test requirement"""
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
            result = dpf.MaxLimit(x_data, y_data,
                                time_begin=req["time_begin"],
                                time_end=req["time_end"],
                                low_limit=req["low_limit"],
                                high_limit=req["high_limit"])
            
        elif req["func_name"] == "min":
            result = dpf.MinLimit(x_data, y_data,
                                time_begin=req["time_begin"],
                                time_end=req["time_end"],
                                low_limit=req["low_limit"],
                                high_limit=req["high_limit"])
            
        elif req["func_name"] == "average":
            result = dpf.AverageLimit(x_data, y_data,
                                    time_begin=req["time_begin"],
                                    time_end=req["time_end"],
                                    low_limit=req["low_limit"],
                                    high_limit=req["high_limit"])
        elif req["func_name"] == "threshold_cross":
            result = dpf.ThresholdCrossLimit(x_data, y_data,
                                           threshold=req["threshold"],
                                           mode=req["mode"],
                                           time_begin=req["time_begin"],
                                           time_end=req["time_end"],
                                           low_limit=req["low_limit"],
                                           high_limit=req["high_limit"])
        elif req["func_name"] == "edge_time_diff":
            # Get second channel data
            x2_channel_name = f"{req['channel_name2']}_Time"
            x2_channel = group[x2_channel_name]
            y2_channel = group[req['channel_name2']]
            x2_data = x2_channel[:]
            y2_data = y2_channel[:]
            
            result = dpf.EdgeTimeDiffLimit(x_data, y_data, x2_data, y2_data,
                                         threshold1=req["threshold"],
                                         threshold2=req["threshold2"],
                                         mode1=req["mode"],
                                         mode2=req["mode2"],
                                         time_begin1=req["time_begin"],
                                         time_end1=req["time_end"],
                                         time_begin2=req["time_begin2"],
                                         time_end2=req["time_end2"],
                                         low_limit=req["low_limit"],
                                         high_limit=req["high_limit"])
        elif req["func_name"] == "transition_time":
            result = dpf.TransitionDurationLimit(x_data, y_data,
                                               mode=req["mode"],
                                               lower_threshold=req["lower_threshold"],
                                               upper_threshold=req["upper_threshold"],
                                               time_begin=req["time_begin"],
                                               time_end=req["time_end"],
                                               min_level=req["min_level"],
                                               low_limit=req["low_limit"],
                                               high_limit=req["high_limit"])
        elif req["func_name"] == "pulse_width":
            result = dpf.PulseWidthLimit(x_data, y_data,
                                       threshold=req["threshold"],
                                       mode=req["mode"],
                                       time_begin=req["time_begin"],
                                       time_end=req["time_end"],
                                       low_limit=req["low_limit"],
                                       high_limit=req["high_limit"])
        elif req["func_name"] == "frequency":
            result = dpf.FreqLimit(x_data, y_data,
                                 time_begin=req["time_begin"],
                                 time_end=req["time_end"],
                                 low_limit=req["low_limit"],
                                 high_limit=req["high_limit"])
        elif req["func_name"] == "duty_cycle":
            result = dpf.DutyCycleLimit(x_data, y_data,
                                      time_begin=req["time_begin"],
                                      time_end=req["time_end"],
                                      low_limit=req["low_limit"],
                                      high_limit=req["high_limit"])
                                    
        elif req["func_name"] == "pulse_count":
            result = dpf.PulseCountLimit(x_data, y_data,
                                       threshold=req["threshold"],
                                       time_begin=req["time_begin"],
                                       time_end=req["time_end"],
                                       low_limit=req["low_limit"],
                                       high_limit=req["high_limit"])
        
        # Return results instead of printing
        return req['req_id'], req['func_name'], result
        
    except Exception as e:
        return req['req_id'], None, f"Error: {str(e)}"

if __name__ == '__main__':
    # Process requirements in parallel
    with Pool(processes=cpu_count()) as pool:
        results = pool.map(process_requirement, config["test_requirements"])
        
    # Print results in order
    for req_id, func_name, result in results:
        if func_name:
            print_result(req_id, func_name, result)
        else:
            print(f"Error processing {req_id}: {result}")