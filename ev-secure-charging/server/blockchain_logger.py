"""
Blockchain-Style Secure Logging System
Creates tamper-proof, immutable logs using SHA256 hash chains
Each log entry is cryptographically linked to the previous one
"""

import hashlib
from datetime import datetime
from models import db, CryptoSecureLog, AttackLog

# ==================== BLOCKCHAIN LOG CREATION ====================

def create_blockchain_log(event_type, description, user_id=None, ip_address=None):
    """Create new blockchain-secured log entry"""
    try:
        # Get previous log
        prev_log = CryptoSecureLog.query.order_by(
            CryptoSecureLog.id.desc()
        ).first()
        
        # Create new log with chain
        log = CryptoSecureLog(
            event_type=event_type,
            description=description,
            user_id=user_id,
            ip_address=ip_address,
            previous_hash=prev_log.current_hash if prev_log else None
        )
        
        # Compute hash
        log.compute_hash()
        
        db.session.add(log)
        db.session.commit()
        
        return {
            'id': log.id,
            'timestamp': log.timestamp.isoformat(),
            'event_type': event_type,
            'current_hash': log.current_hash,
            'previous_hash': log.previous_hash,
            'chain_position': log.id
        }
    except Exception as e:
        db.session.rollback()
        print(f"Error creating blockchain log: {e}")
        return None


# ==================== BLOCKCHAIN VERIFICATION ====================

def verify_single_log(log):
    """Verify integrity of a single log entry"""
    if not log:
        return False
    
    expected_hash_input = f"{log.timestamp}{log.event_type}{log.description}{log.previous_hash or ''}"
    expected_hash = hashlib.sha256(expected_hash_input.encode()).hexdigest()
    
    is_valid = expected_hash == log.current_hash
    return is_valid


def verify_blockchain_chain(start_log_id=None):
    """Verify entire blockchain chain integrity"""
    try:
        if start_log_id:
            logs = CryptoSecureLog.query.filter(
                CryptoSecureLog.id >= start_log_id
            ).order_by(CryptoSecureLog.id.asc()).all()
        else:
            logs = CryptoSecureLog.query.order_by(CryptoSecureLog.id.asc()).all()
        
        if not logs:
            return {
                'is_valid': True,
                'message': 'No logs to verify',
                'total_logs': 0,
                'verified_logs': 0,
                'tampered_logs': []
            }
        
        verified_count = 0
        tampered_logs = []
        prev_hash = None
        
        for i, log in enumerate(logs):
            # Verify hash
            if not verify_single_log(log):
                tampered_logs.append({
                    'log_id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'reason': 'Hash mismatch'
                })
            else:
                verified_count += 1
            
            # Verify chain link
            if log.previous_hash != prev_hash and i > 0:
                tampered_logs.append({
                    'log_id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'reason': 'Chain link broken'
                })
            
            prev_hash = log.current_hash
        
        return {
            'is_valid': len(tampered_logs) == 0,
            'message': 'Blockchain integrity verified' if len(tampered_logs) == 0 else f'{len(tampered_logs)} tampered entries detected',
            'total_logs': len(logs),
            'verified_logs': verified_count,
            'tampered_logs': tampered_logs
        }
    
    except Exception as e:
        return {
            'is_valid': False,
            'message': f'Verification error: {str(e)}',
            'total_logs': 0,
            'verified_logs': 0,
            'tampered_logs': []
        }


def verify_attack_logs_chain():
    """Verify attack logs blockchain chain"""
    try:
        logs = AttackLog.query.order_by(AttackLog.id.asc()).all()
        
        verified_count = 0
        tampered_logs = []
        prev_hash = None
        
        for i, log in enumerate(logs):
            # Verify hash
            expected_hash = hashlib.sha256(
                f"{log.timestamp}{log.attack_type}{log.source_ip}{log.previous_hash or ''}".encode()
            ).hexdigest()
            
            if expected_hash != log.current_hash:
                tampered_logs.append({
                    'log_id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'reason': 'Hash mismatch'
                })
            else:
                verified_count += 1
            
            # Verify chain link
            if log.previous_hash != prev_hash and i > 0:
                tampered_logs.append({
                    'log_id': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'reason': 'Chain link broken'
                })
            
            prev_hash = log.current_hash
        
        return {
            'is_valid': len(tampered_logs) == 0,
            'total_logs': len(logs),
            'verified_logs': verified_count,
            'tampered_logs': tampered_logs
        }
    
    except Exception as e:
        return {
            'is_valid': False,
            'message': str(e),
            'total_logs': 0,
            'verified_logs': 0,
            'tampered_logs': []
        }


