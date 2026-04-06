# ⚡ EV Charging Command Center

A real-time simulation of an EV charging station integrated with cyber attack detection and smart energy management.

---

## 🚀 Features

### 🔌 Smart Charging System
- Vehicles enter a waiting queue (Entered panel)
- Automatically move to Charging panel
- Charging progresses dynamically
- Final bill calculated and shown in Completed panel

---

### 🧾 Vehicle Details
- Vehicle Number (validated using Indian number plate format)
- Driver Name
- Battery percentage
- Charging progress & billing

---

### 🧠 Cyber Attack Detection
Simulates and detects multiple attack types:

- Replay Attack  
- Fake Data Injection  
- DoS Attack  
- Missing Data Attack  

✔️ Attacks are detected and blocked using validation logic  
✔️ Logs are generated in real-time  

---

### 📊 Attack Visualization
- Real-time bar graph (Chart.js)
- Different colors for different attacks
- Hover shows:
  - Target system
  - Impact
  - Prevention method

---

### 📜 Logs System

#### 🔴 Attack Logs
- Type, Details, Timestamp

#### 🟢 Cyber Logs
- Charging completion records
- Energy added and billing details

---

## 🛠️ Tech Stack

- Frontend: HTML, CSS, JavaScript (Chart.js)
- Backend: Flask (Python)
- Simulation: Randomized EV flow + attack scripts

---

## 📂 Project Structure

EVproject/

├── app.py  
├── templates/  
│   └── index.html  
├── attacks/  
│   ├── dos_attack.py  
│   ├── fake_data_attack.py  
│   └── replay_attack.py  

---

## ⚙️ How to Run

1. Install dependencies:
pip install flask

2. Run the server:
python app.py

3. Open in browser:
http://127.0.0.1:5000

---

## 🌐 Live Demo

Currently runs on local server.

To view demo:
1. Clone the repository
2. Run python app.py
3. Open http://127.0.0.1:5000

---

## 🧪 Simulating Attacks

Run attack scripts:

python attacks/dos_attack.py  
python attacks/fake_data_attack.py  
python attacks/replay_attack.py  

---

## 🔐 Security Concept

- Input validation prevents fake energy injection
- Replay detection through repeated payload patterns
- DoS monitored via rapid request spikes
- All attacks are logged and visualized

---

## 📌 Future Scope

- Payment Gateway Integration (UPI / Cards)
- Mobile App Integration
- Cloud Deployment
- AI-based anomaly detection

---

## 👩‍💻 Author

Swati Kapasiya  
B.Tech CSE (Cyber Security)

---

## 🌟 Project Goal

To demonstrate how EV infrastructure can be secured against cyber threats while maintaining efficient real-time operations.
