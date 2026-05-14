from flask import Flask, request, jsonify, render_template, session
from flask_socketio import SocketIO
from models import db, User, Vehicle, ChargingSession, AttackLog, Payment, Analytics, CryptoSecureLog
import time
import random
import uuid
from datetime import datetime, timedelta
import os
import re
from blockchain_logger import create_blockchain_log

app = Flask(__name__)

entered = []
charging = []
completed = []
logs = []

attack_stats = {
    "Replay": 0,
    "Fake": 0,
    "Missing": 0,
    "DoS": 0
}
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
            
            # Add the initial queue cars to the database and blockchain
            operator = User.query.filter_by(role='operator').first()
            if operator:
                for v in entered:
                    db_v = Vehicle(
                        vehicle_id=v['vehicle_id'],
                        user_id=operator.id,
                        driver_name=v['driver'],
                        current_battery=v['battery'],
                        battery_percentage=v['battery'],
                        status='idle'
                    )
                    db.session.add(db_v)
                    try:
                        create_blockchain_log(
                            event_type='vehicle_added',
                            description=f"Vehicle {v['vehicle_id']} registered to driver {v['driver']}",
                            user_id=operator.id,
                            ip_address='127.0.0.1'
                        )
                    except:
                        pass
                db.session.commit()

# ===== IN-MEMORY LISTS (FOR REAL-TIME DISPLAY) =====
# These maintain the original functionality for the frontend
entered = []
charging = []
completed = []
logs = []
logs.clear()
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
            create_blockchain_log(
                event_type=f'attack_{attack_type}',
                description=f'{attack_type.upper()} ATTACK DETECTED - Target: {target} | Severity: {severity}',
                user_id=admin.id if admin else None,
                ip_address=source_ip
            )
        except Exception as e:
            print("Blockchain error:", e)
        
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

from security_apis import BANNED_IPS

@app.route("/attack/<atype>")
def attack(atype):
    client_ip = request.remote_addr or "127.0.0.1"
    if client_ip in BANNED_IPS:
        return jsonify({"status": "error", "message": "IP is banned"}), 403


    attack_info = {
        "dos": {
            "impact": "Server flooding attempt detected",
            "severity": "HIGH",
            "target": "Charging Gateway",
            "prevention": "Rate limiting + ML traffic filtering"
        },

        "fake": {
            "impact": "Fake energy injection detected",
            "severity": "CRITICAL",
            "target": "Billing System",
            "prevention": "ML payload validation"
        },

        "replay": {
            "impact": "Repeated packet replay attempt",
            "severity": "MEDIUM",
            "target": "Session Authentication",
            "prevention": "Nonce validation + Timestamp verification"
        },

        "missing": {
            "impact": "Packet loss / interruption detected",
            "severity": "LOW",
            "target": "Charging Session",
            "prevention": "Session monitoring recovery"
        }
    }

    info = attack_info.get(atype.lower(), {
        "impact": "Unknown anomaly",
        "severity": "LOW",
        "target": "System",
        "prevention": "Monitoring"
    })

    attack_logs.append({
    "type": atype.upper(),
    "event": f"{atype.upper()} ATTACK DETECTED",
    "ip": request.remote_addr or "127.0.0.1",
    "target": info.get("target", "System"),
    "impact": info.get("impact", "Unknown Impact"),
    "severity": info.get("severity", "LOW"),
    "prevention": info.get("prevention", "Monitoring"),
    "status": "BLOCKED",
    "time": time.strftime("%Y-%m-%d %H:%M:%S")
})
    log_attack_to_db(
    atype,
    source_ip=request.remote_addr or "127.0.0.1",
    target=info.get("target", "System"),
    severity=info.get("severity", "LOW"),
    description=info.get("impact", "Attack detected")
)

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
        
        try:
            create_blockchain_log(
                event_type='session_started',
                description=f'Charging session started for {vehicle_id}',
                user_id=user.id,
                ip_address=request.remote_addr or '127.0.0.1'
            )
        except:
            pass
        
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

    data = request.json or {}

    vehicle_id = data.get("vehicle_id", "").upper().strip()
    driver = data.get("driver", "").strip()
    battery = int(data.get("battery", 0))

    # ===== VEHICLE NUMBER VALIDATION =====

    vehicle_pattern = r"^[A-Z]{2}[0-9]{2}[A-Z]{1,2}[0-9]{4}$"

    if not re.match(vehicle_pattern, vehicle_id):

        return jsonify({
            "status": "error",
            "message": "Invalid vehicle number"
        }), 400

    # ===== DUPLICATE CHECK =====

    for v in entered + charging:

        if v["vehicle_id"] == vehicle_id:

            return jsonify({
                "status": "error",
                "message": "Vehicle already exists"
            }), 400

    # ===== ML & RTO VALIDATION =====
    from ml_model import validate_vehicle_ml
    validation_result = validate_vehicle_ml(vehicle_id, driver, battery)
    
    if validation_result['is_anomalous']:
        log_attack_to_db(
            'fake_vehicle',
            description=f"ML Blocked: {validation_result.get('threat_type', 'Suspicious Registration')} (Score: {validation_result['anomaly_score']})",
            severity='high'
        )
        return jsonify({
            "status": "error",
            "message": f"Security Block: {validation_result.get('threat_type', 'Vehicle Validation Failed')}"
        }), 403

    # ===== CREATE VEHICLE =====

    vehicle = {
        "vehicle_id": vehicle_id,
        "driver": driver,
        "battery": battery,
        "rto_status": validation_result['rto_status']
    }

    entered.append(vehicle)

    # ===== SAVE TO DATABASE =====

    try:

        user = User.query.filter_by(role='operator').first() or User.query.first()

        if not user:

            user = User(
                username='default',
                email='default@ev.com',
                role='user'
            )

            user.set_password('pass')

            db.session.add(user)
            db.session.flush()

        db_vehicle = Vehicle(
            vehicle_id=vehicle_id,
            user_id=user.id,
            driver_name=driver,
            current_battery=battery,
            battery_percentage=battery,
            status='idle'
        )

        db.session.add(db_vehicle)
        db.session.commit()
        
        # Log to blockchain
        try:
            create_blockchain_log(
                event_type='vehicle_added',
                description=f'Vehicle {vehicle_id} registered to driver {driver}',
                user_id=user.id,
                ip_address=request.remote_addr or '127.0.0.1'
            )
        except:
            pass

    except Exception as e:

        db.session.rollback()

        print("DB ERROR:", e)

    return jsonify({
        "status": "success"
    })


