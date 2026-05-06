"""
Machine Learning Routes
Provides ML-based anomaly detection and threat monitoring endpoints
"""

from flask import Blueprint, request, jsonify
from ml_model import (
    predict_anomaly, detect_attack_type, calculate_ml_threat_level,
    train_isolation_forest, load_or_train_model
)
from models import db, ChargingSession, User
from auth import role_required
from datetime import datetime, timedelta

ml_bp = Blueprint('ml', __name__, url_prefix='/ml')

# ==================== ANOMALY DETECTION ====================

@ml_bp.route('/predict', methods=['POST'])
@role_required(['admin', 'operator'])
def predict_anomaly_endpoint():
    """Predict anomaly for session data"""
    data = request.json or {}
    
    try:
        result = predict_anomaly(data)
        return jsonify({
            'status': 'success',
            'prediction': result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@ml_bp.route('/classify-attack', methods=['POST'])
@role_required(['admin', 'operator'])
def classify_attack_endpoint():
    """Classify attack type"""
    data = request.json or {}
    
    try:
        anomaly_result = predict_anomaly(data)
        attack_classification = detect_attack_type(
            data,
            anomaly_result['anomaly_score']
        )
        
        return jsonify({
            'status': 'success',
            'classification': attack_classification,
            'anomaly': anomaly_result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== THREAT LEVEL ====================

@ml_bp.route('/threat-level', methods=['GET'])
@role_required(['admin', 'operator'])
def get_threat_level():
    """Get current ML-based threat level"""
    try:
        period = request.args.get('period', 10, type=int)
        threat_data = calculate_ml_threat_level(period)
        
        return jsonify({
            'status': 'success',
            'threat_data': threat_data
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== SUSPICIOUS SESSIONS ====================

@ml_bp.route('/suspicious-sessions', methods=['GET'])
@role_required(['admin', 'operator'])
def get_suspicious_sessions():
    """Get list of suspicious sessions"""
    try:
        limit = request.args.get('limit', 20, type=int)
        
        suspicious = ChargingSession.query.filter_by(
            is_suspicious=True
        ).order_by(
            ChargingSession.start_time.desc()
        ).limit(limit).all()
        
        sessions_data = []
        for session in suspicious:
            sessions_data.append({
                'id': session.id,
                'session_id': session.session_id,
                'vehicle_id': session.vehicle.vehicle_id if session.vehicle else 'N/A',
                'driver': session.vehicle.driver_name if session.vehicle else 'N/A',
                'anomaly_score': session.anomaly_score,
                'start_time': session.start_time.isoformat(),
                'status': session.status
            })
        
        return jsonify({
            'status': 'success',
            'count': len(sessions_data),
            'sessions': sessions_data
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== MODEL TRAINING ====================

@ml_bp.route('/train-model', methods=['POST'])
@role_required(['admin'])
def train_model_endpoint():
    """Retrain ML model (admin only)"""
    try:
        n_samples = request.json.get('n_samples', 1000) if request.json else 1000
        
        iso_forest, scaler = train_isolation_forest(n_samples)
        
        return jsonify({
            'status': 'success',
            'message': f'Model trained with {n_samples} samples',
            'model_type': 'IsolationForest'
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== MODEL INFO ====================

@ml_bp.route('/model-info', methods=['GET'])
@role_required(['admin', 'operator'])
def get_model_info():
    """Get ML model information"""
    try:
        iso_forest, scaler = load_or_train_model()
        
        info = {
            'model_type': 'IsolationForest',
            'n_estimators': iso_forest.n_estimators if iso_forest else 'Unknown',
            'contamination': iso_forest.contamination if iso_forest else 'Unknown',
            'scaler': 'StandardScaler',
            'features': 10,
            'feature_names': [
                'energy_value', 'request_interval', 'battery_level',
                'charging_duration', 'request_frequency', 'payload_size',
                'repeated_payloads', 'energy_spike', 'request_deviation',
                'timestamp_gap'
            ],
            'status': 'Ready' if iso_forest else 'Not Trained'
        }
        
        return jsonify({
            'status': 'success',
            'model_info': info
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== ANOMALY STATISTICS ====================

@ml_bp.route('/anomaly-stats', methods=['GET'])
@role_required(['admin', 'operator'])
def get_anomaly_stats():
    """Get anomaly detection statistics"""
    try:
        period_hours = request.args.get('hours', 24, type=int)
        cutoff_time = datetime.utcnow() - timedelta(hours=period_hours)
        
        total_sessions = ChargingSession.query.filter(
            ChargingSession.start_time >= cutoff_time
        ).count()
        
        suspicious_sessions = ChargingSession.query.filter(
            ChargingSession.start_time >= cutoff_time,
            ChargingSession.is_suspicious == True
        ).count()
        
        avg_anomaly_score = db.session.query(
            db.func.avg(ChargingSession.anomaly_score)
        ).filter(
            ChargingSession.start_time >= cutoff_time
        ).scalar() or 0
        
        high_risk = ChargingSession.query.filter(
            ChargingSession.start_time >= cutoff_time,
            ChargingSession.anomaly_score > 0.7
        ).count()
        
        stats = {
            'period_hours': period_hours,
            'total_sessions': total_sessions,
            'suspicious_sessions': suspicious_sessions,
            'suspicious_rate': (suspicious_sessions / total_sessions * 100) if total_sessions > 0 else 0,
            'avg_anomaly_score': float(avg_anomaly_score),
            'high_risk_sessions': high_risk,
            'detection_accuracy': 'N/A'  # Would be calculated from labeled data
        }
        
        return jsonify({
            'status': 'success',
            'stats': stats
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== FEATURE EXTRACTION TEST ====================

@ml_bp.route('/extract-features', methods=['POST'])
@role_required(['admin', 'operator'])
def extract_features():
    """Test feature extraction from session data"""
    from ml_model import extract_features_from_session
    
    try:
        data = request.json or {}
        features = extract_features_from_session(data)
        
        return jsonify({
            'status': 'success',
            'features': features
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
