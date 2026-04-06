from flask import Flask, request, jsonify, render_template
import time
import random

app = Flask(__name__)

entered = []
charging = []
completed = []
logs = []
attack_logs = []

# ---------------- VEHICLE SYSTEM ---------------- #

def generate_vehicle():
    names = ["Aarav","Vivaan","Aditya","Vihaan","Arjun","Kabir","Riya","Isha","Ananya","Meera",
             "Neha","Karan","Rohit","Priya","Amit","Rahul","Sneha","Ira","Shaurya","Dhruv"]

    return {
        "vehicle_id": f"DL{random.randint(10,99)}AB{random.randint(1000,9999)}",
        "driver": random.choice(names),
        "battery": random.randint(10,60)
    }

# initial load
for _ in range(6):
    entered.append(generate_vehicle())

# ---------------- ATTACK ROUTES ---------------- #

@app.route("/attack/<atype>")
def attack(atype):
    attack_logs.append({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": f"{atype.upper()} ATTACK DETECTED",
        "details": "Source IP: 127.0.0.1 | Target: Billing System | Blocked via ML Validation"
    })
    return jsonify({"status": "attack logged"})


@app.route("/start", methods=["POST"])
def start():
    return jsonify({"status": "started"})


@app.route("/data", methods=["POST"])
def data():
    payload = request.json

    # Fake attack detection
    if payload.get("energy", 0) > 100:
        attack_logs.append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": "FAKE ATTACK DETECTED",
            "details": "Source IP: 127.0.0.1 | Target: Billing System | Blocked via ML Validation"
        })
        return jsonify({"status": "blocked"})

    return jsonify({"status": "ok"})


@app.route("/stop", methods=["POST"])
def stop():
    data = request.json
    return jsonify({
        "status": "stopped",
        "vehicle_id": data.get("vehicle_id")
    })


@app.route("/add_vehicle", methods=["POST"])
def add_vehicle():
    data = request.json

    vehicle = {
        "vehicle_id": data["vehicle_id"],
        "driver": data["driver"],
        "battery": int(data["battery"])
    }

    entered.append(vehicle)
    return jsonify({"status": "added"})


# ---------------- VEHICLE FLOW ---------------- #

def process():

    if len(charging) < 5 and entered:
        v = entered.pop(0)
        v["start"] = v["battery"]
        v["energy_added"] = 0
        charging.append(v)

    for v in charging[:]:
        v["energy_added"] += random.randint(2,5)

        if v["energy_added"] >= (100 - v["start"]):
            charging.remove(v)

            added = 100 - v["start"]
            bill = added * 10

            completed.append({
                "vehicle_id": v["vehicle_id"],
                "driver": v["driver"],
                "battery_start": v["start"],
                "energy_added": added,
                "bill": bill
            })

            logs.append({
                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "Charging Completed",
                "details": f"{v['vehicle_id']} | {v['driver']} | Start:{v['start']}% → +{added}% | ₹{bill}"
            })

    while len(entered) < 6:
        entered.append(generate_vehicle())


# ---------------- STATUS ---------------- #

@app.route("/status")
def status():
    process()

    return jsonify({
        "entered": entered,
        "charging": charging,
        "completed": completed[-10:],
        "logs": logs[-20:],
        "attack_logs": attack_logs[-20:]   # ✅ FIXED
    })


# ---------------- FRONTEND ---------------- #

@app.route("/")
def home():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)