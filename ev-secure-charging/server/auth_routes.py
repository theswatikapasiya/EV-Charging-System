"""
Authentication routes
Handles registration, login, logout, and user management
"""

from flask import Blueprint, request, jsonify, session, render_template
from models import db, User, CryptoSecureLog
from auth import (
    create_access_token, verify_token, create_session, destroy_session,
    token_required, role_required, get_token_from_request
)
from datetime import datetime
from functools import wraps

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# ==================== REGISTRATION ====================

@auth_bp.route('/register', methods=['POST'])
def register():
    """Register new user"""
    data = request.json
    
    # Validate input
    if not data or not data.get('username') or not data.get('password') or not data.get('email'):
        return jsonify({'message': 'Missing required fields', 'status': 'error'}), 400
    
    # Check if user exists
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists', 'status': 'error'}), 409
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already registered', 'status': 'error'}), 409
    
    # Create new user (default role: 'user')
    try:
        user = User(
            username=data['username'],
            email=data['email'],
            role=data.get('role', 'user'),
            is_active=True,
            ip_address=request.remote_addr
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Log to crypto secure logs
        secure_log = CryptoSecureLog(
            event_type='user_registration',
            description=f"New user registered: {user.username} ({user.role})",
            user_id=user.id,
            ip_address=request.remote_addr
        )
        secure_log.compute_hash()
        db.session.add(secure_log)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'status': 'success',
            'user': user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Registration failed: {str(e)}', 'status': 'error'}), 500


# ==================== LOGIN ====================

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login - returns JWT token"""
    data = request.json
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Missing username or password', 'status': 'error'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'message': 'Invalid credentials', 'status': 'error'}), 401
    
    if not user.is_active:
        return jsonify({'message': 'User account is inactive', 'status': 'error'}), 403
    
    try:
        # Update last login
        user.last_login = datetime.utcnow()
        user.ip_address = request.remote_addr
        
        # Create JWT token
        access_token = create_access_token(user.id, user.role)
        
        # Create Flask session
        create_session(user.id)
        
        # Log login event
        secure_log = CryptoSecureLog(
            event_type='user_login',
            description=f"User {user.username} ({user.role}) logged in",
            user_id=user.id,
            ip_address=request.remote_addr
        )
        secure_log.compute_hash()
        db.session.add(secure_log)
        db.session.commit()
        
        response = {
            'message': 'Login successful',
            'status': 'success',
            'access_token': access_token,
            'user': user.to_dict()
        }
        
        return jsonify(response), 200
        
    except Exception as e:
        return jsonify({'message': f'Login failed: {str(e)}', 'status': 'error'}), 500


# ==================== LOGOUT ====================

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """User logout"""
    try:
        user_id = None
        
        # Get user_id from token or session
        token = get_token_from_request()
        if token:
            payload = verify_token(token)
            if payload:
                user_id = payload['user_id']
        
        if 'user_id' in session:
            user_id = session['user_id']
        
        # Log logout event
        if user_id:
            user = User.query.get(user_id)
            if user:
                secure_log = CryptoSecureLog(
                    event_type='user_logout',
                    description=f"User {user.username} logged out",
                    user_id=user_id,
                    ip_address=request.remote_addr
                )
                secure_log.compute_hash()
                db.session.add(secure_log)
                db.session.commit()
        
        # Clear session
        destroy_session()
        
        return jsonify({'message': 'Logout successful', 'status': 'success'}), 200
        
    except Exception as e:
        return jsonify({'message': f'Logout failed: {str(e)}', 'status': 'error'}), 500


# ==================== GET CURRENT USER ====================

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Get current logged-in user info"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'message': 'Not authenticated', 'status': 'error'}), 401
    
    payload = verify_token(token)
    if not payload:
        return jsonify({'message': 'Token invalid or expired', 'status': 'error'}), 401
    
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'message': 'User not found', 'status': 'error'}), 404
    
    return jsonify({
        'status': 'success',
        'user': user.to_dict()
    }), 200


# ==================== CHANGE PASSWORD ====================

@auth_bp.route('/change-password', methods=['POST'])
def change_password():
    """Change user password"""
    token = get_token_from_request()
    
    if not token:
        return jsonify({'message': 'Not authenticated', 'status': 'error'}), 401
    
    payload = verify_token(token)
    if not payload:
        return jsonify({'message': 'Token invalid or expired', 'status': 'error'}), 401
    
    data = request.json
    if not data or not data.get('old_password') or not data.get('new_password'):
        return jsonify({'message': 'Missing required fields', 'status': 'error'}), 400
    
    user = User.query.get(payload['user_id'])
    if not user:
        return jsonify({'message': 'User not found', 'status': 'error'}), 404
    
    if not user.check_password(data['old_password']):
        return jsonify({'message': 'Old password is incorrect', 'status': 'error'}), 401
    
    try:
        user.set_password(data['new_password'])
        db.session.commit()
        
        # Log password change
        secure_log = CryptoSecureLog(
            event_type='password_change',
            description=f"User {user.username} changed password",
            user_id=user.id,
            ip_address=request.remote_addr
        )
        secure_log.compute_hash()
        db.session.add(secure_log)
        db.session.commit()
        
        return jsonify({'message': 'Password changed successfully', 'status': 'success'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': f'Password change failed: {str(e)}', 'status': 'error'}), 500


# ==================== USER MANAGEMENT (ADMIN ONLY) ====================

@auth_bp.route('/users', methods=['GET'])
@role_required(['admin'])
def get_all_users():
    """Get all users (admin only)"""
    try:
        users = User.query.all()
        return jsonify({
            'status': 'success',
            'users': [user.to_dict() for user in users]
        }), 200
    except Exception as e:
        return jsonify({'message': str(e), 'status': 'error'}), 500


@auth_bp.route('/users/<int:user_id>', methods=['GET'])
@role_required(['admin'])
def get_user(user_id):
    """Get specific user (admin only)"""
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found', 'status': 'error'}), 404
    
    return jsonify({
        'status': 'success',
        'user': user.to_dict()
    }), 200


@auth_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@role_required(['admin'])
def update_user_role(user_id):
    """Update user role (admin only)"""
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found', 'status': 'error'}), 404
    
    data = request.json
    if not data or 'role' not in data:
        return jsonify({'message': 'Missing role field', 'status': 'error'}), 400
    
    valid_roles = ['admin', 'operator', 'user']
    if data['role'] not in valid_roles:
        return jsonify({'message': f'Invalid role. Must be one of {valid_roles}', 'status': 'error'}), 400
    
    try:
        old_role = user.role
        user.role = data['role']
        db.session.commit()
        
        # Log role change
        admin_user = User.query.get(request.user_id)
        secure_log = CryptoSecureLog(
            event_type='user_role_change',
            description=f"Admin {admin_user.username} changed {user.username} role from {old_role} to {data['role']}",
            user_id=admin_user.id,
            ip_address=request.remote_addr
        )
        secure_log.compute_hash()
        db.session.add(secure_log)
        db.session.commit()
        
        return jsonify({
            'message': 'User role updated successfully',
            'status': 'success',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e), 'status': 'error'}), 500


@auth_bp.route('/users/<int:user_id>/toggle-active', methods=['PUT'])
@role_required(['admin'])
def toggle_user_active(user_id):
    """Toggle user active status (admin only)"""
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'message': 'User not found', 'status': 'error'}), 404
    
    try:
        user.is_active = not user.is_active
        db.session.commit()
        
        # Log status change
        admin_user = User.query.get(request.user_id)
        secure_log = CryptoSecureLog(
            event_type='user_status_change',
            description=f"Admin {admin_user.username} {'activated' if user.is_active else 'deactivated'} user {user.username}",
            user_id=admin_user.id,
            ip_address=request.remote_addr
        )
        secure_log.compute_hash()
        db.session.add(secure_log)
        db.session.commit()
        
        return jsonify({
            'message': f"User {'activated' if user.is_active else 'deactivated'} successfully",
            'status': 'success',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e), 'status': 'error'}), 500
