/**
 * EV CHARGING COMMAND CENTER - ADVANCED DASHBOARD JS
 * ===================================================
 * Real-time WebSocket integration, advanced charts, analytics
 */

class EVChargingDashboard {
    constructor() {
        this.socket = null;
        this.currentUser = null;
        this.accessToken = localStorage.getItem('accessToken');
        this.charts = {};
        this.updateInterval = 3000; // 3 seconds
        this.init();
    }

    init() {
        this.setupEventListeners();
        if (this.accessToken) {
            this.showDashboard();
            this.initWebSocket();
            this.startAutoUpdate();
        }
    }

    setupEventListeners() {
        document.addEventListener('DOMContentLoaded', () => {
            console.log('Dashboard initialized');
        });
    }

    // ==================== WEBSOCKET ====================
    initWebSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('💫 WebSocket connected');
            this.socket.emit('subscribe', {channel: 'charging_updates'});
            this.socket.emit('subscribe', {channel: 'attacks'});
        });

        this.socket.on('charging_update', (data) => {
            console.log('⚡ Charging update:', data);
            this.updateDashboard();
        });

        this.socket.on('attack_detected', (data) => {
            console.log('🚨 Attack detected:', data);
            this.showNotification('Attack Detected', data.attack_type, 'danger');
            this.updateSecurityDashboard();
        });

        this.socket.on('threat_level_update', (data) => {
            this.updateThreatLevel(data);
        });

        this.socket.on('disconnect', () => {
            console.log('⚠️ WebSocket disconnected');
        });
    }

    // ==================== NOTIFICATIONS ====================
    showNotification(title, message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type}`;
        notification.innerHTML = `
            <div class="alert-icon">🔔</div>
            <div class="alert-content">
                <div class="alert-title">${title}</div>
                <div class="alert-message">${message}</div>
            </div>
        `;

        document.body.appendChild(notification);
        setTimeout(() => notification.remove(), 5000);
    }

    // ==================== CHARTS ====================
    initAttackDistributionChart(data) {
        const ctx = document.getElementById('attackChart');
        if (!ctx) return;

        if (this.charts.attackChart) {
            this.charts.attackChart.destroy();
        }

        this.charts.attackChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: Object.keys(data),
                datasets: [{
    label: 'Attacks',
    data: Object.values(data),

    backgroundColor: [
        '#ff4d4d',
        '#00e5ff',
        '#ffd93d',
        '#00ff88'
    ],

    borderColor: [
        '#ff8080',
        '#66f2ff',
        '#ffe680',
        '#66ffb3'
    ],

    borderWidth: 2
}]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        labels: {color: '#e0e0ff'},
                        position: 'bottom'
                    }
                }
            }
        });
    }

    initSeverityChart(data) {
        const ctx = document.getElementById('severityChart');
        if (!ctx) return;

        if (this.charts.severityChart) {
            this.charts.severityChart.destroy();
        }

        const colors = {
            'critical': '#ef4444',
            'high': '#ff7f00',
            'medium': '#facc15',
            'low': '#34d399'
        };

        this.charts.severityChart = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: Object.keys(data),
                datasets: [{
                    data: Object.values(data),
                    backgroundColor: Object.keys(data).map(k => colors[k] || '#00f5ff'),
                    borderColor: '#0f172a',
                    borderWidth: 2
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {labels: {color: '#e0e0ff'}}
                }
            }
        });
    }

    // ==================== DATA UPDATES ====================
    async updateDashboard() {
    try {

        const response = await fetch('/status');
        const data = await response.json();

        this.updateVehiclesPanel(data);

        this.updateAttackChart(data.attack_logs);

        this.updateSystemLogs(data.logs);

    } catch (e) {
        console.error('Error updating dashboard:', e);
    }
}

    async updateSecurityDashboard() {
        try {
            const threatResponse = await fetch('/api/security/threat-level');
            const threatData = await threatResponse.json();

            if (threatData.status === 'success') {
                this.updateThreatLevel(threatData);
            }

            const ipResponse = await fetch('/api/security/ip-reputation');
            const ipData = await ipResponse.json();
            
            if (ipData.status === 'success') {
                this.updateIPTable(ipData.ips);
            }
        } catch (e) {
            console.error('Error updating security dashboard:', e);
        }
    }

    updateThreatLevel(data) {
        const threatElement = document.getElementById('threatLevel');
        const riskElement = document.getElementById('riskScore');
        const badge = document.getElementById('threatBadge');

        if (threatElement) threatElement.textContent = data.threat_level.toUpperCase();
        if (riskElement) riskElement.textContent = data.risk_score;
        
        if (badge) {
            badge.className = `threat-badge threat-${data.threat_level}`;
            badge.textContent = `🛡️ THREAT: ${data.threat_level.toUpperCase()}`;
        }
    }

    updateVehiclesPanel(data) {
        if (data.entered) {
            this.updatePanel('queuePanel', data.entered);
        }
        if (data.charging) {
            this.updatePanel('chargingPanel', data.charging);
        }
        if (data.completed) {
            this.updatePanel('completedPanel', data.completed);
        }
    }

    updatePanel(panelId, items) {
        const panel = document.getElementById(panelId);
        if (!panel) return;

        panel.innerHTML = '';
        if (!items || items.length === 0) {
            panel.innerHTML = '<p style="color:#94a3b8;font-size:12px;">No data</p>';
            return;
        }

        items.slice(0, 5).forEach(item => {
            let content = `
                <div style="padding:10px; background:rgba(0,245,255,0.1); border-radius:6px; margin:5px 0; font-size:12px; border-left:3px solid #00f5ff;">
            `;
            
            if (item.vehicle_id) content += `🚗 ${item.vehicle_id}<br>`;
            if (item.driver) content += `👤 ${item.driver}<br>`;
            if (item.battery) content += `🔋 ${item.battery}%<br>`;
            if (item.energy_added) content += `⚡ +${item.energy_added}%<br>`;
            if (item.bill) content += `💰 ₹${item.bill}`;
            
            content += '</div>';
            panel.innerHTML += content;
        });
    }

    updateAttackChart(attackLogs) {
        const counts = {Replay: 0, Fake: 0, Missing: 0, DoS: 0};
        
        if (attackLogs && Array.isArray(attackLogs)) {
            attackLogs.forEach(log => {
                const event = log.event || '';
                if (event.includes('REPLAY')) counts.Replay++;
                if (event.includes('FAKE')) counts.Fake++;
                if (event.includes('MISSING')) counts.Missing++;
                if (event.includes('DOS')) counts.DoS++;
            });
        }

        this.initAttackDistributionChart(counts);
    }

    updateSystemLogs(logs) {

    const tableBody = document.getElementById('systemLogsBody');

    if (!tableBody) {
        console.error('systemLogsBody not found');
        return;
    }

    tableBody.innerHTML = '';

    if (!Array.isArray(logs)) {
        console.error('Logs is not array:', logs);
        return;
    }

    logs.slice().reverse().forEach(log => {

        const row = document.createElement('tr');

        row.innerHTML = `
            <td style="padding:10px;">${log.time || '-'}</td>
            <td style="padding:10px;">${log.event || '-'}</td>
            <td style="padding:10px;">${log.details || '-'}</td>
        `;

        tableBody.appendChild(row);
    });
}

    updateIPTable(ips) {
        const table = document.getElementById('ipReputationTable');
        if (!table) return;

        table.innerHTML = '';
        if (!ips || ips.length === 0) return;

        ips.slice(0, 10).forEach(ip => {
            const row = table.insertRow();
            row.innerHTML = `
                <td><code>${ip.ip}</code></td>
                <td>${ip.attack_count}</td>
                <td><span style="padding:4px 8px; border-radius:4px; font-size:11px; font-weight:bold; background:rgba(239,68,68,0.2); color:#ef4444;">${ip.risk_level.toUpperCase()}</span></td>
                <td>${ip.last_seen ? new Date(ip.last_seen).toLocaleTimeString() : 'N/A'}</td>
            `;
        });
    }

    // ==================== AUTO-UPDATE ====================
    startAutoUpdate() {
        setInterval(() => {
            this.updateDashboard();
            this.updateSecurityDashboard();
        }, this.updateInterval);
    }

    // ==================== UTILITY ====================
    showDashboard() {
        const authContainer = document.getElementById('authContainer');
        const dashboard = document.getElementById('dashboard');

        if (authContainer) authContainer.style.display = 'none';
        if (dashboard) dashboard.classList.remove('dashboard-hidden');
    }
}

// Initialize dashboard on page load
document.addEventListener('DOMContentLoaded', () => {
    window.evDashboard = new EVCharingDashboard();
});
