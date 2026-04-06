import requests
import time
import uuid

BASE_URL = "http://127.0.0.1:5000"
VEHICLE_ID = "EV001"

print("Launching Fake Data Injection Attack...")

# ✅ FIXED endpoint (lowercase)
requests.get(f"{BASE_URL}/attack/fake")

# start session
requests.post(f"{BASE_URL}/start", json={"vehicle_id": VEHICLE_ID})

# inject fake data
for i in range(5):
    payload = {
        "vehicle_id": VEHICLE_ID,
        "energy": 500,  # unrealistic energy
        "request_id": str(uuid.uuid4()),
        "timestamp": time.time()
    }

    requests.post(f"{BASE_URL}/data", json=payload)
    print("Injected fake energy:", payload["energy"])
    time.sleep(0.7)

# stop session
response = requests.post(f"{BASE_URL}/stop", json={"vehicle_id": VEHICLE_ID})

try:
    print("Final Response:", response.json())
except:
    print("Final Response (raw):", response.text)