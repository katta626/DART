import streamlit as st
import pandas as pd
import os
import zipfile
from io import BytesIO
from streamlit.components.v1 import html


st.markdown("""
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css" rel="stylesheet">
""", unsafe_allow_html=True)
st.markdown("""
<nav class="navbar navbar-expand-lg navbar-dark bg-dark">
  <div class="container-fluid">
    <span class="navbar-brand mb-0 h1">🔭 DART - Pulsar Observation Dashboard</span>
    <div class="collapse navbar-collapse">
      <ul class="navbar-nav ms-auto">
        <li class="nav-item">
          <span class="nav-link">Current Time: <span id="time"></span></span>
        </li>
      </ul>
    </div>
  </div>
</nav>

<script>
  function updateTime() {
    const now = new Date();
    document.getElementById("time").textContent = now.toLocaleTimeString();
  }
  setInterval(updateTime, 1000);
  updateTime();
</script>

<style>
    .navbar {
        margin-bottom: 1rem;
    }
    .stApp {
        padding-top: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# --- Load data from CSV ---
df = pd.read_csv("pulsar_data.csv")
df["Observation Time"] = pd.to_datetime(df["Observation Time"])

st.title("Pulsar Observation Table")

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
