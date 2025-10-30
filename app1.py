import datetime
import subprocess
import sys
import os
import streamlit as st
import base64
import pandas as pd
from pulsar_info import RA
import atexit
from datastore import DataStore  # SQLite handler
import numpy as np
import matplotlib.pyplot as plt
from streamlit_autorefresh import st_autorefresh
from io import BytesIO
import zipfile
import re
from PIL import Image

# Initialize database
db = DataStore("data_store.db")

st.set_page_config(page_title='DART', page_icon="☩", initial_sidebar_state="expanded", layout='wide')

if "proc" not in st.session_state:
    st.session_state.proc = None

script_path = os.path.join(os.getcwd(), "scheduler1.py")

# Function to clean up subprocess on exit
def cleanup():
    proc = st.session_state.get("proc")
    if proc is not None and proc.poll() is None:
        proc.terminate()
        proc.wait()
        
atexit.register(cleanup)

def set_bg_hack(main_bg):

    # set bg name
    main_bg_ext = "png"
        
    st.markdown(
         f"""
         <style>
         .stApp {{
             background: url(data:image/{main_bg_ext};base64,{base64.b64encode(open(main_bg, "rb").read()).decode()});
             background-size: cover
         }}
         </style>
         """,
         unsafe_allow_html=True
     )

if not hasattr(st, "app_initialized"):
    db = DataStore("data_store.db")

    # Reset all statuses on app start if needed
    observations = db.get_all_observations()
    for obs in observations:
        db.update_observation(obs["name"], status="Not Started")

    st.app_initialized = True

