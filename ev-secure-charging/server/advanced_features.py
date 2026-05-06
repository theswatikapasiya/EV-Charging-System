"""
Phases 7-10: Advanced Features
- Phase 7: Predictive Charging (ETA & smart charging)
- Phase 8: QR Payment System
- Phase 9: Cloud Architecture Simulation
- Phase 10: Enhanced Cybersecurity Monitoring
"""

import hashlib
import base64
from datetime import datetime, timedelta
from models import db, ChargingSession, Payment, AttackLog, User, CryptoSecureLog
import qrcode
import io

# ==================== PHASE 7: PREDICTIVE CHARGING ====================

def calculate_charging_prediction(session_id):
    """Calculate ETA and charging predictions for active session"""
    session = ChargingSession.query.filter_by(session_id=session_id).first()
    
    if not session or session.status != 'active':
        return None
    
    battery_needed = 100 - session.initial_battery
    time_needed_hours = battery_needed / (session.charging_rate / session.vehicle.battery_capacity * 100)
    estimated_completion = session.start_time + timedelta(hours=time_needed_hours)
    
    cost_estimate = battery_needed * 5.0  # ₹5 per unit charged
    
    return {
        'session_id': session_id,
        'initial_battery': session.initial_battery,
        'current_battery': session.initial_battery + (session.energy_added or 0),
        'battery_needed': battery_needed,
        'charging_rate': session.charging_rate,
        'time_needed_minutes': round(time_needed_hours * 60, 1),
        'estimated_completion': estimated_completion.isoformat(),
        'estimated_cost': round(cost_estimate, 2),
        'charging_efficiency': '95%'
    }


def smart_charging_recommendation(session_id):
    """Provide smart charging insights"""
    session = ChargingSession.query.filter_by(session_id=session_id).first()
    
    if not session:
        return None
    
    recommendations = []
    
    battery_level = session.initial_battery + (session.energy_added or 0)
    
    if battery_level > 80:
        recommendations.append({
            'priority': 'low',
            'message': 'Battery level sufficient',
            'action': 'Consider terminating charging to save costs'
        })
    elif battery_level < 20:
        recommendations.append({
            'priority': 'high',
            'message': 'Low battery detected',
            'action': 'Increase charging rate for faster completion'
        })
    
    # Peak hours check
    current_hour = datetime.utcnow().hour
    if 9 <= current_hour <= 17:
        recommendations.append({
            'priority': 'medium',
            'message': 'Peak charging hours',
            'action': 'Consider optimized charging during off-peak hours (18-22)'
        })
    
    return recommendations


# ==================== PHASE 8: QR PAYMENT SYSTEM ====================

def generate_payment_qr(session_id, amount, currency='INR'):
    """Generate QR code for payment"""
    payment_data = {
        'session_id': session_id,
        'amount': amount,
        'currency': currency,
        'timestamp': datetime.utcnow().isoformat(),
        'platform': 'EV-Charging-System'
    }
    
    qr_text = f"EV_PAY:{session_id}:{amount}:{currency}:{datetime.utcnow().isoformat()}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(qr_text)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="blue", back_color="white")
    
    # Convert to base64
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return f"data:image/png;base64,{img_str}"


def process_qr_payment(session_id, transaction_id):
    """Process QR payment confirmation"""
    session = ChargingSession.query.filter_by(session_id=session_id).first()
    
    if not session:
        return {'status': 'error', 'message': 'Session not found'}
    
    payment = Payment(
        user_id=session.user_id,
        session_id=session.id,
        transaction_id=transaction_id,
        amount=session.cost,
        currency='INR',
        payment_method='qr',
        status='completed',
        completed_at=datetime.utcnow(),
        qr_code=generate_payment_qr(session_id, session.cost)
    )
    
    payment.invoice_number = f"INV-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    db.session.add(payment)
    db.session.commit()
    
    return {
        'status': 'success',
        'transaction_id': transaction_id,
        'amount': session.cost,
        'invoice_number': payment.invoice_number
    }


# ==================== PHASE 9: CLOUD ARCHITECTURE SIMULATION ====================

