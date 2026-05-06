"""
Analytics Routes
Provides analytics endpoints for dashboard visualization
"""

from flask import Blueprint, request, jsonify
from analytics import (
    get_dashboard_summary, get_total_energy_consumed, get_total_revenue,
    get_total_attacks_blocked, get_average_charging_time, get_charging_efficiency,
    get_peak_charging_hours, get_vehicle_statistics, get_user_statistics,
    get_attacks_by_type, get_most_common_attack, forecast_energy_demand,
    forecast_revenue, get_energy_by_date, get_revenue_by_date
)
from auth import role_required
from datetime import datetime, timedelta

analytics_bp = Blueprint('analytics', __name__, url_prefix='/analytics')

# ==================== DASHBOARD ====================

@analytics_bp.route('/dashboard', methods=['GET'])
@role_required(['admin', 'operator'])
def dashboard():
    """Get complete dashboard data"""
    try:
        days = request.args.get('days', 7, type=int)
        summary = get_dashboard_summary(days)
        
        if summary:
            return jsonify({
                'status': 'success',
                'dashboard': summary
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Failed to generate dashboard'
            }), 500
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500


# ==================== ENERGY ANALYTICS ====================

@analytics_bp.route('/energy/total', methods=['GET'])
@role_required(['admin', 'operator'])
def energy_total():
    """Get total energy consumed"""
    try:
        days = request.args.get('days', None, type=int)
        total = get_total_energy_consumed(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'total_energy_consumed',
            'value': total,
            'unit': 'kWh',
            'period_days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/energy/by-date', methods=['GET'])
@role_required(['admin', 'operator'])
def energy_by_date():
    """Get energy consumption by date"""
    try:
        days = request.args.get('days', 7, type=int)
        data = get_energy_by_date(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'energy_by_date',
            'data': data,
            'unit': 'kWh',
            'days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== REVENUE ANALYTICS ====================

@analytics_bp.route('/revenue/total', methods=['GET'])
@role_required(['admin', 'operator'])
def revenue_total():
    """Get total revenue"""
    try:
        days = request.args.get('days', None, type=int)
        total = get_total_revenue(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'total_revenue',
            'value': total,
            'currency': 'INR',
            'period_days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/revenue/by-date', methods=['GET'])
@role_required(['admin', 'operator'])
def revenue_by_date():
    """Get revenue by date"""
    try:
        days = request.args.get('days', 7, type=int)
        data = get_revenue_by_date(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'revenue_by_date',
            'data': data,
            'currency': 'INR',
            'days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== ATTACK ANALYTICS ====================

@analytics_bp.route('/attacks/blocked', methods=['GET'])
@role_required(['admin', 'operator'])
def attacks_blocked():
    """Get total attacks blocked"""
    try:
        days = request.args.get('days', 7, type=int)
        total = get_total_attacks_blocked(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'total_attacks_blocked',
            'value': total,
            'period_days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/attacks/by-type', methods=['GET'])
@role_required(['admin', 'operator'])
def attacks_by_type():
    """Get attacks breakdown by type"""
    try:
        days = request.args.get('days', 7, type=int)
        data = get_attacks_by_type(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'attacks_by_type',
            'data': data,
            'days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/attacks/most-common', methods=['GET'])
@role_required(['admin', 'operator'])
def most_common_attack():
    """Get most common attack type"""
    try:
        days = request.args.get('days', 7, type=int)
        data = get_most_common_attack(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'most_common_attack',
            'data': data,
            'days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== CHARGING ANALYTICS ====================

@analytics_bp.route('/charging/avg-time', methods=['GET'])
@role_required(['admin', 'operator'])
def charging_avg_time():
    """Get average charging time"""
    try:
        days = request.args.get('days', 7, type=int)
        avg_time = get_average_charging_time(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'average_charging_time',
            'value': avg_time,
            'unit': 'minutes',
            'period_days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/charging/efficiency', methods=['GET'])
@role_required(['admin', 'operator'])
def charging_efficiency_metric():
    """Get charging efficiency"""
    try:
        days = request.args.get('days', 7, type=int)
        efficiency = get_charging_efficiency(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'charging_efficiency',
            'value': efficiency,
            'unit': 'percentage',
            'period_days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/charging/peak-hours', methods=['GET'])
@role_required(['admin', 'operator'])
def peak_hours():
    """Get peak charging hours"""
    try:
        days = request.args.get('days', 7, type=int)
        peaks = get_peak_charging_hours(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'peak_charging_hours',
            'data': peaks,
            'period_days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== VEHICLE ANALYTICS ====================

@analytics_bp.route('/vehicles/stats', methods=['GET'])
@role_required(['admin', 'operator'])
def vehicle_stats():
    """Get vehicle statistics"""
    try:
        days = request.args.get('days', 7, type=int)
        stats = get_vehicle_statistics(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'vehicle_statistics',
            'data': stats,
            'period_days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== USER ANALYTICS ====================

@analytics_bp.route('/users/stats', methods=['GET'])
@role_required(['admin'])
def user_stats():
    """Get user statistics"""
    try:
        stats = get_user_statistics()
        
        return jsonify({
            'status': 'success',
            'metric': 'user_statistics',
            'data': stats
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== FORECASTING ====================

@analytics_bp.route('/forecast/energy', methods=['GET'])
@role_required(['admin', 'operator'])
def forecast_energy():
    """Forecast energy demand"""
    try:
        days = request.args.get('days', 7, type=int)
        forecast = forecast_energy_demand(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'energy_forecast',
            'forecast': forecast,
            'unit': 'kWh',
            'forecast_days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@analytics_bp.route('/forecast/revenue', methods=['GET'])
@role_required(['admin', 'operator'])
def forecast_revenue_endpoint():
    """Forecast revenue"""
    try:
        days = request.args.get('days', 7, type=int)
        forecast = forecast_revenue(days)
        
        return jsonify({
            'status': 'success',
            'metric': 'revenue_forecast',
            'forecast': forecast,
            'currency': 'INR',
            'forecast_days': days
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== EXPORT ====================

@analytics_bp.route('/export', methods=['GET'])
@role_required(['admin', 'operator'])
def export_analytics():
    """Export analytics data as JSON"""
    try:
        days = request.args.get('days', 7, type=int)
        format_type = request.args.get('format', 'json', type=str)
        
        dashboard = get_dashboard_summary(days)
        
        if format_type == 'json':
            return jsonify({
                'status': 'success',
                'format': 'json',
                'data': dashboard,
                'exported_at': datetime.utcnow().isoformat()
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': 'Unsupported format'
            }), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ==================== REAL-TIME STATS ====================

@analytics_bp.route('/realtime/stats', methods=['GET'])
@role_required(['admin', 'operator'])
def realtime_stats():
    """Get real-time system statistics"""
    try:
        from models import ChargingSession, AttackLog, User
        
        active_sessions = ChargingSession.query.filter_by(status='active').count()
        total_sessions = ChargingSession.query.count()
        total_attacks = AttackLog.query.count()
        recent_attacks = AttackLog.query.filter(
            AttackLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
        ).count()
        total_users = User.query.count()
        
        return jsonify({
            'status': 'success',
            'realtime_stats': {
                'active_sessions': active_sessions,
                'total_sessions': total_sessions,
                'total_attacks': total_attacks,
                'recent_attacks_1h': recent_attacks,
                'total_users': total_users,
                'timestamp': datetime.utcnow().isoformat()
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

