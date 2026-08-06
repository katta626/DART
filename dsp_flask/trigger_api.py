from flask import Flask, request
import os
from flask import jsonify, send_file
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

LOG_DIR = ""
OBSERVATION_SCRIPT_PATH = ""

app = Flask(__name__)

@app.route('/trigger', methods=['POST'])
def trigger_observation():
    data = request.json
    #print("Received parameters:", data)
    #print(type(data))
    # Run your observation code here
    #run_observation(data)
    
    return {"status": "observation started"}, 200

def run_observation(params): # it talks with vela PC.
    if not OBSERVATION_SCRIPT_PATH:
        raise RuntimeError("Configure [observation].script in dart_settings.toml before running observations.")

    obs_trigger_cmd = (
        OBSERVATION_SCRIPT_PATH
        + " "
        + str(params["duration"])
        + " "
        + str(params["target"])
        + " "
        + str(params["countdown"])
    )
    print(obs_trigger_cmd)
    os.system(obs_trigger_cmd)
    # Example: call shell scripts.
    

@app.route('/get-log', methods=['GET'])
def get_log_file():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "Filename parameter missing"}), 400

    safe_filename = os.path.basename(filename)
    log_path = os.path.join(LOG_DIR, safe_filename)

    if os.path.exists(log_path):
        return send_file(log_path, as_attachment=True)
    else:
        return jsonify({"error": "Log file not found"}), 404
        

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)  # open to all IPs on port 5000