def get_cloud_architecture_status():
    """Simulate cloud architecture status"""
    active_sessions = ChargingSession.query.filter_by(status='active').count()
    completed_sessions = ChargingSession.query.filter_by(status='completed').count()
    
    return {
        'architecture': 'EV Vehicle → Charging Station → Edge Layer → Cloud Server → Admin Dashboard',
        'layers': [
            {
                'layer': 'EV Vehicle',
                'status': 'active',
                'connections': active_sessions,
                'data_points': 'Battery, Location, Speed'
            },
            {
                'layer': 'Charging Station',
                'status': 'operational',
                'active_stations': 5,
                'charging_slots': active_sessions
            },
            {
                'layer': 'Edge Layer (Local Processing)',
                'status': 'active',
                'processors': 3,
                'latency_ms': 5
            },
            {
                'layer': 'Cloud Server',
                'status': 'online',
                'storage_gb': 500,
                'uptime_percent': 99.9
            },
            {
                'layer': 'Admin Dashboard',
                'status': 'accessible',
                'connected_users': 1,
                'last_sync': datetime.utcnow().isoformat()
            }
        ],
        'data_sync': {
            'local_to_edge': 'Real-time',
            'edge_to_cloud': 'Every 30 seconds',
            'cloud_to_dashboard': 'Live WebSocket'
        },
        'redundancy': {
            'backup_systems': 2,
            'failover_time_seconds': 5,
            'data_replication': 'Triple'
        }
    }


def get_cloud_analytics():
    """Get cloud-based analytics summary"""
    return {
        'cloud_sync_status': 'Synchronized',
        'last_sync_time': datetime.utcnow().isoformat(),
        'distributed_load': {
            'local_processing': 40,
            'edge_processing': 35,
            'cloud_processing': 25
        },
        'data_volume': {
            'today_gb': 2.5,
            'this_month_gb': 45.3,
            'total_gb': 150
        }
    }


# ==================== PHASE 10: ENHANCED CYBERSECURITY ====================

def get_threat_heatmap():
    """Generate system threat heatmap"""
    attacks_last_24h = AttackLog.query.filter(
        AttackLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
    ).all()
    
    threat_map = {}
    for attack in attacks_last_24h:
        key = f"{attack.source_ip}:{attack.target_system}"
        threat_map[key] = threat_map.get(key, 0) + 1
    
    threat_entries = []
    for key, count in sorted(threat_map.items(), key=lambda x: x[1], reverse=True)[:10]:
        threat_entries.append({
            'source': key.split(':')[0],
            'target': key.split(':')[1] if ':' in key else 'Unknown',
            'attempts': count,
            'threat_level': 'critical' if count > 10 else 'high' if count > 5 else 'medium'
        })
    
    return threat_entries


def get_intrusion_alerts():
    """Get recent intrusion alerts"""
    critical_attacks = AttackLog.query.filter(
        AttackLog.severity.in_(['high', 'critical']),
        AttackLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
    ).all()
    
    alerts = []
    for attack in critical_attacks:
        alerts.append({
            'alert_id': attack.id,
            'timestamp': attack.timestamp.isoformat(),
            'attack_type': attack.attack_type,
            'severity': attack.severity,
            'source_ip': attack.source_ip,
            'target': attack.target_system,
            'status': 'Blocked' if attack.blocked else 'Detected',
            'mitigation': attack.mitigation_method
        })
    
    return alerts


def enable_rate_limiting(ip_address, max_requests=100, time_window_seconds=60):
    """Track rate limiting for IP"""
    rate_key = f"rate_limit:{ip_address}"
    # This would use Redis in production
    return {
        'ip': ip_address,
        'max_requests': max_requests,
        'time_window': time_window_seconds,
        'status': 'enabled'
    }


def track_suspicious_activity(ip_address, activity_type, details):
    """Track suspicious activities for audit"""
    log = CryptoSecureLog(
        event_type='suspicious_activity',
        description=f'{activity_type}: {details}',
        ip_address=ip_address
    )
    log.compute_hash()
    db.session.add(log)
    db.session.commit()
    
    return {
        'logged': True,
        'activity_id': log.id,
        'ip': ip_address
    }


def get_security_dashboard():
    """Get comprehensive security dashboard"""
    return {
        'threat_level': 'Medium',
        'risk_score': 45,
        'threats_24h': AttackLog.query.filter(
            AttackLog.timestamp >= datetime.utcnow() - timedelta(hours=24)
        ).count(),
        'blocked_attacks': AttackLog.query.filter_by(blocked=True).count(),
        'active_monitoring': True,
        'intrusion_alerts': len(get_intrusion_alerts()),
        'threat_heatmap': get_threat_heatmap()
    }
