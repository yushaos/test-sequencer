import nidaqmx
from nidaqmx.constants import LineGrouping

class MasterTrigger:
    def __init__(self, device_name, trigger_line):
        self.device_name = device_name
        self.trigger_line = trigger_line
        self.task = None

    def initialize(self):
        self.task = nidaqmx.Task()
        self.task.do_channels.add_do_chan(
            f"{self.device_name}/{self.trigger_line}",
            line_grouping=LineGrouping.CHAN_FOR_ALL_LINES
        )

    def start_trigger(self):
        if not self.task:
            raise RuntimeError("Task not initialized. Call initialize() first.")
        
        self.task.write(True)  # Set the trigger high
        self.task.write(False)  # Set the trigger low (create a pulse)

    def close(self):
        if self.task:
            self.task.close()

def run(config, argument):
    # Extract configuration if needed
    device_name = config.get("device_name", "Dev1")
    trigger_line = config.get("trigger_line", "PFI0")

    master_trigger = MasterTrigger(device_name, trigger_line)
    
    try:
        master_trigger.initialize()
        master_trigger.start_trigger()
        return True
    except Exception as e:
        print(f"An error occurred: {e}")
        return False
    finally:
        master_trigger.close()

if __name__ == "__main__":
    # For testing the script directly
    config = {
        "device_name": "Dev1",       # Replace with your actual device name
        "trigger_line": "PFI0"       # Replace with your actual trigger line
    }
    argument = "test argument"       # Replace or remove if not needed

    result = run(config, argument)
    print(f"The function returned: {result}")
