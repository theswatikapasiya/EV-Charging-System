"""
Machine Learning Attack Detection System
Uses Isolation Forest and statistical analysis for anomaly detection
Detects:
- Fake data injection attacks
- Replay attacks
- Unusual charging patterns
- Billing manipulation attempts
"""

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
import joblib
import os
from datetime import datetime, timedelta
from models import ChargingSession, AttackLog, db

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'models')
if not os.path.exists(MODEL_PATH):
    os.makedirs(MODEL_PATH)

ISOLATION_FOREST_MODEL = os.path.join(MODEL_PATH, 'isolation_forest.pkl')
SCALER_MODEL = os.path.join(MODEL_PATH, 'scaler.pkl')

# ==================== FEATURE EXTRACTION ====================

def extract_features_from_session(session_data):
    """Extract ML features from charging session"""
    features = {
        'energy_value': session_data.get('energy', 0),
        'request_interval': session_data.get('interval', 1),
        'battery_level': session_data.get('battery', 50),
        'charging_duration': session_data.get('duration', 60),
        'request_frequency': session_data.get('frequency', 1),
        'payload_size': session_data.get('payload_size', 100),
        'repeated_payloads': session_data.get('repeated', 0),
        'energy_spike': abs(session_data.get('energy', 0) - session_data.get('prev_energy', 0)),
        'request_deviation': session_data.get('deviation', 0),
        'timestamp_gap': session_data.get('timestamp_gap', 0)
    }
    return features


def features_dict_to_array(features):
    """Convert features dict to numpy array for model"""
    feature_order = [
        'energy_value', 'request_interval', 'battery_level', 'charging_duration',
        'request_frequency', 'payload_size', 'repeated_payloads', 'energy_spike',
        'request_deviation', 'timestamp_gap'
    ]
    return np.array([[features.get(f, 0) for f in feature_order]])


# ==================== MODEL TRAINING ====================

