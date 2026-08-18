
#!/usr/bin/env bash
set -euo pipefail

# Keep the data beside this script, regardless of the machine or login name.
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
local_dir="$script_dir/temp_data/transient_hdf5_data"

# This is the remote archive directory selected for the current observation.
remote_dir="/media/vela/GBD_HDF5ARCHIVE/23_07_2026_17_43"

# DART app1.py now reads the HDF5 files directly. No PNG-plotting script or
# separate Streamlit server is started here.
exec "$script_dir/rsync_new_hdf5_files.sh" "$remote_dir" "$local_dir"