# ==================== BLOCKCHAIN STATISTICS ====================

def get_blockchain_stats():
    """Get blockchain statistics"""
    try:
        total_logs = CryptoSecureLog.query.count()
        attack_logs_count = AttackLog.query.count()
        
        # Get logs by event type
        event_type_breakdown = db.session.query(
            CryptoSecureLog.event_type,
            db.func.count(CryptoSecureLog.id).label('count')
        ).group_by(CryptoSecureLog.event_type).all()
        
        breakdown = {et: count for et, count in event_type_breakdown}
        
        # Verify chain
        verification = verify_blockchain_chain()
        
        return {
            'total_logs': total_logs,
            'attack_logs': attack_logs_count,
            'event_type_breakdown': breakdown,
            'chain_verified': verification['is_valid'],
            'verified_logs': verification['verified_logs'],
            'tampered_entries': len(verification['tampered_logs'])
        }
    
    except Exception as e:
        return {
            'total_logs': 0,
            'error': str(e)
        }


# ==================== EXPORT BLOCKCHAIN ====================

def export_blockchain_chain(format='json', start_log_id=None):
    """Export blockchain chain in various formats"""
    try:
        if start_log_id:
            logs = CryptoSecureLog.query.filter(
                CryptoSecureLog.id >= start_log_id
            ).order_by(CryptoSecureLog.id.asc()).all()
        else:
            logs = CryptoSecureLog.query.order_by(CryptoSecureLog.id.asc()).all()
        
        if format == 'json':
            chain_data = []
            for log in logs:
                chain_data.append({
                    'block_index': log.id,
                    'timestamp': log.timestamp.isoformat(),
                    'event_type': log.event_type,
                    'description': log.description,
                    'user_id': log.user_id,
                    'ip_address': log.ip_address,
                    'previous_hash': log.previous_hash,
                    'current_hash': log.current_hash,
                    'integrity_verified': verify_single_log(log)
                })
            return chain_data
        
        elif format == 'csv':
            import csv
            import io
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow([
                'Block Index', 'Timestamp', 'Event Type', 'Description',
                'User ID', 'IP Address', 'Previous Hash', 'Current Hash', 'Integrity'
            ])
            
            for log in logs:
                writer.writerow([
                    log.id,
                    log.timestamp.isoformat(),
                    log.event_type,
                    log.description,
                    log.user_id,
                    log.ip_address,
                    log.previous_hash[:16] + '...' if log.previous_hash else 'None',
                    log.current_hash[:16] + '...',
                    'Valid' if verify_single_log(log) else 'Invalid'
                ])
            
            return output.getvalue()
    
    except Exception as e:
        return f"Error exporting blockchain: {str(e)}"


# ==================== BLOCKCHAIN VISUALIZATION ====================

def get_blockchain_visualization(limit=50):
    """Get blockchain chain data for visualization"""
    try:
        logs = CryptoSecureLog.query.order_by(
            CryptoSecureLog.id.desc()
        ).limit(limit).all()
        
        logs.reverse()  # Show in chronological order
        
        chain_data = []
        for i, log in enumerate(logs):
            is_valid = verify_single_log(log)
            
            chain_data.append({
                'block_index': log.id,
                'block_number': i + 1,
                'timestamp': log.timestamp.isoformat(),
                'event_type': log.event_type,
                'description': log.description[:50] + '...' if len(log.description) > 50 else log.description,
                'current_hash': log.current_hash[:12] + '...',
                'previous_hash': log.previous_hash[:12] + '...' if log.previous_hash else 'Genesis',
                'is_valid': is_valid,
                'user': f"User_{log.user_id}" if log.user_id else 'System'
            })
        
        return {
            'total_blocks': CryptoSecureLog.query.count(),
            'displayed_blocks': len(chain_data),
            'chain': chain_data
        }
    
    except Exception as e:
        return {
            'error': str(e),
            'chain': []
        }
