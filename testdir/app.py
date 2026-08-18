import json
import os
from pulsar_info import RA
import datetime
import subprocess
import sys
import atexit
from streamlit_autorefresh import st_autorefresh
import base64
from astropy.time import Time
import numpy as np
from astropy import units as u
from astropy.coordinates import EarthLocation
from streamlit.components.v1 import html
from dateutil import parser
import runpy
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
import zipfile

st.set_page_config(page_title='DART', page_icon="", initial_sidebar_state="expanded", layout='wide')

FILE_PATH = "pulsar_schedule.json"
FILE_PATH_1 = "status.json"

def load_schedule():
    if os.path.exists(FILE_PATH):
        with open(FILE_PATH, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

def load_status():
    if os.path.exists(FILE_PATH_1):
        with open(FILE_PATH_1, "r") as f:
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

def get_all_time(): 
    IST = str(np.datetime64(datetime.datetime.now()))
    UTC = datetime.datetime.now(datetime.UTC)
    
    observing_time = Time(UTC, scale='utc', location=observing_location)
    LST = observing_time.sidereal_time('mean')
    #LST.to_string(unit=u.hour, sep=':')
    
    return LST, IST

#GBD observatory

longitude = 77.437547;  # degrees
latitude = 13.603839;  # degrees
height = 713;  # meters

observing_location = EarthLocation(lat=latitude*u.deg, lon=longitude*u.deg)

# Get LST (Angle) and IST (ISO string)
lst, ist = get_all_time()

# Extract hours and minutes from LST (Angle)
lst_hms = lst.hms  # namedtuple: (hour, minute, second)
lst_str = f"{int(lst_hms.h):02d}:{int(lst_hms.m):02d}"

# Format IST
ist_dt = parser.parse(ist)
ist_str = ist_dt.strftime('%H:%M')


# Create a shared "initialized" flag on the Streamlit module itself
if not hasattr(st, "app_initialized"):
    schedule = load_schedule()
    for pulsar in list(schedule.keys()):
        schedule[pulsar]["system_data"]["status"] = "Not Started"
    save_schedule(schedule)

    st.app_initialized = True

if "proc" not in st.session_state:
    st.session_state.proc = None

script_path = os.path.join(os.getcwd(), "scheduler.py")

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
     
def main_1():
    set_bg_hack("dart.png")
    st.sidebar.header("Pulsar Observation Scheduler")

    schedule = load_schedule()

    if 'edit_pulsar' not in st.session_state:
        st.session_state.edit_pulsar = None

    config = load_status()

    # Safely get the value of status_current["current"]
    current = config.get("status_current", {}).get("current", "N/A")

    cols_1, cols_2,cols_3 =  st.sidebar.columns([4, 1, 1])

    with cols_1:
        start_1 = st.button("CURRENT SCHEDULE")
    with cols_2:
        refresh = st.button("🔄️")
        save_schedule(schedule)
    with cols_3:
         stat = st.button(current)
    
    if refresh:
        st.rerun()

    if schedule:
        st.sidebar.markdown("""
            <style>
            .custom-table th, .custom-table td {
                padding: 8px 12px;
                text-align: center;
            }
            </style>
        """, unsafe_allow_html=True)

        # Table Header
        cols = st.sidebar.columns([2, 2, 2, 2, 1])
        headers = ["Pulsar", "Duration", "Status", "Transit Time", "Edit"]
        for col, header in zip(cols, headers):
            col.markdown(f"**{header}**")

        for pulsar in list(schedule.keys()):
            details = schedule[pulsar]
            duration = details.get("duration", "N/A")
            system_data = details.get("system_data", {})
            status = system_data.get("status", "Not Started")
            Transit_Time = system_data.get("Transit Time", "Unknown")

            col1, col2, col3, col4, col5 = st.sidebar.columns([2, 2, 2, 2, 1])
            col1.write(pulsar)
            col2.write(duration)
            col3.write(status)
            col4.write(Transit_Time)

            if col5.button("✏️", key=f"edit_{pulsar}"):
                st.session_state.edit_pulsar = pulsar
    else:
        st.sidebar.info("No scheduled pulsars yet.")
    
    col1, col2 = st.sidebar.columns([1,1])

    with col1:
        if st.button("Start Observation", type = 'primary'):
            if st.session_state.proc is None or st.session_state.proc.poll() is not None:
                st.session_state.proc = subprocess.Popen([sys.executable, "scheduler.py"])
                config["status_current"] = {"current":"LIVE 🟢"}
                save_status(config)
                st.success("Started Observtion.")
                st.rerun()
    with col2:
        if st.button("Stop Observation", type = 'primary'):
            if st.session_state.proc is not None:
                st.session_state.proc.terminate()
                st.session_state.proc.wait()
                st.session_state.proc = None
                config["status_current"] = {"current":"❌"}
                save_status(config)
                st.warning("Stopped Observation.")
                st.rerun()
        
    if st.session_state.proc is not None:
        st.session_state.proc = subprocess.Popen([sys.executable, "scheduler.py"])
        config["status_current"] = {"current":"LIVE 🟢"}
    if st.session_state.proc is None:
        config["status_current"] = {"current":"hehehe"}
        save_status(config)

    # Add new pulsar
    with st.sidebar.expander("➕ Add Pulsar"):
        new_pulsar_name = st.text_input("New Pulsar Name")
        new_duration = st.number_input("New Duration (minutes)", min_value=1, step=1)

        if st.button("Add Pulsar"):
            if new_pulsar_name.strip() == "dummy":
                ra_1, countdown = datetime.datetime.now().strftime('%m-%d %H:%M:%S'), (new_duration*60)/2
                system_data = {
                    "status": "Not Started",
                    "Transit Time": ra_1,
                    "Count Down": countdown,
                }
                schedule[new_pulsar_name] = {
                    "duration": new_duration,
                    "system_data": system_data
                }
                save_schedule(schedule)
                st.success(f"Added pulsar '{new_pulsar_name}'.")
                st.rerun()
                
            elif new_pulsar_name.strip() in schedule:
                st.error("Pulsar already exists. Use Edit instead.")
            else:
                new_pulsar_name = new_pulsar_name.strip()

                new_duration_2 = (new_duration*60)/2

                ra_1, countdown = RA(new_pulsar_name) 
                
                target_ist_dt = ra_1 + datetime.timedelta(seconds=new_duration_2)
                ra = target_ist_dt.strftime('%m-%d %H:%M:%S')
                system_data = {
                    "status": "Not Started",
                    "Transit Time": ra,
                    "Count Down": countdown,
                }
                schedule[new_pulsar_name] = {
                    "duration": new_duration,
                    "system_data": system_data
                }
                save_schedule(schedule)
                st.success(f"Added pulsar '{new_pulsar_name}'.")
                st.rerun() 

    # Edit form below table
    if 'edit_pulsar' in st.session_state and st.session_state.edit_pulsar:
        pulsar = st.session_state.edit_pulsar
        details = schedule[pulsar]
        duration = details.get("duration", 1)

        st.sidebar.markdown("---")
        st.sidebar.subheader(f"Edit Schedule: {pulsar}")
        new_duration = st.sidebar.number_input("Duration (minutes)", min_value=1, value=duration)

        if st.sidebar.button("Update Schedule"):
            system_data = details.get("system_data", {"status": "Not Started", "Transit Time": "Unknown", "countdown": new_duration*30})
            schedule[pulsar] = {
                "duration": new_duration,
                "system_data": system_data
            }
            save_schedule(schedule)
            st.success(f"Updated schedule for '{pulsar}'.")
            st.session_state.edit_pulsar = None
            st.rerun()
        if st.sidebar.button("🗑️"):
                del schedule[pulsar]
                save_schedule(schedule)
                st.success(f"Deleted '{pulsar}'")
                st.session_state.edit_pulsar = None
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
    tab1, tab2, tab3 = st.tabs(["LOG UPDATES", "DATA CENTRE", "DIAGNOSTIC PLOTS"])
    with tab1:
        status_data = load_status()
        log_files = status_data.get("Log_Current", {}).get("current_file", [])
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
        # --- Load data from CSV ---
        df = pd.read_csv("pulsar_data.csv")
        df["Observation Time"] = pd.to_datetime(df["Observation Time"])

        # --- Inline filters: Date filter and row selection
        col1, col2 = st.columns([1, 3])

        with col1:
            date_filter = st.date_input("Filter by Observation Date", value=None)

        # Apply filter
        filtered_df = df.copy()
        if date_filter:
            filtered_df = filtered_df[filtered_df["Observation Time"].dt.date == date_filter]

        with col2:
            selected_rows = st.multiselect(
                "Select rows to download .fits",
                filtered_df.index,
                format_func=lambda x: f"{filtered_df.loc[x, 'Pulsar Name']} at {filtered_df.loc[x, 'Observation Time']}"
            )

        # --- Show the filtered table
        st.dataframe(filtered_df)

        # --- Download selected .fits files as zip
        if selected_rows:
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, "w") as zip_file:
                for idx in selected_rows:
                    file_name = filtered_df.loc[idx, "FITS Filename"]
                    file_path = os.path.join("fits_files", file_name)

                    if os.path.exists(file_path):
                        zip_file.write(file_path, arcname=file_name)
                    else:
                        st.warning(f"File not found: {file_name}")

            zip_buffer.seek(0)

            st.download_button(
                label="Download Selected FITS Files as ZIP",
                data=zip_buffer,
                file_name="selected_pulsars.zip",
                mime="application/zip"
            )
        else:
            st.info("Select rows above to enable download.")

    with tab3:

        # Sample data
        df = pd.DataFrame({
            "x": np.linspace(0, 10, 100),
            "y1": np.sin(np.linspace(0, 10, 100)),
            "y2": np.cos(np.linspace(0, 10, 100)),
            "y3": np.tan(np.linspace(0, 10, 100) / 5),
            "y4": np.exp(np.linspace(0, 2, 100))
        })

        # Row 1: First two charts
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Chart 1 - Sine")
            fig1, ax1 = plt.subplots()
            ax1.plot(df["x"], df["y1"])
            st.pyplot(fig1)

        with col2:
            st.subheader("Chart 2 - Cosine")
            fig2, ax2 = plt.subplots()
            ax2.plot(df["x"], df["y2"], color="orange")
            st.pyplot(fig2)

        # Row 2: Next two charts
        col3, col4 = st.columns(2)

        with col3:
            st.subheader("Chart 3 - Tangent")
            fig3, ax3 = plt.subplots()
            ax3.plot(df["x"], df["y3"], color="green")
            st.pyplot(fig3)

        with col4:
            st.subheader("Chart 4 - Exponential")
            fig4, ax4 = plt.subplots()
            ax4.plot(df["x"], df["y4"], color="red")
            st.pyplot(fig4)

            
    st_autorefresh(interval=10000, key="log_refresh")

if __name__ == "__main__":
    main_1()
    main()
