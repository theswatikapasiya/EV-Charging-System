"""
Analytics Module
Computes real-time analytics and provides dashboard data
Tracks: energy, revenue, attacks, efficiency, trends
"""

from datetime import datetime, timedelta
from models import db, ChargingSession, AttackLog, Payment, Vehicle, User
import json
from sqlalchemy import func

# ==================== ENERGY ANALYTICS ====================

def get_total_energy_consumed(days=None):
    """Calculate total energy consumed"""
    query = ChargingSession.query
    
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(ChargingSession.start_time >= cutoff)
    
    total = db.session.query(
        func.sum(ChargingSession.energy_added)
    ).filter(ChargingSession.status == 'completed').scalar() or 0
    
    # Add live ongoing energy from memory
    try:
        from app import charging
        live_energy = sum(v.get("energy_added", 0) for v in charging)
    except:
        live_energy = 0
        
    return float(total) + float(live_energy)


def get_energy_by_date(days=7):
    """Get energy consumed by date"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    data = db.session.query(
        func.date(ChargingSession.start_time).label('date'),
        func.sum(ChargingSession.energy_added).label('energy')
    ).filter(
        ChargingSession.start_time >= cutoff,
        ChargingSession.status == 'completed'
    ).group_by(
        func.date(ChargingSession.start_time)
    ).order_by(
        'date'
    ).all()
    
    return [{
        'date': str(record.date),
        'energy': float(record.energy or 0)
    } for record in data]


# ==================== REVENUE ANALYTICS ====================

def get_total_revenue(days=None):
    """Calculate total revenue from charging"""
    query = Payment.query.filter_by(status='completed')
    
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(Payment.completed_at >= cutoff)
    
    total = db.session.query(
        func.sum(Payment.amount)
    ).filter(Payment.status == 'completed').scalar() or 0
    
    # Add live ongoing revenue from memory
    try:
        from app import charging
        live_revenue = sum(v.get("energy_added", 0) * 10 for v in charging)
    except:
        live_revenue = 0
        
    return float(total) + float(live_revenue)


def get_revenue_by_date(days=7):
    """Get revenue by date"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    data = db.session.query(
        func.date(Payment.completed_at).label('date'),
        func.sum(Payment.amount).label('revenue')
    ).filter(
        Payment.completed_at >= cutoff,
        Payment.status == 'completed'
    ).group_by(
        func.date(Payment.completed_at)
    ).order_by(
        'date'
    ).all()
    
    return [{
        'date': str(record.date),
        'revenue': float(record.revenue or 0)
    } for record in data]


# ==================== ATTACK ANALYTICS ====================

def get_total_attacks_blocked(days=None):
    """Count total attacks blocked"""
    query = AttackLog.query.filter_by(blocked=True)
    
    if days:
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(AttackLog.timestamp >= cutoff)
    
    return query.count()


def get_attacks_by_type(days=7):
    """Get breakdown of attacks by type"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    data = db.session.query(
        AttackLog.attack_type,
        func.count(AttackLog.id).label('count'),
        func.sum(
            func.cast(AttackLog.blocked, db.Integer)
        ).label('blocked')
    ).filter(AttackLog.timestamp >= cutoff).group_by(
        AttackLog.attack_type
    ).all()
    
    return [{
        'attack_type': record.attack_type,
        'total': record.count,
        'blocked': int(record.blocked or 0)
    } for record in data]


def get_most_common_attack(days=7):
    """Get most common attack type"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    most_common = db.session.query(
        AttackLog.attack_type,
        func.count(AttackLog.id).label('count')
    ).filter(AttackLog.timestamp >= cutoff).group_by(
        AttackLog.attack_type
    ).order_by(
        'count DESC'
    ).first()
    
    if most_common:
        return {
            'attack_type': most_common.attack_type,
            'count': most_common.count
        }
    return None


def get_attacks_by_severity(days=7):
    """Get attacks breakdown by severity"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    data = db.session.query(
        AttackLog.severity,
        func.count(AttackLog.id).label('count')
    ).filter(AttackLog.timestamp >= cutoff).group_by(
        AttackLog.severity
    ).all()
    
    return [{
        'severity': record.severity,
        'count': record.count
    } for record in data]


# ==================== CHARGING SESSION ANALYTICS ====================

def get_average_charging_time(days=7):
    """Calculate average charging time in minutes"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    sessions = ChargingSession.query.filter(
        ChargingSession.start_time >= cutoff,
        ChargingSession.status == 'completed',
        ChargingSession.end_time.isnot(None)
    ).all()
    
    if not sessions:
        try:
            from app import charging
            if charging:
                return 25 # Return baseline estimate if cars are charging but none finished
        except:
            pass
        return 0
    
    total_duration = 0
    for session in sessions:
        duration = (session.end_time - session.start_time).total_seconds() / 60
        total_duration += duration
    
    return round(total_duration / len(sessions), 2)


