from flask import Flask, request, jsonify, render_template, session
from flask_socketio import SocketIO
from models import db, User, Vehicle, ChargingSession, AttackLog, Payment, Analytics, CryptoSecureLog
import time
import random
import uuid
from datetime import datetime, timedelta
import os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ============ FLASK CONFIGURATION ============
app.config['SESSION_COOKIE_SECURE'] = False  # Set to True in production with HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# ============ DATABASE CONFIGURATION ============
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(basedir, "database.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ev-charging-secret-2026-dev')

# Initialize database
db.init_app(app)

# ============ WEBSOCKET CONFIGURATION ============
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')


# ============ DATABASE INITIALIZATION ============
@app.before_request
def initialize_db():
    """Initialize database tables on first request"""
    with app.app_context():
        db.create_all()

def init_sample_data():
    """Initialize sample data if database is empty"""
    with app.app_context():
        if User.query.first() is None:
            # Create default admin user
            admin = User(username='admin', email='admin@ev-charging.com', role='admin', is_active=True)
            admin.set_password('admin123')
            db.session.add(admin)
            
            # Create default operator user
            operator = User(username='operator', email='operator@ev-charging.com', role='operator', is_active=True)
            operator.set_password('operator123')
            db.session.add(operator)
            
            db.session.commit()


# ===== IN-MEMORY LISTS (FOR REAL-TIME DISPLAY) =====
# These maintain the original functionality for the frontend
entered = []
charging = []
completed = []
logs = []
attack_logs = []


# ============ VEHICLE GENERATION ============

def generate_vehicle():
    names = ["Aarav","Vivaan","Aditya","Vihaan","Arjun","Kabir","Riya","Isha","Ananya","Meera",
             "Neha","Karan","Rohit","Priya","Amit","Rahul","Sneha","Ira","Shaurya","Dhruv"]

    return {
        "vehicle_id": f"DL{random.randint(10,99)}AB{random.randint(1000,9999)}",
        "driver": random.choice(names),
        "battery": random.randint(10,60)
    }

# initial load (in-memory for real-time display)
for _ in range(6):
    entered.append(generate_vehicle())


# ============ IMPORT WEBSOCKET EVENTS (after app/socketio initialization) ============
from websocket_events import (
    socketio as ws_socketio,
    emit_attack_detected,
    emit_attack_blocked,
    emit_threat_level_update,
    emit_session_started,
    emit_charging_update,
    emit_session_completed,
    emit_system_event
)


# ============ ATTACK LOGGING (DATABASE + MEMORY) ============

def log_attack_to_db(attack_type, source_ip='127.0.0.1', target='Billing System', severity='medium', description=''):
    """Log attack to database and emit WebSocket event"""
    try:
        attack_log = AttackLog(
            attack_type=attack_type,
            source_ip=source_ip,
            target_system=target,
            severity=severity,
            description=description or f'{attack_type.upper()} ATTACK DETECTED',
            blocked=True,
            mitigation_method='ML Validation'
        )
        attack_log.compute_hash()
        db.session.add(attack_log)
        
        # Log to crypto secure logs
        try:
            admin = User.query.filter_by(role='admin').first()
            secure_log = CryptoSecureLog(
                event_type='attack',
                description=f'{attack_type.upper()} ATTACK DETECTED - Blocked',
                user_id=admin.id if admin else None,
                ip_address=source_ip
            )
            secure_log.compute_hash()
            db.session.add(secure_log)
        except:
            pass
        
        db.session.commit()
        
        # Emit WebSocket events
        try:
            emit_attack_detected({
                'attack_type': attack_type,
                'source_ip': source_ip,
                'target': target,
                'severity': severity,
                'status': 'detected'
            })
            
            emit_attack_blocked({
                'attack_type': attack_type,
                'source_ip': source_ip,
                'mitigation': 'Blocked via ML Validation',
                'status': 'blocked'
            })
            
            # Update threat level
            total_attacks = AttackLog.query.count()
            recent_attacks = AttackLog.query.filter(
                AttackLog.timestamp >= datetime.utcnow() - timedelta(minutes=5)
            ).count()
            
            if recent_attacks > 5:
                threat_level = 'critical'
                risk_score = 95
            elif recent_attacks > 3:
                threat_level = 'high'
                risk_score = 75
            elif recent_attacks > 1:
                threat_level = 'medium'
                risk_score = 50
            else:
                threat_level = 'low'
                risk_score = 25
            
            emit_threat_level_update(threat_level, risk_score)
        except:
            pass
        
    except Exception as e:
        db.session.rollback()
        print(f"Error logging attack: {e}")


# ============ ATTACK ROUTES ============

# ============ ATTACK ROUTES ============

@app.route("/attack/<atype>")
def attack(atype):
    """Log attack event (DoS, Fake, Replay, etc)"""
    # Log to database
    log_attack_to_db(atype.lower())
    
    # Also maintain in-memory for frontend
    attack_logs.append({
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "event": f"{atype.upper()} ATTACK DETECTED",
        "details": "Source IP: 127.0.0.1 | Target: Billing System | Blocked via ML Validation"
    })
    
    return jsonify({"status": "attack logged"})


@app.route("/start", methods=["POST"])
def start():
    """Start charging session"""
    data = request.json or {}
    session_id = str(uuid.uuid4())
    
    # Create database session
    try:
        # Get or create default user
        user = User.query.filter_by(role='operator').first()
        if not user:
            user = User(username='default_op', email='op@ev.com', role='operator')
            user.set_password('password')
            db.session.add(user)
            db.session.commit()
        
        # Create vehicle record
        vehicle_id = data.get('vehicle_id', f"EV_{random.randint(100,999)}")
        vehicle = Vehicle(
            vehicle_id=vehicle_id,
            user_id=user.id,
            driver_name=data.get('driver', 'Unknown'),
            current_battery=data.get('battery', 20),
            battery_percentage=data.get('battery', 20)
        )
        db.session.add(vehicle)
        db.session.flush()
        
        # Create charging session
        session = ChargingSession(
            user_id=user.id,
            vehicle_id=vehicle.id,
            session_id=session_id,
            initial_battery=vehicle.battery_percentage
        )
        session.estimate_completion_time()
        db.session.add(session)
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        print(f"Error creating session: {e}")
    
    return jsonify({"status": "started", "session_id": session_id})


@app.route("/data", methods=["POST"])
def data():
    """Process charging data and detect attacks using ML"""
    payload = request.json or {}
    vehicle_id = payload.get("vehicle_id")
    energy = payload.get("energy", 0)

    # ===== ML ANOMALY DETECTION =====
    try:
        from ml_model import predict_anomaly, detect_attack_type
        
        ml_result = predict_anomaly(payload)
        
        # Update database session with anomaly score
        session = ChargingSession.query.filter_by(
            session_id=payload.get('session_id')
        ).first()
        
        if session:
            session.anomaly_score = ml_result['anomaly_score']
            session.is_suspicious = ml_result['is_anomalous']
            
            if ml_result['is_anomalous']:
                attack_classification = detect_attack_type(payload, ml_result['anomaly_score'])
                suspected_attack = attack_classification['detected_attack']
                
                log_attack_to_db(
                    suspected_attack,
                    description=f'ML detected: {ml_result["prediction"]} (Score: {ml_result["anomaly_score"]:.2f})'
                )
                
                db.session.commit()
                
                attack_logs.append({
                    "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "event": f"ML ATTACK DETECTED: {suspected_attack.upper()}",
                    "details": f"Anomaly Score: {ml_result['anomaly_score']:.2f} | Confidence: {ml_result['confidence']:.1f}% | Blocked"
                })
                
                return jsonify({
                    "status": "blocked",
                    "reason": "ML anomaly detected",
                    "attack_type": suspected_attack,
                    "anomaly_score": ml_result['anomaly_score']
                })
    except Exception as e:
        print(f"ML detection error: {e}")

    # ===== RULE-BASED DETECTION =====
    # Fake attack detection (rule-based backup)
    if energy > 100:
        log_attack_to_db('fake_data', description='Energy value > 100 detected')
        attack_logs.append({
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "event": "FAKE ATTACK DETECTED",
            "details": "Source IP: 127.0.0.1 | Target: Billing System | Blocked via Rule Engine"
        })
        return jsonify({"status": "blocked"})

    return jsonify({"status": "ok"})


@app.route("/stop", methods=["POST"])
def stop():
    """Complete charging session"""
    data = request.json or {}
    vehicle_id = data.get("vehicle_id")
    
    # Finalize session in database
    try:
        session = ChargingSession.query.filter_by(
            session_id=data.get('session_id')
        ).first()
        
        if session:
            session.status = 'completed'
            session.end_time = datetime.utcnow()
            session.calculate_cost()
            db.session.commit()
    except:
        pass
    
    return jsonify({
        "status": "stopped",
        "vehicle_id": vehicle_id
    })



@app.route("/add_vehicle", methods=["POST"])
def add_vehicle():
    """Add new vehicle to queue"""
    data = request.json or {}

    vehicle = {
        "vehicle_id": data["vehicle_id"],
        "driver": data["driver"],
        "battery": int(data["battery"])
    }

    # Add to in-memory queue for frontend
    entered.append(vehicle)
    
    # Also save to database
    try:
        user = User.query.filter_by(role='operator').first() or User.query.first()
        if not user:
            user = User(username='default', email='default@ev.com', role='user')
            user.set_password('pass')
            db.session.add(user)
            db.session.flush()
        
        db_vehicle = Vehicle(
            vehicle_id=data["vehicle_id"],
            user_id=user.id,
            driver_name=data["driver"],
            current_battery=int(data["battery"]),
            battery_percentage=int(data["battery"]),
            status='idle'
        )
        db.session.add(db_vehicle)
        db.session.commit()
        
        # Log to crypto secure logs
        secure_log = CryptoSecureLog(
            event_type='vehicle_registration',
            description=f"Vehicle {data['vehicle_id']} registered: {data['driver']} | Battery: {data['battery']}%",
            user_id=user.id if user else None
        )
        secure_log.compute_hash()
        db.session.add(secure_log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Error adding vehicle to DB: {e}")

    return jsonify({"status": "added"})


# ============ VEHICLE FLOW PROCESSING ============

def process():
    """Main charging simulation loop"""
    
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



# ============ STATUS ENDPOINT ============

@app.route("/status")
def status():
    """Return current system status (in-memory for real-time display)"""
    process()

    return jsonify({
        "entered": entered,
        "charging": charging,
        "completed": completed[-10:],
        "logs": logs[-20:],
        "attack_logs": attack_logs[-20:]
    })


# ============ DATABASE STATUS ENDPOINT ============

@app.route("/api/db/status")
def db_status():
    """Return data from database (for analytics)"""
    try:
        total_vehicles = Vehicle.query.count()
        total_sessions = ChargingSession.query.count()
        total_attacks = AttackLog.query.count()
        active_sessions = ChargingSession.query.filter_by(status='active').count()
        
        return jsonify({
            "total_vehicles": total_vehicles,
            "total_sessions": total_sessions,
            "total_attacks": total_attacks,
            "active_sessions": active_sessions
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ============ FRONTEND ============

@app.route("/")
def home():
    return render_template("index_new.html")


# ============ REGISTER BLUEPRINTS ============

from auth_routes import auth_bp
from ml_routes import ml_bp
from blockchain_routes import blockchain_bp
from analytics_routes import analytics_bp
from advanced_routes import advanced_bp

app.register_blueprint(auth_bp)
app.register_blueprint(ml_bp)
app.register_blueprint(blockchain_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(advanced_bp)


# ============ APP INITIALIZATION ============

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        init_sample_data()
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)