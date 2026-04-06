import requests
import time
import uuid
import random
import threading

BASE_URL = "http://127.0.0.1:5000"

def simulate_vehicle():
    vehicle_id = f"EV_{random.randint(100,999)}"
    print(f"🚗 {vehicle_id} entered")

    try:
        # start
        requests.post(f"{BASE_URL}/start", json={"vehicle_id": vehicle_id})

        for _ in range(5):
            payload = {
                "vehicle_id": vehicle_id,
                "energy": random.randint(1,3),
                "request_id": str(uuid.uuid4()),
                "timestamp": time.time()
            }

            requests.post(f"{BASE_URL}/data", json=payload)
            time.sleep(1)

        # stop
        res = requests.post(f"{BASE_URL}/stop", json={"vehicle_id": vehicle_id})

        # ✅ SAFE JSON HANDLING
        try:
            print(f"💰 {vehicle_id} bill:", res.json())
        except:
            print(f"⚠️ {vehicle_id} server response (non-json):", res.text)

    except Exception as e:
        print(f"❌ ERROR for {vehicle_id}:", e)


# MULTI VEHICLE SIMULATION
while True:
    threading.Thread(target=simulate_vehicle).start()
    time.sleep(random.randint(2,4))