import time

def run(config, argument):
    print("Starting 3-second wait...")
    time.sleep(3)
    print("3-second wait completed.")
    return True

if __name__ == "__main__":
    # For testing the script directly
    result = run({}, "test argument")
    print(f"The function returned: {result}")
