def run(config, argument):
    print("Hello, World!")
    return True

if __name__ == "__main__":
    # For testing the script directly
    result = run({}, "test argument")
    print(f"The function returned: {result}")