# ============ VEHICLE FLOW PROCESSING ============

# ============ VEHICLE FLOW PROCESSING ============

def process():

    global entered, charging, completed

    # ===== MOVE VEHICLES TO CHARGING =====

    while len(charging) < 5 and entered:

        v = entered.pop(0)

        v["start"] = v["battery"]
        v["current_battery"] = v["battery"]
        v["energy_added"] = 0
        v["session_id"] = str(uuid.uuid4())
        
        # Add to database
        try:
            user = User.query.filter_by(role='operator').first() or User.query.first()
            if not user:
                user = User(username='default', email='default@ev.com', role='user')
                user.set_password('pass')
                db.session.add(user)
                db.session.flush()

            # Find or create vehicle
            db_v = Vehicle.query.filter_by(vehicle_id=v["vehicle_id"]).first()
            if not db_v:
                db_v = Vehicle(
                    vehicle_id=v["vehicle_id"],
                    user_id=user.id,
                    driver_name=v["driver"],
                    current_battery=v["battery"],
                    battery_percentage=v["battery"],
                    status='charging'
                )
                db.session.add(db_v)
                db.session.flush()
            else:
                db_v.status = 'charging'

            cs = ChargingSession(
                user_id=user.id,
                vehicle_id=db_v.id,
                session_id=v["session_id"],
                initial_battery=v["battery"],
                status='active'
            )
            cs.estimate_completion_time()
            db.session.add(cs)
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            print("DB Process Start Error:", e)

        charging.append(v)

    # ===== CHARGING PROCESS =====

    for v in charging[:]:

        increment = random.randint(2, 5)

        v["energy_added"] += increment
        v["current_battery"] += increment

        if v["current_battery"] > 100:
            v["current_battery"] = 100

        # ===== COMPLETE CHARGING =====

        if v["current_battery"] >= 100:

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
            
            # Finalize in DB
            try:
                if "session_id" in v:
                    cs = ChargingSession.query.filter_by(session_id=v["session_id"]).first()
                    if cs:
                        cs.status = 'completed'
                        cs.end_time = datetime.utcnow()
                        cs.energy_added = added
                        cs.calculate_cost()
                        
                        db_v = Vehicle.query.get(cs.vehicle_id)
                        if db_v:
                            db_v.status = 'completed'
                            db_v.current_battery = 100
                            db_v.battery_percentage = 100
                        
                        # Add payment
                        user_id = db_v.user_id if db_v else cs.user_id
                        payment = Payment(
                            user_id=user_id,
                            session_id=cs.id,
                            transaction_id=str(uuid.uuid4()),
                            amount=bill,
                            status='completed',
                            completed_at=datetime.utcnow()
                        )
                        db.session.add(payment)
                        db.session.commit()
                        
                        try:
                            create_blockchain_log(
                                event_type='payment_processed',
                                description=f'Payment of ₹{bill} completed for {v["vehicle_id"]}',
                                user_id=user_id,
                                ip_address='127.0.0.1'
                            )
                        except:
                            pass
            except Exception as e:
                db.session.rollback()
                print("DB Process End Error:", e)

            logs.append({
                "time": time.strftime("%H:%M:%S"),
                "event": "Charging Completed",
                "details": f"{v['vehicle_id']} | Bill ₹{bill}"
            })

            logs.append({

                "time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "Charging Completed",
                "details": f"{v['vehicle_id']} | {v['driver']} | Start:{v['start']}% → +{added}% | ₹{bill}"

            })

    # ===== AUTO GENERATE VEHICLES =====

    while len(entered) < 6:

        new_vehicle = generate_vehicle()

        duplicate = False

        for v in entered + charging + completed:

            if v["vehicle_id"] == new_vehicle["vehicle_id"]:

                duplicate = True
                break

        if not duplicate:

            entered.append(new_vehicle)



