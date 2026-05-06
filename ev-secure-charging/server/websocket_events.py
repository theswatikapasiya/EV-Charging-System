"""
WebSocket events for real-time communication
Replaces polling with instant push updates for:
- Vehicle charging status
- Attack logs
- Billing updates
- Session events
- Analytics updates
"""

from flask_socketio import emit, join_room, leave_room, SocketIO
from models import db, ChargingSession, AttackLog, Vehicle, User
from datetime import datetime
import json

socketio = SocketIO(cors_allowed_origins="*")

# Store connected clients
CONNECTED_CLIENTS = {}
ROOM_SUBSCRIPTIONS = {}

# ==================== CONNECTION HANDLERS ====================

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    from flask import request, session
    
    client_id = request.sid
    CONNECTED_CLIENTS[client_id] = {
        'connected_at': datetime.utcnow(),
        'user_id': session.get('user_id'),
        'rooms': []
    }
    
    print(f"🔌 Client connected: {client_id}")
    emit('connection_response', {'status': 'connected', 'client_id': client_id})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    from flask import request
    
    client_id = request.sid
    if client_id in CONNECTED_CLIENTS:
        del CONNECTED_CLIENTS[client_id]
    
    print(f"❌ Client disconnected: {client_id}")


# ==================== ROOM MANAGEMENT ====================

@socketio.on('subscribe')
def handle_subscribe(data):
    """Subscribe to specific room/channel"""
    from flask import request
    
    client_id = request.sid
    channel = data.get('channel')  # e.g., 'charging_updates', 'attacks', 'analytics'
    
    if channel:
        join_room(channel)
        
        if client_id in CONNECTED_CLIENTS:
            CONNECTED_CLIENTS[client_id]['rooms'].append(channel)
        
        print(f"👥 Client {client_id} subscribed to {channel}")
        emit('subscribe_response', {'status': 'subscribed', 'channel': channel})


@socketio.on('unsubscribe')
def handle_unsubscribe(data):
    """Unsubscribe from specific room/channel"""
    from flask import request
    
    client_id = request.sid
    channel = data.get('channel')
    
    if channel:
        leave_room(channel)
        
        if client_id in CONNECTED_CLIENTS and channel in CONNECTED_CLIENTS[client_id]['rooms']:
            CONNECTED_CLIENTS[client_id]['rooms'].remove(channel)
        
        emit('unsubscribe_response', {'status': 'unsubscribed', 'channel': channel})


# ==================== CHARGING UPDATES ====================

def emit_charging_update(session_data):
    """Emit real-time charging progress update"""
    socketio.emit('charging_update', {
        'status': 'update',
        'session': session_data,
        'timestamp': datetime.utcnow().isoformat()
    }, room='charging_updates')


def emit_session_started(session_id, vehicle_data):
    """Emit event when new charging session starts"""
    socketio.emit('session_started', {
        'status': 'success',
        'session_id': session_id,
        'vehicle': vehicle_data,
        'timestamp': datetime.utcnow().isoformat()
    }, room='charging_updates')


def emit_session_completed(session_id, completion_data):
    """Emit event when charging session completes"""
    socketio.emit('session_completed', {
        'status': 'completed',
        'session_id': session_id,
        'data': completion_data,
        'timestamp': datetime.utcnow().isoformat()
    }, room='charging_updates')


def emit_vehicle_entered_queue(vehicle_data):
    """Emit event when vehicle enters queue"""
    socketio.emit('vehicle_queued', {
        'status': 'queued',
        'vehicle': vehicle_data,
        'timestamp': datetime.utcnow().isoformat()
    }, room='charging_updates')


# ==================== ATTACK UPDATES ====================

def emit_attack_detected(attack_data):
    """Emit real-time attack detection alert"""
    socketio.emit('attack_detected', {
        'status': 'alert',
        'attack': attack_data,
        'timestamp': datetime.utcnow().isoformat()
    }, room='attacks')


