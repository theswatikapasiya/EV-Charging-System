# 🚗⚡ EV Charging Command Center
## Enterprise AI-Powered EV Security & Smart Charging Platform

An enterprise-grade EV charging management and cybersecurity platform designed to simulate, monitor, analyze, and secure EV charging infrastructures using Machine Learning, Blockchain-style logging, Real-Time Analytics, and Threat Detection Systems.

---

# 📌 Project Overview

The EV Charging Command Center is a real-time cybersecurity-integrated EV charging station management system that combines:

- ⚡ Smart EV charging simulation
- 🛡️ AI-powered cyber attack detection
- ⛓️ Blockchain-style immutable logging
- 📊 Advanced analytics dashboard
- 🌐 Real-time WebSocket communication
- 🤖 Machine Learning anomaly detection
- 💳 QR-based billing and payment simulation
- 👨‍💼 Admin security control center

The platform continuously monitors charging sessions, user activity, network requests, and simulated cyber threats while maintaining operational efficiency and charging optimization.

---

# 🎯 Key Features

## ⚡ Smart Charging System
- Real-time EV charging queue management
- Dynamic charging session tracking
- Battery monitoring and charging analytics
- Charging demand prediction
- Smart energy optimization
- Queue congestion analysis
- Automated billing calculations

---

## 🛡️ AI-Powered Cybersecurity Layer
- Machine Learning based anomaly detection
- Isolation Forest attack detection model
- Detection of:
  - DoS Attacks
  - Fake Data Injection
  - Replay Attacks
  - Missing Packet Attacks
- Threat severity scoring
- Risk analysis engine
- Automatic suspicious request blocking
- IP reputation tracking system

---

## ⛓️ Blockchain Security & Immutable Logging
- SHA256 blockchain-style hash chaining
- Tamper-proof audit logging
- Secure transaction verification
- Blockchain integrity validation
- Immutable attack logging
- Cryptographic event verification

---

## 📊 Real-Time Analytics Dashboard
- Live charging analytics
- Real-time revenue tracking
- Energy consumption monitoring
- Threat heatmaps
- Attack frequency visualization
- Peak charging hour analysis
- System efficiency metrics
- Interactive Chart.js visualizations

---

## 🌐 Real-Time Communication
- Flask-SocketIO integration
- Live dashboard synchronization
- Real-time attack notifications
- Dynamic threat updates
- Instant charging session updates
- WebSocket-based event broadcasting

---

## 👨‍💼 Enterprise Admin Control Center
- System health monitoring
- Blockchain verification controls
- Security testing controls
- Queue reset management
- Report generation
- IP blocking center
- Threat monitoring panel

---

# 🏗️ System Architecture

## Backend
- Flask 2.3.3
- Flask-SocketIO
- SQLAlchemy ORM
- JWT Authentication
- SQLite Database

## Frontend
- HTML5
- CSS3
- JavaScript
- Chart.js
- Cyberpunk Neon UI

## Machine Learning
- Scikit-learn
- Isolation Forest
- Feature Extraction Pipeline
- Anomaly Classification Engine

## Security
- SHA256 Cryptographic Hashing
- JWT Token Authentication
- Role-Based Access Control
- Blockchain-style Secure Logging

---

# 🧠 Machine Learning Workflow

The system uses an Isolation Forest anomaly detection model to analyze charging requests and network traffic.

### Features Extracted:
- Charging energy values
- Request frequency
- Payload size
- Request intervals
- Session duration
- Repeated packet patterns

### ML Pipeline:
1. Request enters the server
2. Features are extracted
3. Isolation Forest evaluates anomaly score
4. Threat classification is performed
5. Attack is logged
6. IP reputation score is updated
7. Threat is displayed on dashboard
8. Blockchain log entry is generated

---

# 🔐 Cybersecurity Workflow

## Attack Detection Flow

```text
Incoming Request
       ↓
ML Anomaly Detection
       ↓
Threat Classification
       ↓
Risk Scoring
       ↓
Attack Logging
       ↓
Blockchain Verification
       ↓
Automatic Blocking
       ↓
Dashboard Visualization
```

---

# 📊 Dashboard Modules

## 📌 Dashboard Tab
- Vehicle queue management
- Active charging sessions
- Completed sessions
- Attack distribution graphs
- System logs

## 🛡️ Security Tab
- Threat heatmap
- Suspicious IP table
- Attack timeline
- Threat level meter
- Risk score monitoring

## 📈 Analytics Tab
- Revenue trends
- Charging volume analysis
- Attack frequency analysis
- System efficiency metrics
- Average charging time

## ⚡ Charging Tab
- Smart charging management
- Energy allocation
- Wait time estimation
- Charging optimization

## 👨‍💼 Admin Tab
- System controls
- Blockchain verification
- Queue reset
- Export reports
- Security test triggers
- IP blocking center

---

# 🗃️ Database Models

The platform uses SQLAlchemy ORM with multiple interconnected models:

| Model | Purpose |
|------|------|
| User | Authentication & RBAC |
| Vehicle | Vehicle queue tracking |
| ChargingSession | Charging analytics |
| AttackLog | Cyber attack records |
| Payment | Billing & QR payments |
| Analytics | System metrics |
| CryptoSecureLog | Blockchain logs |

---

# 📡 API Endpoints

## Authentication

```http
POST /auth/register
POST /auth/login
POST /auth/logout
```

## Charging System

```http
POST /add_vehicle
POST /start
POST /stop
GET /status
```

## Security APIs

```http
GET /api/security/threat-level
GET /api/security/threat-heatmap
GET /api/security/ip-reputation
GET /api/security/attacks/timeline
```

## Analytics APIs

```http
GET /analytics/dashboard
GET /analytics/revenue/total
GET /analytics/charging/efficiency
```

## Blockchain APIs

```http
GET /blockchain/verify-chain
GET /blockchain/stats
```

---

# 🧪 Attack Simulation

The system includes attack simulation scripts for cybersecurity testing.

## Simulated Attacks
- DoS Attack
- Fake Data Injection
- Replay Attack
- Missing Packet Attack

## Run Attack Scripts

```bash
cd attacks

python3 dos_attack.py
python3 fake_data_attack.py
python3 replay_attack.py
```

These attacks are automatically:
- detected by ML
- classified
- logged
- visualized
- blocked by the system

---

# 🚀 Installation & Setup

## Clone Repository

```bash
git clone https://github.com/theswatikapasiya/EV-Charging-System.git
cd EV-Charging-System
```

---

## Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

## Start Server

```bash
cd ev-secure-charging/server
python3 app.py
```

Server runs on:

```text
http://localhost:5000
```

---

# 🔑 Default Credentials

## Admin Login

```text
Username: admin
Password: admin123
```


---

# 📁 Project Structure

```text
EV-Charging-System/
│
├── attacks/
│   ├── dos_attack.py
│   ├── fake_data_attack.py
│   └── replay_attack.py
│
├── ev-secure-charging/
│   └── server/
│       ├── app.py
│       ├── models.py
│       ├── analytics.py
│       ├── blockchain_logger.py
│       ├── ml_model.py
│       ├── security_apis.py
│       ├── websocket_events.py
│       ├── templates/
│       ├── static/
│       └── database.db
│
├── README.md
└── requirements.txt
```



---


# 📜 License

This project is developed for educational and research purposes.

---

# ⭐ Final Note

This platform demonstrates how modern EV charging infrastructures can be protected using AI-driven cybersecurity systems, blockchain verification mechanisms, and intelligent monitoring architectures.

The project focuses on building a secure, scalable, and intelligent EV ecosystem capable of detecting and mitigating cyber threats in real time.
