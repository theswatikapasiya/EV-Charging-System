"""
Routes for Advanced Features (Phases 7-10)
"""

from flask import Blueprint, request, jsonify
from advanced_features import (
    calculate_charging_prediction, smart_charging_recommendation,
    generate_payment_qr, process_qr_payment, get_cloud_architecture_status,
    get_cloud_analytics, get_threat_heatmap, get_intrusion_alerts,
    get_security_dashboard
)
from auth import role_required, token_required
from models import ChargingSession

advanced_bp = Blueprint('advanced', __name__, url_prefix='/advanced')

# ==================== PHASE 7: PREDICTIVE CHARGING ====================

@advanced_bp.route('/charging/prediction/<session_id>', methods=['GET'])
@token_required
def charging_prediction(session_id):
    """Get charging prediction for session"""
    try:
        prediction = calculate_charging_prediction(session_id)
        
        if prediction:
            return jsonify({
                'status': 'success',
                'prediction': prediction
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Session not found or not active'
            }), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@advanced_bp.route('/charging/recommendations/<session_id>', methods=['GET'])
@token_required
def charging_recommendations(session_id):
    """Get smart charging recommendations"""
    try:
        recommendations = smart_charging_recommendation(session_id)
        
        if recommendations is not None:
            return jsonify({
                'status': 'success',
                'recommendations': recommendations
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Session not found'
            }), 404
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== PHASE 8: QR PAYMENT ====================

@advanced_bp.route('/payment/generate-qr/<session_id>', methods=['GET'])
@token_required
def generate_qr(session_id):
    """Generate payment QR code"""
    try:
        session = ChargingSession.query.filter_by(session_id=session_id).first()
        
        if not session:
            return jsonify({'status': 'error', 'message': 'Session not found'}), 404
        
        qr_code = generate_payment_qr(session_id, session.cost)
        
        return jsonify({
            'status': 'success',
            'qr_code': qr_code,
            'amount': session.cost,
            'currency': 'INR',
            'session_id': session_id
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@advanced_bp.route('/payment/confirm-qr', methods=['POST'])
@token_required
def confirm_qr_payment():
    """Confirm QR payment"""
    try:
        data = request.json or {}
        session_id = data.get('session_id')
        transaction_id = data.get('transaction_id')
        
        if not session_id or not transaction_id:
            return jsonify({
                'status': 'error',
                'message': 'Missing session_id or transaction_id'
            }), 400
        
        result = process_qr_payment(session_id, transaction_id)
        
        if result['status'] == 'success':
            return jsonify(result), 201
        else:
            return jsonify(result), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== PHASE 9: CLOUD ARCHITECTURE ====================

@advanced_bp.route('/cloud/architecture', methods=['GET'])
@role_required(['admin', 'operator'])
def cloud_architecture():
    """Get cloud architecture status"""
    try:
        arch = get_cloud_architecture_status()
        
        return jsonify({
            'status': 'success',
            'architecture': arch
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@advanced_bp.route('/cloud/analytics', methods=['GET'])
@role_required(['admin', 'operator'])
def cloud_analytics():
    """Get cloud analytics"""
    try:
        analytics = get_cloud_analytics()
        
        return jsonify({
            'status': 'success',
            'analytics': analytics
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== PHASE 10: CYBERSECURITY ====================

@advanced_bp.route('/security/threat-heatmap', methods=['GET'])
@role_required(['admin'])
def threat_heatmap():
    """Get threat heatmap"""
    try:
        heatmap = get_threat_heatmap()
        
        return jsonify({
            'status': 'success',
            'heatmap': heatmap
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@advanced_bp.route('/security/intrusion-alerts', methods=['GET'])
@role_required(['admin', 'operator'])
def intrusion_alerts():
    """Get intrusion alerts"""
    try:
        alerts = get_intrusion_alerts()
        
        return jsonify({
            'status': 'success',
            'alerts': alerts,
            'count': len(alerts)
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@advanced_bp.route('/security/dashboard', methods=['GET'])
@role_required(['admin', 'operator'])
def security_dashboard():
    """Get security dashboard"""
    try:
        dashboard = get_security_dashboard()
        
        return jsonify({
            'status': 'success',
            'dashboard': dashboard
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
