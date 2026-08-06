import requests
import json

data = {
    "target": "J0437-4715",
    "duration": 300,
    "countdown": "100"
}

response = requests.post("http://172.16.126.79:5000/trigger", json=data)

filename = "1pps_09_09_2025_observation.log"
url = f"http://172.17.20.205:5000/get-log?filename={filename}"

response = requests.get(url)

if response.status_code == 200:
    with open(filename, "wb") as f:
        f.write(response.content)
    print("Log downloaded successfully")
else:
    print("Error:", response.json())
