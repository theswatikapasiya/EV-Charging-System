"""
Database models for EV Charging Management System
SQLAlchemy ORM models for users, vehicles, charging sessions, payments, analytics, and logs
"""

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import hashlib
import json

db = SQLAlchemy()

# ==================== USER MODEL ====================

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user')  # admin, operator, user
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    
    # Relationships
    vehicles = db.relationship('Vehicle', backref='owner', lazy=True, cascade='all, delete-orphan')
    charging_sessions = db.relationship('ChargingSession', backref='user', lazy=True, cascade='all, delete-orphan')
    payments = db.relationship('Payment', backref='user', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat(),
            'is_active': self.is_active
        }


# ==================== VEHICLE MODEL ====================

class Vehicle(db.Model):
    __tablename__ = 'vehicles'
    
    id = db.Column(db.Integer, primary_key=True)
    vehicle_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    driver_name = db.Column(db.String(100), nullable=False)
    battery_capacity = db.Column(db.Float, default=100.0)  # kWh
    current_battery = db.Column(db.Float, nullable=False)
    battery_percentage = db.Column(db.Float, nullable=False)
    status = db.Column(db.String(20), default='idle')  # idle, charging, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    charging_sessions = db.relationship('ChargingSession', backref='vehicle', lazy=True, cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'vehicle_id': self.vehicle_id,
            'driver_name': self.driver_name,
            'battery_capacity': self.battery_capacity,
            'current_battery': self.current_battery,
            'battery_percentage': self.battery_percentage,
            'status': self.status
        }


# ==================== CHARGING SESSION MODEL ====================

class ChargingSession(db.Model):
    __tablename__ = 'charging_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=False)
    session_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime)
    initial_battery = db.Column(db.Float, nullable=False)
    final_battery = db.Column(db.Float)
    energy_added = db.Column(db.Float, default=0)  # kWh
    duration = db.Column(db.Integer)  # seconds
    charging_rate = db.Column(db.Float, default=10.0)  # kW
    estimated_completion = db.Column(db.DateTime)
    actual_completion = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # active, completed, failed, interrupted
    cost = db.Column(db.Float, default=0)
    anomaly_score = db.Column(db.Float, default=0)  # ML anomaly detection score
    is_suspicious = db.Column(db.Boolean, default=False)
    
    # Relationships
    attack_logs = db.relationship('AttackLog', backref='session', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='session', uselist=False, cascade='all, delete-orphan')
    
    def calculate_cost(self, rate_per_kwh=5.0):
        """Calculate charging cost"""
        self.cost = self.energy_added * rate_per_kwh
        return self.cost
    
    def estimate_completion_time(self):
        """Estimate when charging will complete"""
        battery_needed = 100 - self.initial_battery
        # Fallback to 100 if vehicle is not attached yet
        capacity = self.vehicle.battery_capacity if self.vehicle else 100.0
        time_needed = battery_needed / (self.charging_rate / capacity * 100)
        self.estimated_completion = datetime.utcnow() + timedelta(minutes=time_needed)
        return self.estimated_completion
    
    def to_dict(self):
        return {
            'id': self.id,
            'session_id': self.session_id,
            'vehicle_id': self.vehicle.vehicle_id if self.vehicle else None,
            'driver': self.vehicle.driver_name if self.vehicle else None,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'initial_battery': self.initial_battery,
            'final_battery': self.final_battery,
            'energy_added': self.energy_added,
            'status': self.status,
            'cost': self.cost,
            'anomaly_score': self.anomaly_score,
            'is_suspicious': self.is_suspicious
        }


# ==================== ATTACK LOG MODEL ====================