def emit_attack_blocked(attack_data):
    """Emit attack blocked notification"""
    socketio.emit('attack_blocked', {
        'status': 'blocked',
        'attack': attack_data,
        'timestamp': datetime.utcnow().isoformat()
    }, room='attacks')


def emit_threat_level_update(threat_level, risk_score):
    """Emit system threat level update"""
    socketio.emit('threat_level', {
        'status': 'update',
        'threat_level': threat_level,  # low, medium, high, critical
        'risk_score': risk_score,
        'timestamp': datetime.utcnow().isoformat()
    }, room='attacks')


# ==================== ANALYTICS UPDATES ====================

def emit_analytics_update(analytics_data):
    """Emit real-time analytics update"""
    socketio.emit('analytics_update', {
        'status': 'update',
        'data': analytics_data,
        'timestamp': datetime.utcnow().isoformat()
    }, room='analytics')


def emit_dashboard_stats(stats):
    """Emit dashboard statistics update"""
    socketio.emit('dashboard_stats', {
        'status': 'update',
        'stats': stats,
        'timestamp': datetime.utcnow().isoformat()
    }, room='analytics')


# ==================== BILLING & PAYMENT UPDATES ====================

def emit_billing_update(session_id, billing_data):
    """Emit real-time billing update"""
    socketio.emit('billing_update', {
        'status': 'update',
        'session_id': session_id,
        'billing': billing_data,
        'timestamp': datetime.utcnow().isoformat()
    }, room='billing')


def emit_payment_generated(session_id, qr_code, amount):
    """Emit payment QR code generation"""
    socketio.emit('payment_qr_ready', {
        'status': 'ready',
        'session_id': session_id,
        'qr_code': qr_code,
        'amount': amount,
        'timestamp': datetime.utcnow().isoformat()
    }, room='billing')


def emit_payment_confirmed(session_id, transaction_id):
    """Emit payment confirmation"""
    socketio.emit('payment_confirmed', {
        'status': 'confirmed',
        'session_id': session_id,
        'transaction_id': transaction_id,
        'timestamp': datetime.utcnow().isoformat()
    }, room='billing')


# ==================== SYSTEM EVENTS ====================

def emit_system_event(event_type, event_data):
    """Emit generic system event"""
    socketio.emit('system_event', {
        'event_type': event_type,
        'data': event_data,
        'timestamp': datetime.utcnow().isoformat()
    }, room='system')


def emit_status_snapshot():
    """Emit complete system status snapshot"""
    try:
        total_sessions = ChargingSession.query.count()
        active_sessions = ChargingSession.query.filter_by(status='active').count()
        completed_sessions = ChargingSession.query.filter_by(status='completed').count()
        total_attacks = AttackLog.query.count()
        blocked_attacks = AttackLog.query.filter_by(blocked=True).count()
        
        socketio.emit('status_snapshot', {
            'status': 'snapshot',
            'total_sessions': total_sessions,
            'active_sessions': active_sessions,
            'completed_sessions': completed_sessions,
            'total_attacks': total_attacks,
            'blocked_attacks': blocked_attacks,
            'connected_clients': len(CONNECTED_CLIENTS),
            'timestamp': datetime.utcnow().isoformat()
        }, room='system')
    except:
        pass


# ==================== BROADCAST HELPERS ====================

def broadcast_to_admins(event_name, data):
    """Broadcast event only to admin users"""
    admin_users = User.query.filter_by(role='admin').all()
    # Would need to track admin client IDs to implement properly
    socketio.emit(event_name, data, room='admins')


def broadcast_to_operators(event_name, data):
    """Broadcast event to all operators"""
    socketio.emit(event_name, data, room='operators')


def notify_all_clients(event_name, data):
    """Notify all connected clients"""
    socketio.emit(event_name, data, broadcast=True)


# ==================== ERROR HANDLING ====================

@socketio.on_error_default
def default_error_handler(e):
    """Handle WebSocket errors"""
    print(f"⚠️  WebSocket Error: {str(e)}")
    emit('error', {'message': str(e)})