def generate_synthetic_training_data(n_samples=1000):
    """Generate synthetic training data for model"""
    np.random.seed(42)
    
    # Normal charging patterns
    normal_samples = []
    for _ in range(n_samples // 2):
        sample = {
            'energy_value': np.random.normal(5, 2),  # Normal range: 1-10
            'request_interval': np.random.normal(1, 0.3),
            'battery_level': np.random.uniform(20, 100),
            'charging_duration': np.random.normal(300, 50),
            'request_frequency': np.random.normal(1, 0.2),
            'payload_size': np.random.normal(100, 20),
            'repeated_payloads': np.random.poisson(0.5),
            'energy_spike': np.random.exponential(1),
            'request_deviation': np.random.normal(0, 0.1),
            'timestamp_gap': np.random.exponential(1),
            'label': 0  # Normal
        }
        normal_samples.append(sample)
    
    # Attack patterns
    attack_samples = []
    for _ in range(n_samples // 2):
        attack_type = np.random.choice(['fake_data', 'replay', 'dos', 'missing_data'])
        
        if attack_type == 'fake_data':
            sample = {
                'energy_value': np.random.uniform(50, 150),  # Fake high values
                'request_interval': np.random.normal(1, 0.3),
                'battery_level': np.random.choice([0, 100]),
                'charging_duration': np.random.uniform(10, 30),
                'request_frequency': np.random.normal(1, 0.2),
                'payload_size': np.random.uniform(200, 1000),
                'repeated_payloads': np.random.poisson(3),
                'energy_spike': np.random.exponential(10),
                'request_deviation': np.random.normal(0, 5),
                'timestamp_gap': np.random.exponential(0.1),
                'label': 1  # Attack
            }
        elif attack_type == 'replay':
            sample = {
                'energy_value': np.random.normal(5, 0.1),  # Repeated exact values
                'request_interval': np.random.normal(5, 0.2),
                'battery_level': np.random.normal(50, 0.5),
                'charging_duration': np.random.normal(300, 2),
                'request_frequency': np.random.uniform(5, 20),  # Very high
                'payload_size': np.random.normal(100, 5),
                'repeated_payloads': np.random.poisson(10),  # Many repeats
                'energy_spike': np.random.normal(0, 0.05),
                'request_deviation': np.random.uniform(10, 50),
                'timestamp_gap': np.random.exponential(0.2),
                'label': 1  # Attack
            }
        elif attack_type == 'dos':
            sample = {
                'energy_value': np.random.uniform(0, 200),
                'request_interval': np.random.uniform(0.01, 0.1),  # Very frequent
                'battery_level': np.random.uniform(0, 100),
                'charging_duration': np.random.uniform(1, 10),
                'request_frequency': np.random.uniform(100, 1000),  # Extremely high
                'payload_size': np.random.uniform(1000, 5000),
                'repeated_payloads': np.random.poisson(20),
                'energy_spike': np.random.exponential(50),
                'request_deviation': np.random.uniform(20, 100),
                'timestamp_gap': np.random.exponential(0.01),
                'label': 1  # Attack
            }
        else:  # missing_data
            sample = {
                'energy_value': 0,
                'request_interval': np.random.exponential(10),
                'battery_level': np.random.uniform(20, 100),
                'charging_duration': np.random.uniform(200, 400),
                'request_frequency': np.random.uniform(0, 0.5),  # Very low
                'payload_size': np.random.normal(50, 10),
                'repeated_payloads': 0,
                'energy_spike': 0,
                'request_deviation': np.random.normal(0, 2),
                'timestamp_gap': np.random.exponential(5),
                'label': 1  # Attack
            }
        
        attack_samples.append(sample)
    
    all_samples = normal_samples + attack_samples
    df = pd.DataFrame(all_samples)
    return df


def train_isolation_forest(n_samples=1000):
    """Train Isolation Forest for unsupervised anomaly detection"""
    
    print("🤖 Generating synthetic training data...")
    df = generate_synthetic_training_data(n_samples)
    
    # Feature columns
    feature_cols = [
        'energy_value', 'request_interval', 'battery_level', 'charging_duration',
        'request_frequency', 'payload_size', 'repeated_payloads', 'energy_spike',
        'request_deviation', 'timestamp_gap'
    ]
    
    X = df[feature_cols].values
    
    # Scale features
    print("📊 Scaling features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Train model
    print("🧠 Training Isolation Forest...")
    iso_forest = IsolationForest(
        contamination=0.3,  # Expect ~30% anomalies during training
        random_state=42,
        n_estimators=100
    )
    iso_forest.fit(X_scaled)
    
    # Save models
    joblib.dump(iso_forest, ISOLATION_FOREST_MODEL)
    joblib.dump(scaler, SCALER_MODEL)
    
    print("✅ Models trained and saved")
    
    # Evaluate
    predictions = iso_forest.predict(X_scaled)
    scores = iso_forest.score_samples(X_scaled)
    
    print(f"Train accuracy: {np.mean(predictions[df['label']==0] == -1) * 100:.2f}% detection on normal samples")
    print(f"Train recall: {np.mean(predictions[df['label']==1] == -1) * 100:.2f}% detection on attack samples")
    
    return iso_forest, scaler


def load_or_train_model():
    """Load existing model or train new one"""
    if os.path.exists(ISOLATION_FOREST_MODEL) and os.path.exists(SCALER_MODEL):
        print("📂 Loading trained models...")
        iso_forest = joblib.load(ISOLATION_FOREST_MODEL)
        scaler = joblib.load(SCALER_MODEL)
        return iso_forest, scaler
    else:
        print("🚀 No models found. Training new models...")
        return train_isolation_forest()


# ==================== PREDICTION & ANOMALY DETECTION ====================

def predict_anomaly(session_data):
    """Predict if session contains anomalies"""
    try:
        iso_forest, scaler = load_or_train_model()
        
        # Extract features
        features = extract_features_from_session(session_data)
        X = features_dict_to_array(features)
        
        # Scale
        X_scaled = scaler.transform(X)
        
        # Predict: -1 = anomaly, 1 = normal
        prediction = iso_forest.predict(X_scaled)[0]
        anomaly_score = -iso_forest.score_samples(X_scaled)[0]  # Convert to positive
        
        # Normalize anomaly score to 0-100
        anomaly_probability = min(100, max(0, anomaly_score * 10))
        
        is_anomalous = prediction == -1
        
        return {
            'is_anomalous': is_anomalous,
            'anomaly_score': float(anomaly_score),
            'anomaly_probability': float(anomaly_probability),
            'confidence': float(min(100, anomaly_probability)),
            'prediction': 'Suspicious' if is_anomalous else 'Normal',
            'features': features
        }
    
    except Exception as e:
        print(f"Error in prediction: {e}")
        return {
            'is_anomalous': False,
            'anomaly_score': 0,
            'anomaly_probability': 0,
            'confidence': 0,
            'prediction': 'Unknown',
            'features': {}
        }


def detect_attack_type(session_data, anomaly_score):
    """Classify attack type based on features"""
    features = session_data if isinstance(session_data, dict) else extract_features_from_session(session_data)
    
    energy = features.get('energy_value', 0)
    interval = features.get('request_interval', 1)
    frequency = features.get('request_frequency', 1)
    repeated = features.get('repeated_payloads', 0)
    spike = features.get('energy_spike', 0)
    
    attack_scores = {
        'fake_data': 0,
        'replay': 0,
        'dos': 0,
        'missing_data': 0
    }
    
    # Fake data signature: very high energy values
    if energy > 50:
        attack_scores['fake_data'] += 0.8
    
    # Replay signature: high frequency, low variation
    if frequency > 5 and spike < 1:
        attack_scores['replay'] += 0.8
    
    # DoS signature: extremely high frequency
    if frequency > 20:
        attack_scores['dos'] += 0.9
    
    # Missing data signature: zero values
    if energy == 0:
        attack_scores['missing_data'] += 0.8
    
    # High anomaly score indicates attack
    if anomaly_score > 0.5:
        for attack_type in attack_scores:
            attack_scores[attack_type] += 0.5
    
    detected_attack = max(attack_scores, key=attack_scores.get)
    confidence = attack_scores[detected_attack]
    
    return {
        'detected_attack': detected_attack if confidence > 0.4 else 'unknown',
        'confidence': min(100, confidence * 100),
        'scores': attack_scores
    }


# ==================== ANALYTICS ====================

def calculate_ml_threat_level(period_minutes=10):
    """Calculate current ML-based threat level"""
    try:
        cutoff_time = datetime.utcnow() - timedelta(minutes=period_minutes)
        
        recent_sessions = ChargingSession.query.filter(
            ChargingSession.start_time >= cutoff_time
        ).all()
        
        if not recent_sessions:
            return {
                'threat_level': 'low',
                'risk_score': 10,
                'suspicious_count': 0,
                'total_sessions': 0
            }
        
        suspicious_count = sum(1 for s in recent_sessions if s.is_suspicious)
        suspicious_rate = (suspicious_count / len(recent_sessions)) * 100
        
        if suspicious_rate > 30:
            threat_level = 'critical'
            risk_score = 90
        elif suspicious_rate > 20:
            threat_level = 'high'
            risk_score = 70
        elif suspicious_rate > 10:
            threat_level = 'medium'
            risk_score = 50
        else:
            threat_level = 'low'
            risk_score = 20
        
        return {
            'threat_level': threat_level,
            'risk_score': risk_score,
            'suspicious_count': suspicious_count,
            'total_sessions': len(recent_sessions),
            'suspicious_rate': suspicious_rate
        }
    except:
        return {
            'threat_level': 'unknown',
            'risk_score': 0,
            'suspicious_count': 0,
            'total_sessions': 0
        }


# ==================== MODEL INITIALIZATION ====================

# Initialize models on import
try:
    iso_forest, scaler = load_or_train_model()
    print("✅ ML Models ready")
except Exception as e:
    print(f"⚠️  ML Model initialization delayed: {e}")
    iso_forest = None
    scaler = None
