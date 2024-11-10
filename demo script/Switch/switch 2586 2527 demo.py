import niswitch
import time

def main():
    try:
        # Initialize switch sessions
        print("Initializing switch sessions...")
        switch_01 = niswitch.Session("switch_01")  # PXI-2586
        switch_02 = niswitch.Session("switch_02")  # PXIe-2527
        
        # Configure switch_01 (PXI-2586)
        print("Configuring switch_01 (PXI-2586)...")
        # Enable and close channels 0-2
        channels_to_configure = ["ch0", "ch1", "ch2"]
        for channel in channels_to_configure:
            switch_01.connect(channel, "com0")  # Connect channels to common
        
        # Configure switch_02 (PXIe-2527)
        print("Configuring switch_02 (PXIe-2527)...")
        # Enable channel 0 and set to open state
        switch_02.disconnect("ch0", "com0")  # Disconnect = open state
        
        print("Switches configured. Waiting for 3 seconds...")
        time.sleep(3)
        
        # Return to default state
        print("Returning switches to default state...")
        switch_01.disconnect_all()
        switch_02.disconnect_all()
        
        # Close sessions
        print("Closing switch sessions...")
        switch_01.close()
        switch_02.close()
        
        print("Program completed successfully!")
        
    except niswitch.Error as e:
        print(f"Error occurred: {e}")
        # Attempt to clean up in case of error
        try:
            switch_01.close()
            switch_02.close()
        except:
            pass
        raise
    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        raise

if __name__ == "__main__":
    main()