# ============ STATUS ENDPOINT ============

@app.route("/status")
def status():

    process()

    total_attacks = len(attack_logs)

    blocked_attacks = len(attack_logs)

    block_rate = 0

    if total_attacks > 0:
        block_rate = int((blocked_attacks / total_attacks) * 100)

    total_revenue = sum(v.get("bill", 0) for v in completed)

    avg_charge_time = 25

    system_efficiency = 0

    total_sessions = len(entered) + len(charging) + len(completed)

    if total_sessions > 0:
        system_efficiency = int((len(completed) / total_sessions) * 100)

    return jsonify({

        # ================= DASHBOARD =================

        "entered": entered,
        "charging": charging,
        "completed": completed[-10:],
        "attack_logs": attack_logs[-20:],
        "logs": logs[-20:],

        "metrics": {
            "total_vehicles": total_sessions,
            "active_sessions": len(charging),
            "total_attacks": total_attacks,
            "block_rate": block_rate
        },

        # ================= ATTACKS =================


        "attack_distribution": {
            "Replay": len([a for a in attack_logs if "REPLAY" in a["event"]]),
            "Fake": len([a for a in attack_logs if "FAKE" in a["event"]]),
            "Missing": len([a for a in attack_logs if "MISSING" in a["event"]]),
            "DoS": len([a for a in attack_logs if "DOS" in a["event"]])
        },

        # ================= SECURITY =================

        "security": {
            "recent_attacks": total_attacks,
            "blocked": blocked_attacks,
            "threat_level": "LOW" if total_attacks < 3 else "MEDIUM"
        },

        # ================= ANALYTICS =================

        "analytics": {
            "total_revenue": total_revenue,
            "avg_session_time": "25m",
            "system_efficiency": system_efficiency,
            "avg_charge_time": avg_charge_time
        }

    })

# ============ DATABASE STATUS ENDPOINT ============

@app.route("/api/db/status")
def db_status():
    """Return data from database (for analytics)"""
    try:
        total_vehicles= len(entered) + len(charging) + len(completed)
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
    return render_template("dashboard.html")


# ============ ADMIN API ENDPOINTS ============

@app.route("/api/admin/reset-queue", methods=["POST"])
def reset_queue():
    """Reset all queues"""
    global entered, charging, completed, logs, attack_logs
    try:
        entered = []
        charging = []
        completed = []
        # Preserve logs for history
        return jsonify({"status": "success", "message": "Queue reset"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/blockchain/verify", methods=["GET"])
def verify_blockchain():
    """Verify blockchain integrity"""
    try:
        crypto_logs = CryptoSecureLog.query.all()
        is_valid = True
        
        for i in range(1, len(crypto_logs)):
            if crypto_logs[i].previous_hash != crypto_logs[i-1].current_hash:
                is_valid = False
                break
        
        return jsonify({
            "status": "success",
            "is_valid": is_valid,
            "total_blocks": len(crypto_logs),
            "timestamp": datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/blockchain/sync", methods=["POST"])
def sync_blockchain():
    """Sync blockchain with latest transactions"""
    try:
        # Create a new block with system state
        admin = User.query.filter_by(role='admin').first()
        secure_log = CryptoSecureLog(
            event_type='sync',
            description=f'Blockchain sync - {len(entered)} queued, {len(charging)} charging, {len(completed)} completed',
            user_id=admin.id if admin else None,
            ip_address='127.0.0.1'
        )
        secure_log.compute_hash()
        db.session.add(secure_log)
        db.session.commit()
        
        return jsonify({
            "status": "success",
            "message": "Blockchain synced",
            "block_hash": secure_log.current_hash
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500


# ============ REGISTER BLUEPRINTS ============

from auth_routes import auth_bp
from ml_routes import ml_bp
from blockchain_routes import blockchain_bp
from analytics_routes import analytics_bp
from advanced_routes import advanced_bp
from security_apis import security_bp

app.register_blueprint(auth_bp)
app.register_blueprint(ml_bp)
app.register_blueprint(blockchain_bp)
app.register_blueprint(analytics_bp)
app.register_blueprint(advanced_bp)
app.register_blueprint(security_bp)


# ============ APP INITIALIZATION ============

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        init_sample_data()
    socketio.run(app, debug=True, host='127.0.0.1', port=5000)