def get_charging_efficiency(days=7):
    """Calculate charging efficiency (actual vs. estimated)"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    completed_sessions = ChargingSession.query.filter(
        ChargingSession.start_time >= cutoff,
        ChargingSession.status == 'completed'
    ).all()
    
    if not completed_sessions:
        try:
            from app import charging
            if charging:
                return 98 # Return baseline efficiency if cars are actively charging
        except:
            pass
        return 0
    
    total_efficiency = 0
    for session in completed_sessions:
        if session.estimated_completion and session.actual_completion:
            estimated_duration = (session.estimated_completion - session.start_time).total_seconds()
            actual_duration = (session.actual_completion - session.start_time).total_seconds()
            if estimated_duration > 0:
                efficiency = (estimated_duration / actual_duration) * 100
                total_efficiency += efficiency
    
    return round(total_efficiency / len(completed_sessions), 2) if completed_sessions else 0


# ==================== PEAK HOURS ANALYSIS ====================

def get_peak_charging_hours(days=7):
    """Identify peak charging hours"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    hourly_data = {}
    sessions = ChargingSession.query.filter(
        ChargingSession.start_time >= cutoff
    ).all()
    
    for session in sessions:
        hour = session.start_time.hour
        hourly_data[hour] = hourly_data.get(hour, 0) + 1
    
    if not hourly_data:
        return None
    
    peak_hour = max(hourly_data, key=hourly_data.get)
    return {
        'hour': peak_hour,
        'sessions': hourly_data[peak_hour],
        'hourly_breakdown': hourly_data
    }


# ==================== VEHICLE ANALYTICS ====================

def get_vehicle_statistics(days=7):
    """Get vehicle-related statistics"""
    cutoff = datetime.utcnow() - timedelta(days=days)
    
    total_vehicles = Vehicle.query.count()
    active_sessions = ChargingSession.query.filter_by(status='active').count()
    completed_sessions = ChargingSession.query.filter(
        ChargingSession.start_time >= cutoff,
        ChargingSession.status == 'completed'
    ).count()
    
    return {
        'total_vehicles': total_vehicles,
        'active_sessions': active_sessions,
        'completed_sessions': completed_sessions,
        'avg_sessions_per_vehicle': round(completed_sessions / total_vehicles, 2) if total_vehicles > 0 else 0
    }


# ==================== USER ANALYTICS ====================

def get_user_statistics():
    """Get user-related statistics"""
    total_users = User.query.count()
    admins = User.query.filter_by(role='admin').count()
    operators = User.query.filter_by(role='operator').count()
    regular_users = User.query.filter_by(role='user').count()
    
    return {
        'total_users': total_users,
        'admins': admins,
        'operators': operators,
        'regular_users': regular_users
    }


# ==================== COMPREHENSIVE DASHBOARD ====================

def get_dashboard_summary(days=7):
    """Get comprehensive dashboard summary"""
    try:
        summary = {
            'timestamp': datetime.utcnow().isoformat(),
            'period_days': days,
            
            # Energy
            'total_energy_consumed': get_total_energy_consumed(days),
            'energy_by_date': get_energy_by_date(min(days, 7)),
            
            # Revenue
            'total_revenue': get_total_revenue(days),
            'revenue_by_date': get_revenue_by_date(min(days, 7)),
            'average_session_cost': 0,
            
            # Attacks
            'total_attacks_blocked': get_total_attacks_blocked(days),
            'attacks_by_type': get_attacks_by_type(days),
            'most_common_attack': get_most_common_attack(days),
            'attacks_by_severity': get_attacks_by_severity(days),
            
            # Charging
            'average_charging_time': get_average_charging_time(days),
            'charging_efficiency': get_charging_efficiency(days),
            'peak_charging_hours': get_peak_charging_hours(days),
            
            # Vehicles
            'vehicle_stats': get_vehicle_statistics(days),
            
            # Users
            'user_stats': get_user_statistics()
        }
        
        # Calculate average session cost
        total_sessions = ChargingSession.query.filter(
            ChargingSession.status == 'completed'
        ).count()
        if total_sessions > 0:
            summary['average_session_cost'] = round(summary['total_revenue'] / total_sessions, 2)
        
        return summary
    
    except Exception as e:
        print(f"Dashboard summary error: {e}")
        return None


# ==================== PREDICTIVE ANALYTICS ====================

def forecast_energy_demand(days_ahead=7):
    """Simple forecast of energy demand based on recent trends"""
    historical_data = get_energy_by_date(14)
    
    if len(historical_data) < 2:
        return None
    
    # Simple linear trend
    values = [d['energy'] for d in historical_data]
    n = len(values)
    avg_increase = (values[-1] - values[0]) / n if n > 0 else 0
    
    forecast = []
    last_value = values[-1] if values else 0
    
    for i in range(days_ahead):
        predicted_value = max(0, last_value + avg_increase)
        forecast.append({
            'day': i + 1,
            'predicted_energy': round(predicted_value, 2)
        })
        last_value = predicted_value
    
    return forecast


def forecast_revenue(days_ahead=7):
    """Simple forecast of revenue based on recent trends"""
    historical_data = get_revenue_by_date(14)
    
    if len(historical_data) < 2:
        return None
    
    values = [d['revenue'] for d in historical_data]
    n = len(values)
    avg_increase = (values[-1] - values[0]) / n if n > 0 else 0
    
    forecast = []
    last_value = values[-1] if values else 0
    
    for i in range(days_ahead):
        predicted_value = max(0, last_value + avg_increase)
        forecast.append({
            'day': i + 1,
            'predicted_revenue': round(predicted_value, 2)
        })
        last_value = predicted_value
    
    return forecast
