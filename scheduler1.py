import time
import os
import datetime
from pulsar_info import RA
from datastore import DataStore  # ← your SQLite handler
import requests
from urllib.parse import quote
THRESHOLD_SECONDS = 2400000  # Execution threshold in seconds
FILTER_KEYWORDS = [
    "Waiting for", "Observation", "Pulsar:", "ACQ over",
    "Removing Trigger file from remote machine", "Observation stoped",
    "SLIP check", "Pulsar data reduction pipeline started ...",
    "---", "All done!"
]
# Initialize database
db = DataStore("data_store.db")

def read_all_lines(file_path):
    """Read all lines from a log file"""
    if not os.path.exists(file_path):
        return []
    with open(file_path, "r") as f:
        return [line.strip() for line in f.readlines()]

def filter_lines(lines, keywords):
    """Keep only lines containing any of the keywords"""
    if not keywords:
        return lines
    return [line for line in lines if any(k in line for k in keywords)]

def main():
    print("naveen katta")
    changed = False
    # Load all observations and status data
    schedule = {obs["name"]: obs for obs in db.get_all_observations()}
    system_status = db.get_system_status("status_current") or "N/A"
    log_current = db.get_system_status("Log_Current") or ""
    for pulsar, data in schedule.items():
        status = data["status"]
        countdown = data["count_down"]
        duration = data["duration"]
        transit_time = data["transit_time"]
        # ---- DUMMY CHECK ----
        if pulsar == "dummy":
            if countdown < 300:
                db.update_observation(pulsar, status="In Progress")
                data_post = {"target": "dummy", "duration": 10, "countdown": "1000"}
                # requests.post("http://172.16.126.79:5000/trigger", json=data_post)
            if status == "In Progress":
                filename = "obs_2025-09-27_14-30.log"
                log_dir = "log_files"
                os.makedirs(log_dir, exist_ok=True)
                save_path = os.path.join(log_dir, filename)
                # url = f"http://172.17.20.205:5000/get-log?filename={filename}"
                # response = requests.get(url)
                # if response.status_code == 200:
                #     with open(save_path, "wb") as f:
                #         f.write(response.content)
                # Add to Log_Current
                if filename not in log_current:
                    log_current.append(filename)
                    db.update_system_status("Log_Current", log_current)
                    changed = True
        # ---- REAL PULSARS ----
        else:
            if countdown is not None and status != "Not Started":
                # check logs
                time_val = str(transit_time).split()
                log_dir = "log_files"
                log_name = f"{pulsar}_{time_val[0]}_observation.log"
                
                os.makedirs(log_dir, exist_ok=True)
                save_path = os.path.join(log_dir, log_name)
                filename = "1pps_09_09_2025_observation.log"
                file_path = os.path.join("log_files", log_name)
                
                encoded_log_name = quote(log_name) # Encodes '+' to '%2B'
                
                #url = f"http://172.17.20.210:6000/get-log?filename={encoded_log_name}"
                #response = requests.get(url)
                
                #param = {"filename":encoded_log_name}
                #response = requests.get("http://172.17.20.210:6000/get-log", params=param)
                
                #if response.status_code == 200:
                    #with open(save_path, "wb") as f:
                        #f.write(response.content)
                        # add new file if not already present
                if log_name not in log_current:
                    log_current.append(log_name)
                    db.update_system_status("Log_Current", ",".join(log_current))
                for log_name in log_current:
                    lines = read_all_lines(file_path)
                    if lines and "Observation Over." in lines[-1]:
                        db.update_observation(pulsar, status="Not Started")
                        if log_name in log_current:
                            log_current.remove(log_name)
                            db.update_system_status("Log_Current", log_current)
                            changed = True
            if countdown is not None and status == "Not Started":
                # update countdown using RA()
                ra_1, updated_countdown = RA(pulsar)
                new_duration = duration
                updated_countdown -= (new_duration * 60) / 2
                # Update in DB
                db.update_observation(
                    pulsar,
                    count_down=updated_countdown,
                    transit_time=ra_1.strftime('%d_%m_%Y %H:%M:%S')
                )
                changed = True
                # Trigger observation if countdown below threshold
                if updated_countdown <= THRESHOLD_SECONDS:
                    num_files = duration * 2
                    db.update_observation(pulsar, status="In Progress")
                    data_post = {"target": pulsar, "duration": num_files, "countdown": "300"}
                    #requests.post("http://172.17.20.210:6000/trigger", json=data_post)
                    changed = True
    #if changed:
        #print("Database updated with latest observation data.")
    #else:
        #print("No updates required.")

if __name__ == "__main__":
    while True:
        main()