class AttackLog(db.Model):
    __tablename__ = 'attack_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('charging_sessions.id'), nullable=True)
    attack_type = db.Column(db.String(50), nullable=False)  # fake_data, replay, dos, missing_data
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    source_ip = db.Column(db.String(45), nullable=False)
    target_system = db.Column(db.String(100))  # Billing System, Authentication, etc
    severity = db.Column(db.String(20), default='medium')  # low, medium, high, critical
    description = db.Column(db.Text)
    payload = db.Column(db.Text)  # JSON serialized attack payload
    blocked = db.Column(db.Boolean, default=True)
    mitigation_method = db.Column(db.String(255))
    previous_hash = db.Column(db.String(64))  # For blockchain-style logging
    current_hash = db.Column(db.String(64))  # SHA256 hash
    
    def compute_hash(self):
        """Compute SHA256 hash for blockchain-style logging"""
        hash_input = f"{self.timestamp}{self.attack_type}{self.source_ip}{self.previous_hash or ''}"
        self.current_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        return self.current_hash
    
    def to_dict(self):
        return {
            'id': self.id,
            'attack_type': self.attack_type,
            'timestamp': self.timestamp.isoformat(),
            'source_ip': self.source_ip,
            'target_system': self.target_system,
            'severity': self.severity,
            'description': self.description,
            'blocked': self.blocked,
            'mitigation_method': self.mitigation_method
        }


# ==================== PAYMENT MODEL ====================

class Payment(db.Model):
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    session_id = db.Column(db.Integer, db.ForeignKey('charging_sessions.id'), nullable=False)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(3), default='INR')
    payment_method = db.Column(db.String(50))  # credit_card, qr, walletg
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed, refunded
    qr_code = db.Column(db.Text)  # Base64 encoded QR code
    invoice_number = db.Column(db.String(100), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'amount': self.amount,
            'currency': self.currency,
            'status': self.status,
            'invoice_number': self.invoice_number,
            'created_at': self.created_at.isoformat()
        }


# ==================== ANALYTICS MODEL ====================

class Analytics(db.Model):
    __tablename__ = 'analytics'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow, index=True)
    total_sessions = db.Column(db.Integer, default=0)
    total_energy_consumed = db.Column(db.Float, default=0)  # kWh
    total_revenue = db.Column(db.Float, default=0)
    total_attacks_blocked = db.Column(db.Integer, default=0)
    attacks_by_type = db.Column(db.Text)  # JSON: {fake_data: 5, replay: 3, dos: 1}
    average_charging_time = db.Column(db.Float, default=0)  # minutes
    average_session_cost = db.Column(db.Float, default=0)
    peak_charging_hour = db.Column(db.Integer)  # 0-23
    charging_efficiency = db.Column(db.Float, default=0)  # percentage
    suspicious_sessions = db.Column(db.Integer, default=0)
    
    def to_dict(self):
        return {
            'date': self.date.isoformat(),
            'total_sessions': self.total_sessions,
            'total_energy_consumed': self.total_energy_consumed,
            'total_revenue': self.total_revenue,
            'total_attacks_blocked': self.total_attacks_blocked,
            'attacks_by_type': json.loads(self.attacks_by_type or '{}'),
            'average_charging_time': self.average_charging_time,
            'average_session_cost': self.average_session_cost,
            'peak_charging_hour': self.peak_charging_hour,
            'charging_efficiency': self.charging_efficiency,
            'suspicious_sessions': self.suspicious_sessions
        }


# ==================== CRYPTO LOG MODEL ====================

class CryptoSecureLog(db.Model):
    __tablename__ = 'crypto_secure_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    event_type = db.Column(db.String(100), nullable=False)  # system_event, user_action, attack, payment, etc
    description = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    ip_address = db.Column(db.String(45))
    previous_hash = db.Column(db.String(64))  # Blockchain chain
    current_hash = db.Column(db.String(64))  # SHA256
    is_verified = db.Column(db.Boolean, default=True)
    
    def compute_hash(self):
        """Compute blockchain-style hash"""
        hash_input = f"{self.timestamp}{self.event_type}{self.description}{self.previous_hash or ''}"
        self.current_hash = hashlib.sha256(hash_input.encode()).hexdigest()
        return self.current_hash
    
    def verify_integrity(self):
        """Verify if log has been tampered with"""
        expected_hash = hashlib.sha256(
            f"{self.timestamp}{self.event_type}{self.description}{self.previous_hash or ''}".encode()
        ).hexdigest()
        self.is_verified = (expected_hash == self.current_hash)
        return self.is_verified
    
    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'event_type': self.event_type,
            'description': self.description,
            'is_verified': self.is_verified
        }
