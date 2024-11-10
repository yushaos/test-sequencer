import nidmm
import time
from datetime import datetime

def configure_dmm(session):
    """Configure basic DMM settings"""
    session.configure_measurement_digits(
        measurement_function=nidmm.Function.DC_VOLTS,
        range=10.0,
        resolution_digits=6.5
    )

def get_timestamp():
    """Get current timestamp for measurements"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

def main():
    try:
        # Initialize DMM session
        with nidmm.Session("DMM_01") as session:
            print(f"Connected to: {session.instrument_model}")
            
            # Basic DC Voltage Measurement
            configure_dmm(session)
            print("\n=== DC Voltage Measurement (10V range) ===")
            for i in range(3):
                reading = session.read()
                print(f"{get_timestamp()} - DC Voltage: {reading:.7f} V")
                time.sleep(0.5)
            
            # AC Voltage Measurement
            session.configure_measurement_digits(
                measurement_function=nidmm.Function.AC_VOLTS,
                range=10.0,
                resolution_digits=6.5
            )
            print("\n=== AC Voltage Measurement (10V range) ===")
            for i in range(3):
                reading = session.read()
                print(f"{get_timestamp()} - AC Voltage: {reading:.7f} V")
                time.sleep(0.5)
            
            # Resistance Measurement (2-wire)
            session.configure_measurement_digits(
                measurement_function=nidmm.Function.TWO_WIRE_RES,
                range=1e6,  # 1 MΩ range
                resolution_digits=6.5
            )
            print("\n=== 2-Wire Resistance Measurement ===")
            for i in range(3):
                reading = session.read()
                print(f"{get_timestamp()} - Resistance: {reading:.2f} Ω")
                time.sleep(0.5)
            
            # Current Measurement (DC)
            session.configure_measurement_digits(
                measurement_function=nidmm.Function.DC_CURRENT,
                range=0.1,  # 100mA range
                resolution_digits=6.5
            )
            print("\n=== DC Current Measurement ===")
            for i in range(3):
                reading = session.read()
                print(f"{get_timestamp()} - DC Current: {reading:.7f} A")
                time.sleep(0.5)
            
            # Temperature Measurement (RTD)
            session.configure_measurement_digits(
                measurement_function=nidmm.Function.TEMPERATURE,
                range=100.0,
                resolution_digits=3.5
            )
            session.temp_rtd_type = nidmm.RTDType.PT3851
            
            print("\n=== Temperature Measurement (PT100 RTD) ===")
            for i in range(3):
                reading = session.read()
                print(f"{get_timestamp()} - Temperature: {reading:.3f} °C")
                time.sleep(0.5)

    except nidmm.Error as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    main()
