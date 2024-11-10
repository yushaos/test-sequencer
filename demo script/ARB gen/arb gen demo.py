import nifgen
import time

def configure_pxi5423():
    try:
        # Initialize the session
        # Replace with your actual resource name
        session = nifgen.Session("PXIe-5423_01")
        
        # Configure output mode and impedance
        session.output_mode = nifgen.OutputMode.FUNC
        session.output_impedance = 50.0  # Set to 50 ohm
        
        # Configure the waveform
        session.func_waveform = nifgen.Waveform.SQUARE
        session.func_frequency = 5000.0  # 5 kHz
        session.func_amplitude = 3.0     # 3V peak-to-peak
        session.func_duty_cycle = 50.0   # 50% duty cycle
        
        # Configure the trigger
        session.trigger_mode = nifgen.TriggerMode.CONTINUOUS
        
        # Enable the output channel
        session.channels[0].output_enabled = True
        
        # Initiate generation
        session.initiate()
        
        print("Waveform generation started...")
        print("Generating square wave for 5 seconds...")
        
        # Wait for 5 seconds
        time.sleep(5)
        
        # Stop generation and cleanup
        session.abort()
        session.channels[0].output_enabled = False
        print("Waveform generation stopped")
        
        # Close the session
        session.close()
        print("Session closed successfully")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        if 'session' in locals():
            session.close()

if __name__ == "__main__":
    configure_pxi5423()
