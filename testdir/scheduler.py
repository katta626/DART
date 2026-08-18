import json
import time
import os
from pulsar_info import RA
import datetime
import requests

FILE_PATH = "pulsar_schedule.json"
FILE_PATH_1 = "status.json"
THRESHOLD_SECONDS = 100 # Set your execution threshold

# Define which messages to show (keywords)
FILTER_KEYWORDS = ["Waiting for", "Observation", "Pulsar:","ACQ over","Removing Trigger file from remote machine","Observation stoped","SLIP check","Pulsar data reduction pipeline started ...","---","All done!"]  # only show lines containing these

def load_schedule():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def save_schedule(schedule):
    with open(FILE_PATH, "w") as f:
        sorted_items = dict(
            sorted(
                schedule.items(),
                key=lambda item: item[1]["system_data"].get("Count Down", float("inf"))
            )
        )
        json.dump(sorted_items, f, indent=4)

def save_status(status):
    with open(FILE_PATH_1, "w") as f:
        json.dump(status, f, indent=4)

def load_status():
    if os.path.exists(FILE_PATH_1):
        with open(FILE_PATH_1, "r") as f:
            try:

                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def read_all_lines(file_path):
    """Read all lines from the log file"""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f.readlines()]

def filter_lines(lines, keywords):
    """Keep only lines containing any of the keywords"""
    if not keywords:
        return lines  # no filtering
    return [line for line in lines if any(k in line for k in keywords)]

def trigger_observation(pulsar, num_files, trigger_time):
 
    observation_script = "/home/dsp/PDR_acquire_setup/GBD_DART_lite_obs_script_V5_IQUV_FITS_09_09_2025.sh"
 
    start_screen =  "ssh -X dsp@172.17.20.210 screen -dmS "+'"'+ str(pulsar)+'"'
    end_screen   =  "ssh -X dsp@172.17.20.210 screen -S "+'"'+ str(pulsar)+'"'+ " -X  quit"
    obs_trigger_cmd = "ssh -X dsp@172.17.20.210 "+'"screen -R '+'"'+ str(pulsar)+'"' +" -X stuff "+"'"+ str(observation_script)+ " " +str(num_files) + " "+ str(pulsar) + " " +str(trigger_time)+" ^M'"+'"'
 
    os.system(end_screen)          # To kill old screen session
    os.system(start_screen)        # To Start new screen session
    os.system(obs_trigger_cmd)     # Execute commands in new screen session


def main():

    print("naveen katta")
    schedule = load_schedule()
    status_data = load_status()
    changed = False
    
    for pulsar, data in schedule.items():
        if pulsar == "dummy":
            system_data = data.get("system_data", {})
            countdown = system_data.get("Count Down")
            status = system_data.get("status", "Not Started")
            if countdown < 300:
                data = {"target": "dummy",
                    "duration": 10,
                    "countdown": "1000"
                }

                #response = requests.post("http://172.16.126.79:5000/trigger", json=data)
                schedule[pulsar]["system_data"]["status"] = "In Progress"
                
            if status == "In Progress":
                filename = "obs_2025-09-27_14-30.log"
                log_dir = "log_file"  # or absolute path like "/home/navee/logs"
                os.makedirs(log_dir, exist_ok=True)

                # Full path to where you want to save the file
                save_path = os.path.join(log_dir, filename)

                # Correct the URL (your original had a syntax error)
                url = f"http://172.17.20.205:5000/get-log?filename={filename}"


                #response = requests.get(url)

                #if response.status_code == 200:
                    # Always update the file with the latest contents
                    #with open(save_path, "wb") as f:
                        #f.write(response.content)
                                    
                if "Log_Current" not in status_data:
                    status_data["Log_Current"] = {}

                # Ensure "current_file" is a list
                if not isinstance(status_data["Log_Current"].get("current_file"), list):
                    status_data["Log_Current"]["current_file"] = []

                # Append new file if not already present
                if filename not in status_data["Log_Current"]["current_file"]:
                    status_data["Log_Current"]["current_file"].append(filename)
                    changed = True

                                
        if pulsar != "dummy":
            system_data = data.get("system_data", {})
            countdown = system_data.get("Count Down")
            status = system_data.get("status", "Not Started")
            
            if countdown is not None and status != "Not Started":
                time_val = schedule[pulsar]["system_data"]["Transit Time"]
                time_val = time_val.split()
                name = pulsar + "_" + time_val[0] + "_" + "observation.log"
                log_files = status_data.get("Log_Current", {}).get("current_file", [])

                for log_file in log_files:
                    file_path = os.path.join("log_files", log_file)
                    all_lines = read_all_lines(file_path)

                    parts = log_file.split("_")
                    pulsar_name = parts[0] if parts else "Unknown"
                    # Check if file exists before reading
                    if os.path.isfile(file_path):
                        print(f"Reading file: {file_path}")
                        all_lines = read_all_lines(file_path)
                        print(all_lines)

                        parts = log_file.split("_")
                        pulsar_name = parts[0] if parts else "Unknown"

                        # Ensure all_lines is not empty before accessing last line
                        if len(log_files) > 1 and all_lines and "Observation Over." in all_lines[-1]:
                            # Update schedule.json status
                            schedule[pulsar_name]["system_data"]["status"] = "Not Started"
                            if log_file in status_data["Log_Current"]["current_file"]:
                                status_data["Log_Current"]["current_file"].remove(log_file)
                                changed = True
                        else:
                            print(f"File does not exist: {file_path}")
                                # Ensure "Log_Current" exists
                            
                if "Log_Current" not in status_data:
                    status_data["Log_Current"] = {}

                # Ensure "current_file" is a list
                if not isinstance(status_data["Log_Current"].get("current_file"), list):
                    status_data["Log_Current"]["current_file"] = []

                # Append new file if not already present
                if name not in status_data["Log_Current"]["current_file"]:
                    status_data["Log_Current"]["current_file"].append(name)
                    changed = True
                
            if countdown is not None and status == "Not Started":
                # Update countdown using RA()
                ra_1, updated_countdown = RA(pulsar)
                new_duration = schedule[pulsar]["duration"]
                new_duration_2 = (new_duration * 60) / 2
                updated_countdown = updated_countdown - new_duration_2
                schedule[pulsar]["system_data"]["Count Down"] = updated_countdown
                schedule[pulsar]["system_data"]["Transit Time"] = ra_1.strftime('%d_%m_%Y %H:%M:%S')
                changed = True


                # Trigger if countdown is below threshold
                if updated_countdown <= THRESHOLD_SECONDS:
                    duration = schedule[pulsar]["duration"]
                    Num_files = duration*2
                    schedule[pulsar]["system_data"]["status"] = "In Progress"
                    #trigger_observation(pulsar, Num_files, THRESHOLD_SECONDS)
                    data = {"target": pulsar,
                        "duration": Num_files,
                        "countdown": "100"
                    }

                    #response = requests.post("http://172.17.20.205:5000/trigger", json=data)



                    #filename = "obs_2025-09-27_14-30.log"
                    #url = f"http://"http://172.17.20.205:5000/trigger":5000/get-log?filename={filename}"
                    changed = True

    if changed:
        save_schedule(schedule)
        save_status(status_data)

    #time.sleep(1)


if __name__ == "__main__":
    main()
