import niswitch
import time

def safe_connect(switch, ch, com):
    """Safely connect channels by checking existing connections first"""
    try:
        # Try to check if path exists first
        try:
            if switch.can_connect(ch, com):
                switch.connect(ch, com)
                print(f"Successfully connected {ch} to {com}")
            else:
                print(f"Cannot connect {ch} to {com} - path not possible")
        except niswitch.Error:
            # If can_connect raises an error, try disconnecting first
            try:
                switch.disconnect(ch, com)
                print(f"Disconnected existing connection between {ch} and {com}")
                switch.connect(ch, com)
                print(f"Successfully connected {ch} to {com}")
            except niswitch.Error as e:
                print(f"Error managing connection {ch} to {com}: {e}")
    except Exception as e:
        print(f"Unexpected error connecting {ch} to {com}: {e}")

def main():
    try:
        # Initialize switch sessions
        print("Initializing switch sessions...")
        switch_01 = niswitch.Session("switch_01")  # PXI-2586
        switch_02 = niswitch.Session("switch_02")  # PXIe-2527
        
        # First disconnect all connections to ensure clean state
        print("Cleaning up any existing connections...")
        switch_01.disconnect_all()
        switch_02.disconnect_all()
        time.sleep(0.5)  # Small delay to ensure cleanup completes
        
        # Configure switch_01 (PXI-2586)
        print("Configuring switch_01 (PXI-2586)...")
        # Connect multiple channels to their respective COMs
        safe_connect(switch_01, "ch0", "com0")
        safe_connect(switch_01, "ch1", "com1")
        
        # Configure switch_02 (PXIe-2527)
        print("Configuring switch_02 (PXIe-2527)...")
        # For 2527, connect one channel to the common terminal
        safe_connect(switch_02, "ch5", "com0")
        
        print("Switches configured. Waiting for 3 seconds...")
        time.sleep(3)
        
        # Demonstrate checking connection status
        print("\nChecking current connections...")
        try:
            path_01 = switch_01.get_path("ch0", "com0")
            print(f"Switch_01 path for ch0-com0: {path_01}")
        except niswitch.Error as e:
            print(f"No path exists for ch0-com0: {e}")
            
        try:
            path_02 = switch_02.get_path("ch5", "com0")
            print(f"Switch_02 path for ch5-com0: {path_02}")
        except niswitch.Error as e:
            print(f"No path exists for ch5-com0: {e}")
        
        # Return to default state
        print("\nReturning switches to default state...")
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