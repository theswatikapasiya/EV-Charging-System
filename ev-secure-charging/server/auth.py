"""
Authentication and Authorization utilities
Handles JWT tokens, password hashing, and role-based access control
"""

from flask import request, jsonify
from functools import wraps
import jwt
from datetime import datetime, timedelta
from models import User, db
import os

SECRET_KEY = os.environ.get('SECRET_KEY', 'ev-charging-secret-2026')
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# ==================== JWT TOKEN FUNCTIONS ====================

def create_access_token(user_id, role, expires_delta=None):
    """Create JWT access token"""
    if expires_delta is None:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.utcnow() + expires_delta
    payload = {
        'user_id': user_id,
        'role': role,
        'exp': expire
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return token


def verify_token(token):
    """Verify JWT token and return user_id"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_token_from_request():
    """Extract token from request headers or cookies"""
    # Check Authorization header
    if 'Authorization' in request.headers:
        auth_header = request.headers['Authorization']
        if auth_header.startswith('Bearer '):
            return auth_header[7:]
    
    # Check cookies
    if 'access_token' in request.cookies:
        return request.cookies['access_token']
    
    return None


# ==================== DECORATORS ====================

def token_required(f):
    """Decorator to require valid JWT token"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        
        if not token:
            return jsonify({'message': 'Token is missing', 'status': 'unauthorized'}), 401
        
        payload = verify_token(token)
        if not payload:
            return jsonify({'message': 'Token is invalid or expired', 'status': 'unauthorized'}), 401
        
        request.user_id = payload['user_id']
        request.user_role = payload['role']
        return f(*args, **kwargs)
    
    return decorated


def role_required(allowed_roles):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = get_token_from_request()
            
            if not token:
                return jsonify({'message': 'Token is missing', 'status': 'unauthorized'}), 401
            
            payload = verify_token(token)
            if not payload:
                return jsonify({'message': 'Token is invalid or expired', 'status': 'unauthorized'}), 401
            
            if payload['role'] not in allowed_roles:
                return jsonify({'message': 'Insufficient permissions', 'status': 'forbidden'}), 403
            
            request.user_id = payload['user_id']
            request.user_role = payload['role']
            return f(*args, **kwargs)
        
        return decorated
    return decorator


def session_required(f):
    """Decorator to require Flask session (can be used alongside token_required)"""
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import session
        
        if 'user_id' not in session:
            return jsonify({'message': 'Session expired', 'status': 'unauthorized'}), 401
        
        request.user_id = session['user_id']
        request.user_role = session.get('role', 'user')
        return f(*args, **kwargs)
    
    return decorated


# ==================== PERMISSION CHECKS ====================

ROLE_PERMISSIONS = {
    'admin': ['dashboard', 'analytics', 'attack_logs', 'user_management', 'system_settings', 'charts', 'payments'],
    'operator': ['charging_monitor', 'vehicle_control', 'logs_access', 'attack_response', 'session_management'],
    'user': ['submit_vehicle', 'view_session', 'pay_bill', 'view_payment_history']
}

def has_permission(user_role, action):
    """Check if user role has permission for action"""
    return action in ROLE_PERMISSIONS.get(user_role, [])


# ==================== SESSION HELPERS ====================

def create_session(user_id):
    """Create Flask session"""
    from flask import session
    user = User.query.get(user_id)
    
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        session['role'] = user.role
        session['email'] = user.email
        session['created_at'] = datetime.utcnow().isoformat()
        return True
    
    return False


def destroy_session():
    """Destroy Flask session"""
    from flask import session
    session.clear()