def main_1():
    set_bg_hack("dart.png")

    # Load all observations from DB
    schedule_list = db.get_all_observations()
    schedule = {obs["name"]: obs for obs in db.get_all_observations(order_by_countdown=True)}
    
    st.sidebar.header("SCHEDULER")

    # Initialize session state flags
    if 'edit_pulsar' not in st.session_state:
        st.session_state.edit_pulsar = None
    if 'edit_mode' not in st.session_state:
        st.session_state.edit_mode = False

    # Load system status from DB
    status_current = db.get_system_status("status_current")
    current_status = status_current or "N/A"
    cols_2, cols_3, cols_1, cols_4 = st.sidebar.columns([2, 2, 4, 3])

    with cols_2:
        # Show the "Edit Pulsar" button
        if st.button("✏️"):
            st.session_state.edit_mode = True  # Activate edit mode

    with cols_3:
        if st.button("➕ Add"):
            st.session_state.add_mode = True  # Activate add mode
    # Display the table
    if schedule:
        data_rows = []
        for pulsar, details in schedule.items():
            data_rows.append({
                "Pulsar": pulsar,
                "Duration": details.get("duration", "N/A"),
                "Status": details.get("status", "Not Started"),
                "Transit Time": details.get("transit_time", "Unknown")
            })

        df = pd.DataFrame(data_rows)
        st.sidebar.dataframe(df, width='stretch')

    else:
        st.sidebar.info("No scheduled pulsars yet.")

    with cols_4:
        obs_running = st.session_state.proc is not None and st.session_state.proc.poll() is None
        button_label = "Stop Observation" if obs_running else "Start Observation"
        
        if st.button(button_label, type="primary"):
            if obs_running:
                # Stop observation safely
                proc = st.session_state.proc
                if proc:
                    proc.terminate()
                    try:
                        proc.wait(timeout=5) # Wait up to 5 seconds for process to exit
                    except subprocess.TimeoutExpired:
                        proc.kill()  # Force kill if not terminated
                    st.session_state.proc = None
                    db.update_system_status("status_current", "❌")
                    st.warning("Stopped Observation.")
            else:
                # Start observation
                st.session_state.proc = subprocess.Popen([sys.executable, "scheduler1.py"])
                db.update_system_status("status_current", "LIVE 🟢")
                st.success("Started Observation.")
            
            st.rerun()



    # Add new pulsar
    if st.session_state.get("add_mode", False):
        with st.sidebar.expander("Add New Pulsar", expanded=True):
            new_pulsar_name = st.text_input("New Pulsar Name")
            new_duration = st.number_input("New Duration (minutes)", min_value=1, step=1)

            if st.button("Confirm Add"):
                name = new_pulsar_name.strip()
                if name == "":
                    st.error("Please enter a pulsar name.")
                    st.session_state.add_mode = False
                elif name in schedule:
                    st.error("Pulsar already exists. Use Edit instead.")
                    st.session_state.add_mode = False
                else:
                    # Special case for 'dummy'
                    if name.lower() == "dummy":
                        ra_1 = datetime.datetime.now()
                        countdown = (new_duration * 60) / 2
                        transit_time = ra_1.strftime('%m-%d %H:%M:%S')
                    else:
                        ra_1, countdown = RA(name)
                        countdown /= 2
                        transit_time = (ra_1 + datetime.timedelta(seconds=countdown)).strftime('%m-%d %H:%M:%S')

                    # Add to DB
                    db.add_or_update_observation(
                        name=name,
                        duration=new_duration,
                        status="Not Started",
                        transit_time=transit_time,
                        count_down=countdown
                    )

                    st.success(f"Added pulsar '{name}'.")
                    st.session_state.add_mode = False  # Hide the form
                    st.rerun()

    # Edit existing pulsar
    # Show edit expander only if edit_mode is True
    if schedule and st.session_state.edit_mode:
        with st.sidebar.expander("✏️ Edit Pulsar", expanded=True):
            # Dropdown to select pulsar
            selected_pulsar = st.selectbox(
                "Select Pulsar to Edit",
                options=list(schedule.keys()),
                index=0
            )

            if selected_pulsar:
                details = schedule[selected_pulsar]

                duration = details.get("duration", 1)
                status = details.get("status", "Not Started")
                transit_time = details.get("transit_time", datetime.datetime.now().strftime('%d_%m_%Y %H:%M:%S'))
                count_down = details.get("count_down", duration * 30)

                # Editable fields
                new_duration = st.number_input(
                    "Duration (minutes)",
                    min_value=1,
                    value=duration,
                    step=1
                )

                if st.button("Update Schedule"):
                    # Update DB
                    db.add_or_update_observation(
                        name=selected_pulsar,
                        duration=new_duration,
                        status=status,
                        transit_time=transit_time,
                        count_down=count_down
                    )

                    # Update local schedule dict for UI
                    schedule[selected_pulsar]["duration"] = new_duration
                    schedule[selected_pulsar]["status"] = new_status

                    st.success(f"Updated schedule for '{selected_pulsar}'.")
                    st.session_state.edit_mode = False  # Close edit mode
                    st.rerun()
                if st.button("Delete Schedule", type="secondary"):
                    db.delete_observation(selected_pulsar)  # Remove from DB
                    schedule.pop(selected_pulsar, None)     # Remove from local cache
                    st.warning(f"🗑️ Deleted schedule for '{selected_pulsar}'.")
                    st.session_state.edit_mode = False
                    st.rerun()
                    
                    
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
    tab1, tab2, tab3 = st.tabs(["LOG UPDATES", "🌀 Pulsar Data Archive", "DIAGNOSTIC PLOTS"])
    with tab1:
        #log_current_str = db.get_system_status("Log_Current") or ""
        #log_files = log_current_str.split(",") if log_current_str else []
        log_files = db.get_system_status("Log_Current") or []
        # Ensure it's always a list
        if isinstance(log_files, str):
            log_files = [log_files]
        print(log_files)
        FILTER_KEYWORDS = ["Waiting for", "Observation", "Pulsar:", "ACQ over","Removing Trigger file from remote machine", "Observation stoped","SLIP check", "Pulsar data reduction pipeline started ...","---", "All done!"]

        if not log_files:
            st.warning("No log files found in status.json")
            
        # Loop through all log files in the list
        for log_file in log_files:
            file_path = os.path.join("log_files", log_file)

            with st.expander(f"Show Log Updates: {log_file}", expanded=False):
                all_lines = read_all_lines(file_path)
                filtered_lines = filter_lines(all_lines, FILTER_KEYWORDS)

                if filtered_lines:
                    st.text("\n".join(filtered_lines[:]))  # show last 5 lines
                    
                else:
                    st.text("No matching logs yet.")
                    
    with tab2:
        def get_image_from_disk(path_to_image):
            """Load image from disk as PIL Image object."""
            return Image.open(path_to_image)

        def image_to_base64(img):
            if img:
                with BytesIO() as buffer:
                    img.save(buffer, "png")
                    raw_base64 = base64.b64encode(buffer.getvalue()).decode()
                    return f"data:image/png;base64,{raw_base64}"
        
        BASE_DIR = "/Users/naveenkatta/Downloads/DART/fits_plots"  # Each subfolder = Pulsar Name

        # --- Step 1: List available pulsars ---
        if not os.path.exists(BASE_DIR):
            print(f"Plots directory '{BASE_DIR}' not found.")

        pulsars = [d for d in os.listdir(BASE_DIR) if os.path.isdir(os.path.join(BASE_DIR, d))]
        if not pulsars:
            print("No pulsar folders found inside 'plots/'.")
        df = pd.DataFrame(columns=["Pulsar", "FITS", "PNG", "Observation Dates"])
        for selected_pulsar in pulsars:
            pulsar_dir = os.path.join(BASE_DIR, selected_pulsar)
            files = os.listdir(pulsar_dir)
            fits_files = [f for f in files if f.endswith(".fits")]
            png_files = [f for f in files if f.endswith(".png")]

            print(f"{selected_pulsar}: {len(fits_files)} FITS files, {len(png_files)} PNG files")
            for f in fits_files:
                match = re.search(r'(\d{2})_(\d{2})_(\d{4})', f)
                if match:
                    day, month, year = match.groups()
                    print(f"File: {f} => Date: {day}-{month}-{year}")
                    image_path = pulsar_dir + "/" + f.replace(".fits", ".png")
                    image_path = image_to_base64(get_image_from_disk(image_path))
                    df.loc[len(df)] = [selected_pulsar ,f , image_path, f"{day}-{month}-{year}"]
                    
        st.data_editor(
                        df,
                        column_config={
                            "PNG": st.column_config.ImageColumn(
                                "Preview Image", help="Streamlit app preview screenshots",
                                width = "small"
                            )
                        },
                        hide_index=True
                    )



    with tab3:
        # Row 1: First two images
        #col1, col2 = st.columns(2)

        #with col1:
            #st.image("/home/summer/Pictures/transient_hdf5/plots/combined_1hr_plot/one_hr_plot.png", use_container_width=True)

        #with col2:
            #st.image("/home/summer/Pictures/transient_hdf5/plots/onefile_plot/cc_tseries_phase.png", use_container_width=True)

        # Row 2: Next two images
        col3, col4 = st.columns(2)

        #with col3:
            #st.image("/home/summer/Pictures/transient_hdf5/plots/spectrogram/spectrogram.png", use_container_width=True)

        #with col4:
            #st.image("/home/summer/Pictures/transient_hdf5/plots/pearson_CC/Pearson_Corr_coeff.png", use_container_width=True)

            
    st_autorefresh(interval=10000, key="log_refresh")


if __name__ == "__main__":
    main_1()
    main()
