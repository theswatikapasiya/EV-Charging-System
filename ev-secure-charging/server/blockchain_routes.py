"""
Blockchain routes
Endpoints for blockchain-secured log verification and visualization
"""

from flask import Blueprint, request, jsonify
from blockchain_logger import (
    verify_blockchain_chain, verify_attack_logs_chain,
    get_blockchain_stats, export_blockchain_chain,
    get_blockchain_visualization, create_blockchain_log
)
from auth import role_required

blockchain_bp = Blueprint('blockchain', __name__, url_prefix='/blockchain')

# ==================== VERIFICATION ====================

@blockchain_bp.route('/verify-chain', methods=['GET'])
@role_required(['admin', 'operator'])
def verify_chain():
    """Verify blockchain chain integrity"""
    try:
        start_id = request.args.get('start_id', None, type=int)
        result = verify_blockchain_chain(start_id)
        
        return jsonify({
            'status': 'success',
            'verification': result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


@blockchain_bp.route('/verify-attack-logs', methods=['GET'])
@role_required(['admin', 'operator'])
def verify_attack_logs():
    """Verify attack logs blockchain chain"""
    try:
        result = verify_attack_logs_chain()
        
        return jsonify({
            'status': 'success',
            'verification': result
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== STATISTICS ====================

@blockchain_bp.route('/stats', methods=['GET'])
@role_required(['admin', 'operator'])
def get_stats():
    """Get blockchain statistics"""
    try:
        stats = get_blockchain_stats()
        
        return jsonify({
            'status': 'success',
            'stats': stats
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== VISUALIZATION ====================

@blockchain_bp.route('/chain-visualization', methods=['GET'])
@role_required(['admin', 'operator'])
def chain_visualization():
    """Get blockchain chain for visualization"""
    try:
        limit = request.args.get('limit', 50, type=int)
        data = get_blockchain_visualization(limit)
        
        return jsonify({
            'status': 'success',
            'visualization': data
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== EXPORT ====================

@blockchain_bp.route('/export', methods=['GET'])
@role_required(['admin', 'operator'])
def export_chain():
    """Export blockchain chain"""
    try:
        format_type = request.args.get('format', 'json', type=str)  # json or csv
        start_id = request.args.get('start_id', None, type=int)
        
        if format_type not in ['json', 'csv']:
            return jsonify({
                'status': 'error',
                'message': 'Invalid format. Must be json or csv'
            }), 400
        
        data = export_blockchain_chain(format_type, start_id)
        
        if format_type == 'csv':
            return data, 200, {'Content-Type': 'text/csv'}
        else:
            return jsonify({
                'status': 'success',
                'format': 'json',
                'chain': data
            }), 200
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== CREATE LOG ====================

@blockchain_bp.route('/create-log', methods=['POST'])
@role_required(['admin', 'operator'])
def create_log():
    """Create new blockchain-secured log entry"""
    try:
        from flask import session
        data = request.json or {}
        
        user_id = session.get('user_id')
        ip_address = request.remote_addr
        
        log_entry = create_blockchain_log(
            event_type=data.get('event_type', 'manual_entry'),
            description=data.get('description', 'Manual log entry'),
            user_id=user_id,
            ip_address=ip_address
        )
        
        if log_entry:
            return jsonify({
                'status': 'success',
                'log': log_entry
            }), 201
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to create log entry'
            }), 500
    
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== DASHBOARD ====================

@blockchain_bp.route('/dashboard', methods=['GET'])
@role_required(['admin'])
def blockchain_dashboard():
    """Get complete blockchain dashboard data"""
    try:
        stats = get_blockchain_stats()
        visualization = get_blockchain_visualization(20)
        verification = verify_blockchain_chain()
        
        dashboard_data = {
            'stats': stats,
            'recent_chain': visualization['chain'],
            'chain_verification': {
                'is_valid': verification['is_valid'],
                'verified_logs': verification['verified_logs'],
                'total_logs': verification['total_logs'],
                'tampered_entries': len(verification['tampered_logs'])
            },
            'timestamp': __import__('datetime').datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'status': 'success',
            'dashboard': dashboard_data
        }), 200
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500
