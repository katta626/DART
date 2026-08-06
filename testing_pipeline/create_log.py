import os
import time

def read_all_lines(file_path):
    """Read all lines from a log file"""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f.readlines()]

def log_file(j_name, directory=".", delay=1):

    # Ensure directory exists
    os.makedirs(directory, exist_ok=True)
    
    log_path = os.path.join(directory, f"{j_name}.log")
    
    # Create the file if it doesn't exist
    if not os.path.exists(log_path):
        open(log_path, "w").close()
    
    # Read lines from another file
    lines = read_all_lines("log_files/J0534+2200_09_09_2025_observation.log")
    
    # Write lines one by one with delay
    with open(log_path, "a") as f:
        for line in lines:
            f.write(line + "\n")
            f.flush()  # Make sure it's written immediately
            time.sleep(delay)
    
    return log_path