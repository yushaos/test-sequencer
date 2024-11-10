#!/usr/bin/env python3
"""
Basic SpaceWire communication demo using STAR-Dundee hardware.
Requires STAR-API Python package to be installed.
"""

import star
import time
from typing import List, Optional

class SpaceWireDemo:
    def __init__(self, device_index: int = 0):
        """Initialize SpaceWire connection using STAR-Dundee device."""
        self.device = None
        self.port = None
        self.device_index = device_index
        
    def initialize(self) -> bool:
        """
        Initialize connection to SpaceWire device.
        Returns True if successful, False otherwise.
        """
        try:
            # Initialize STAR-API
            star.initAPI()
            
            # Get list of available devices
            devices = star.getDeviceList()
            if not devices:
                print("No STAR-Dundee devices found")
                return False
                
            # Open first available device
            self.device = star.openDevice(devices[self.device_index])
            if not self.device:
                print(f"Failed to open device {self.device_index}")
                return False
                
            # Configure first port
            self.port = self.device.port[0]
            
            # Configure link settings
            self.port.linkSpeed = 100  # 100 Mbps
            self.port.autoStart = True
            
            # Start the link
            self.port.link.start()
            
            # Wait for link to establish
            timeout = 5  # seconds
            start_time = time.time()
            while not self.port.link.running:
                if time.time() - start_time > timeout:
                    print("Timeout waiting for link to start")
                    return False
                time.sleep(0.1)
                
            print("SpaceWire link established successfully")
            return True
            
        except Exception as e:
            print(f"Initialization error: {str(e)}")
            return False
            
    def send_message(self, data: List[int]) -> bool:
        """
        Send data over SpaceWire link.
        Args:
            data: List of bytes to send
        Returns:
            True if successful, False otherwise
        """
        try:
            if not self.port or not self.port.link.running:
                print("Link not established")
                return False
                
            # Create packet
            packet = star.Packet(data)
            
            # Send packet
            self.port.tx(packet)
            print(f"Sent {len(data)} bytes")
            return True
            
        except Exception as e:
            print(f"Send error: {str(e)}")
            return False
            
    def receive_message(self, timeout_ms: int = 1000) -> Optional[List[int]]:
        """
        Receive data from SpaceWire link.
        Args:
            timeout_ms: Timeout in milliseconds
        Returns:
            List of received bytes or None if timeout/error
        """
        try:
            if not self.port or not self.port.link.running:
                print("Link not established")
                return None
                
            # Wait for packet
            packet = self.port.rx(timeout_ms)
            if packet:
                data = list(packet.data)
                print(f"Received {len(data)} bytes")
                return data
            else:
                print("Receive timeout")
                return None
                
        except Exception as e:
            print(f"Receive error: {str(e)}")
            return None
            
    def close(self):
        """Clean up SpaceWire connection."""
        try:
            if self.port and self.port.link.running:
                self.port.link.stop()
            if self.device:
                self.device.close()
            star.shutdownAPI()
            print("SpaceWire connection closed")
        except Exception as e:
            print(f"Close error: {str(e)}")

# Example usage
def main():
    # Create SpaceWire interface
    spw = SpaceWireDemo()
    
    # Initialize connection
    if not spw.initialize():
        return
        
    try:
        # Send test message
        test_data = [0x01, 0x02, 0x03, 0x04]
        spw.send_message(test_data)
        
        # Receive response
        received_data = spw.receive_message()
        if received_data:
            print(f"Received data: {[hex(x) for x in received_data]}")
            
    finally:
        # Clean up
        spw.close()

if __name__ == "__main__":
    main()
