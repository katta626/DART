from flask import Flask, request
import os
import time
from flask import jsonify, send_file
log_files = "log_files"
app = Flask(__name__)

@app.route('/trigger', methods=['POST'])
def trigger_observation():
    data = request.json
    #print("Received parameters:", data)
    #print(type(data))
    # Run your observation code here
    run_observation(data)
    
    return {"status": "observation started"}, 200

def run_observation(params): # it talks with vela PC.
    observation_script = "/home/dsp/PDR_acquire_setup/GBD_DART_lite_obs_script_V5_IQUV_FITS_09_09_2025.sh"
    print("Running observation with:", params)
    
    obs_trigger_cmd = observation_script+" "+str(params["duration"])+" "+str(params["target"])+' '+str(params["countdown"])
    print(obs_trigger_cmd)
    #time.sleep(10000)
    os.system(obs_trigger_cmd)
    # Example: call shell scripts.
    

@app.route('/get-log', methods=['GET'])
def get_log_file():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "Filename parameter missing"}), 400

    safe_filename = os.path.basename(filename)
    log_path = os.path.join(log_files, safe_filename)

    if os.path.exists(log_path):
        return send_file(log_path, as_attachment=True)
    else:
        return jsonify({"error": "Log file not found"}), 404
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)  # open to all IPs on port 5000
