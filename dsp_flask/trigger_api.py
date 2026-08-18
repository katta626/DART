from flask import Flask, request, jsonify, send_file
import os
import shutil
import subprocess

log_files = "/home/dsp/PDR_acquire_setup/master_obs_log"
observation_script = "/home/dsp/PDR_acquire_setup/GBD_DART_lite_obs_script_V5_IQUV_FITS_09_09_2025.sh"

app = Flask(__name__)


@app.route('/trigger', methods=['POST'])
def trigger_observation():
    data = request.json
    print("Received parameters:", data)
    run_observation(data)
    return {"status": "observation started"}, 200


def run_observation(params):
    obs_cmd = (
        observation_script + " "
        + str(params["duration"]) + " "
        + str(params["target"]) + " "
        + str(params["countdown"])
    )

    start_screen = 'screen -dmS "' + str(params["target"]) + '"'
    end_screen = 'screen -S "' + str(params["target"]) + '" -X quit'
    obs_trigger_cmd = "screen -S " + str(params["target"]) + " -X stuff " + "' " + str(obs_cmd) + " ^M'"

    os.system(end_screen)
    os.system(start_screen)
    os.system(obs_trigger_cmd)


@app.route('/get-log', methods=['GET'])
def get_log_file():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "Filename parameter missing"}), 400

    log_path = log_files + "/" + filename
    print(filename, log_path)

    if os.path.exists(log_path):
        return send_file(log_path, as_attachment=True)
    return jsonify({"error": "Log file not found"}), 404


@app.route('/get-prms', methods=['GET'])
def get_prms():
    total, used, free = shutil.disk_usage(log_files)
    gb = 1024 ** 3
    return jsonify({
        "total": f"{total / gb:.2f} GB",
        "used": f"{used / gb:.2f} GB",
        "free": f"{free / gb:.2f} GB",
    }), 200


@app.route('/observation-over', methods=['POST'])
def observation_over():
    pulsar_name = request.args.get("pulsar_name")
    if not pulsar_name:
        return jsonify({"error": "pulsar_name parameter missing"}), 400
    
    end_screen = 'screen -S "' + pulsar_name + '" -X quit'
    os.system(end_screen)
    
    print(f"Observation over received for {pulsar_name}")
    return jsonify({"status": "received", "pulsar_name": pulsar_name}), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)
