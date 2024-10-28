import time

def wait_3_seconds():
    print("Waiting for 3 seconds...")
    time.sleep(3)
    return True

if __name__ == "__main__":
    # For testing the script directly
    result = wait_3_seconds()
    print(f"The function returned: {result}")
