"""
Flask Web Application for Log Viewer
View and analyze monitoring and failover logs
"""

from flask import Flask, render_template, jsonify, request
from pathlib import Path
import json
from datetime import datetime
from utils import read_log_file, get_all_logs

app = Flask(__name__)


@app.route('/')
def index():
    """Main dashboard"""
    return render_template('index.html')


@app.route('/api/logs/summary')
def get_summary_logs():
    """Get summary logs for table view"""

    monitor_logs = read_log_file('monitor')

    # Get filter parameters
    start_time = request.args.get('start_time')
    instance_id = request.args.get('instance_id')
    tag_name = request.args.get('tag_name')
    status = request.args.get('status')
    resource_type = request.args.get('resource_type')
    aws_profile = request.args.get('aws_profile')

    # Filter logs
    filtered_logs = monitor_logs

    if start_time:
        filtered_logs = [log for log in filtered_logs
                         if log.get('script_start_time', '').startswith(start_time)]

    if instance_id:
        filtered_logs = [log for log in filtered_logs
                         if instance_id.lower() in log.get('resource_id', '').lower()]

    if tag_name:
        filtered_logs = [log for log in filtered_logs
                         if tag_name.lower() in log.get('tag_name', '').lower()]

    if status:
        filtered_logs = [log for log in filtered_logs
                         if status.lower() in log.get('status', '').lower()]

    if resource_type:
        filtered_logs = [log for log in filtered_logs
                         if resource_type.lower() in log.get('resource_type', '').lower()]

    if aws_profile:
        filtered_logs = [log for log in filtered_logs
                         if aws_profile.lower() in log.get('aws_profile', '').lower()]

    return jsonify(filtered_logs)


@app.route('/api/logs/detailed')
def get_detailed_logs():
    """Get detailed logs"""

    all_logs = get_all_logs()

    # Combine and sort by timestamp
    combined = []

    for log_type, logs in all_logs.items():
        for log in logs:
            log['log_type'] = log_type
            combined.append(log)

    # Sort by timestamp descending
    combined.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

    return jsonify(combined)


@app.route('/api/logs/failover')
def get_failover_logs():
    """Get failover and system logs"""

    failover_logs = read_log_file('failover')

    # Get system logs from text log files
    log_dir = Path('logs')
    system_logs = []

    for log_file in log_dir.glob('failover_*.log'):
        try:
            with open(log_file, 'r') as f:
                system_logs.append({
                    'filename': log_file.name,
                    'content': f.read(),
                    'timestamp': datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
                })
        except Exception as e:
            print(f"Error reading {log_file}: {e}")

    return jsonify({
        'failover_logs': failover_logs,
        'system_logs': system_logs
    })


@app.route('/api/stats')
def get_stats():
    """Get summary statistics"""

    monitor_logs = read_log_file('monitor')
    failover_logs = read_log_file('failover')

    # Get filter parameter
    aws_profile = request.args.get('aws_profile')

    # Filter by profile if specified
    if aws_profile:
        monitor_logs = [log for log in monitor_logs
                        if aws_profile.lower() in log.get('aws_profile', '').lower()]
        failover_logs = [log for log in failover_logs
                         if aws_profile.lower() in log.get('aws_profile', '').lower()]

    # Calculate stats
    total_resources = len(monitor_logs)

    status_counts = {}
    resource_type_counts = {}
    profile_counts = {}

    for log in monitor_logs:
        status = log.get('status', 'UNKNOWN')
        resource_type = log.get('resource_type', 'UNKNOWN')
        profile = log.get('aws_profile', 'UNKNOWN')

        status_counts[status] = status_counts.get(status, 0) + 1
        resource_type_counts[resource_type] = resource_type_counts.get(resource_type, 0) + 1
        profile_counts[profile] = profile_counts.get(profile, 0) + 1

    # Failover stats
    failover_success = len([log for log in failover_logs if log.get('result') == 'SUCCESS'])
    failover_errors = len([log for log in failover_logs if log.get('result') == 'ERROR'])

    stats = {
        'total_resources': total_resources,
        'total_failovers': len(failover_logs),
        'failover_success': failover_success,
        'failover_errors': failover_errors,
        'status_counts': status_counts,
        'resource_type_counts': resource_type_counts,
        'profile_counts': profile_counts,
        'last_updated': datetime.now().isoformat()
    }

    return jsonify(stats)


@app.route('/api/profiles')
def get_profiles():
    """Get list of available AWS profiles from logs"""

    monitor_logs = read_log_file('monitor')

    # Extract unique profiles
    profiles = set()
    for log in monitor_logs:
        profile = log.get('aws_profile')
        if profile:
            profiles.add(profile)

    return jsonify(sorted(list(profiles)))


def run_server(host='0.0.0.0', port=7501, debug=True):
    """Run the Flask server"""

    # Create templates directory if it doesn't exist
    templates_dir = Path('templates')
    templates_dir.mkdir(exist_ok=True)

    # Create index.html if it doesn't exist
    index_file = templates_dir / 'index.html'
    if not index_file.exists():
        create_index_html(index_file)

    app.run(host=host, port=port, debug=debug)


def create_index_html(filepath):
    """Create the HTML template"""

    html_content = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AWS Failover Monitor</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }

        header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }

        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }

        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            text-align: center;
        }

        .stat-card h3 {
            color: #667eea;
            font-size: 0.9em;
            margin-bottom: 10px;
            text-transform: uppercase;
        }

        .stat-card .value {
            font-size: 2.5em;
            font-weight: bold;
            color: #333;
        }

        .tabs {
            display: flex;
            background: #f8f9fa;
            padding: 0 30px;
            border-bottom: 2px solid #e0e0e0;
        }

        .tab {
            padding: 15px 30px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 1.1em;
            color: #666;
            transition: all 0.3s;
        }

        .tab.active {
            color: #667eea;
            border-bottom: 3px solid #667eea;
            font-weight: bold;
        }

        .tab:hover {
            color: #667eea;
        }

        .tab-content {
            padding: 30px;
        }

        .tab-pane {
            display: none;
        }

        .tab-pane.active {
            display: block;
        }

        .filters {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }

        .filter-group {
            display: flex;
            flex-direction: column;
        }

        .filter-group label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }

        .filter-group input {
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 1em;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
            background: white;
        }

        thead {
            background: #667eea;
            color: white;
        }

        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #e0e0e0;
        }

        tbody tr:hover {
            background: #f8f9fa;
        }

        .status-badge {
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            display: inline-block;
        }

        .status-running { background: #d4edda; color: #155724; }
        .status-stopped { background: #fff3cd; color: #856404; }
        .status-terminated { background: #f8d7da; color: #721c24; }
        .status-error { background: #f8d7da; color: #721c24; }
        .status-success { background: #d4edda; color: #155724; }

        .log-entry {
            background: #f8f9fa;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }

        .log-entry pre {
            white-space: pre-wrap;
            word-wrap: break-word;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
            margin-top: 10px;
        }

        .refresh-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            margin-bottom: 20px;
        }

        .refresh-btn:hover {
            background: #5568d3;
        }

        .no-data {
            text-align: center;
            padding: 40px;
            color: #666;
            font-size: 1.2em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🔄 AWS Failover Monitor</h1>
            <p>Real-time monitoring and failover management</p>
        </header>

        <div class="stats" id="stats">
            <div class="stat-card">
                <h3>Total Resources</h3>
                <div class="value" id="totalResources">0</div>
            </div>
            <div class="stat-card">
                <h3>Total Failovers</h3>
                <div class="value" id="totalFailovers">0</div>
            </div>
            <div class="stat-card">
                <h3>Successful</h3>
                <div class="value" id="successCount">0</div>
            </div>
            <div class="stat-card">
                <h3>Errors</h3>
                <div class="value" id="errorCount">0</div>
            </div>
        </div>

        <div class="tabs">
            <button class="tab active" onclick="switchTab('summary')">Summary</button>
            <button class="tab" onclick="switchTab('detailed')">Detailed Logs</button>
            <button class="tab" onclick="switchTab('failover')">Failover Logs</button>
        </div>

        <div class="tab-content">
            <div id="summary" class="tab-pane active">
                <button class="refresh-btn" onclick="loadSummary()">🔄 Refresh</button>

                <div class="filters">
                    <div class="filter-group">
                        <label>Start Time</label>
                        <input type="text" id="filterStartTime" placeholder="YYYY-MM-DD">
                    </div>
                    <div class="filter-group">
                        <label>Instance ID</label>
                        <input type="text" id="filterInstanceId" placeholder="i-xxxxx">
                    </div>
                    <div class="filter-group">
                        <label>Tag Name</label>
                        <input type="text" id="filterTagName" placeholder="tag name">
                    </div>
                    <div class="filter-group">
                        <label>Status</label>
                        <input type="text" id="filterStatus" placeholder="running">
                    </div>
                    <div class="filter-group">
                        <label>Resource Type</label>
                        <input type="text" id="filterResourceType" placeholder="ec2">
                    </div>
                </div>

                <table id="summaryTable">
                    <thead>
                        <tr>
                            <th>Start Time</th>
                            <th>Instance ID</th>
                            <th>Tag Name</th>
                            <th>Status</th>
                            <th>Resource Type</th>
                            <th>Timestamp</th>
                        </tr>
                    </thead>
                    <tbody id="summaryBody">
                        <tr><td colspan="6" class="no-data">Loading...</td></tr>
                    </tbody>
                </table>
            </div>

            <div id="detailed" class="tab-pane">
                <button class="refresh-btn" onclick="loadDetailed()">🔄 Refresh</button>
                <div id="detailedContent">
                    <p class="no-data">Loading...</p>
                </div>
            </div>

            <div id="failover" class="tab-pane">
                <button class="refresh-btn" onclick="loadFailover()">🔄 Refresh</button>
                <div id="failoverContent">
                    <p class="no-data">Loading...</p>
                </div>
            </div>
        </div>
    </div>

    <script>
        function switchTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });

            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');

            // Load data
            if (tabName === 'summary') loadSummary();
            else if (tabName === 'detailed') loadDetailed();
            else if (tabName === 'failover') loadFailover();
        }

        function getStatusClass(status) {
            const s = status.toLowerCase();
            if (s.includes('running') || s.includes('active') || s.includes('valid')) return 'status-running';
            if (s.includes('stopped')) return 'status-stopped';
            if (s.includes('terminated') || s.includes('failed')) return 'status-terminated';
            if (s.includes('error')) return 'status-error';
            if (s.includes('success')) return 'status-success';
            return '';
        }

        function loadStats() {
            fetch('/api/stats')
                .then(r => r.json())
                .then(data => {
                    document.getElementById('totalResources').textContent = data.total_resources;
                    document.getElementById('totalFailovers').textContent = data.total_failovers;
                    document.getElementById('successCount').textContent = data.failover_success;
                    document.getElementById('errorCount').textContent = data.failover_errors;
                });
        }

        function loadSummary() {
            const params = new URLSearchParams({
                start_time: document.getElementById('filterStartTime').value,
                instance_id: document.getElementById('filterInstanceId').value,
                tag_name: document.getElementById('filterTagName').value,
                status: document.getElementById('filterStatus').value,
                resource_type: document.getElementById('filterResourceType').value
            });

            fetch('/api/logs/summary?' + params)
                .then(r => r.json())
                .then(data => {
                    const tbody = document.getElementById('summaryBody');
                    if (data.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="6" class="no-data">No data available</td></tr>';
                        return;
                    }

                    tbody.innerHTML = data.map(log => `
                        <tr>
                            <td>${log.script_start_time || 'N/A'}</td>
                            <td>${log.resource_id || 'N/A'}</td>
                            <td>${log.tag_name || 'N/A'}</td>
                            <td><span class="status-badge ${getStatusClass(log.status || '')}">${log.status || 'UNKNOWN'}</span></td>
                            <td>${log.resource_type || 'N/A'}</td>
                            <td>${log.timestamp || 'N/A'}</td>
                        </tr>
                    `).join('');
                });

            loadStats();
        }

        function loadDetailed() {
            fetch('/api/logs/detailed')
                .then(r => r.json())
                .then(data => {
                    const content = document.getElementById('detailedContent');
                    if (data.length === 0) {
                        content.innerHTML = '<p class="no-data">No detailed logs available</p>';
                        return;
                    }

                    content.innerHTML = data.map(log => `
                        <div class="log-entry">
                            <strong>${log.log_type.toUpperCase()}</strong> - ${log.resource_type || 'N/A'} - ${log.resource_id || 'N/A'}
                            <pre>${JSON.stringify(log, null, 2)}</pre>
                        </div>
                    `).join('');
                });
        }

        function loadFailover() {
            fetch('/api/logs/failover')
                .then(r => r.json())
                .then(data => {
                    const content = document.getElementById('failoverContent');

                    let html = '<h2>Failover Logs</h2>';

                    if (data.failover_logs.length === 0) {
                        html += '<p class="no-data">No failover logs available</p>';
                    } else {
                        html += data.failover_logs.map(log => `
                            <div class="log-entry">
                                <strong>${log.resource_type}</strong> - ${log.resource_id} - 
                                <span class="status-badge ${getStatusClass(log.result || '')}">${log.result || 'UNKNOWN'}</span>
                                <pre>${JSON.stringify(log, null, 2)}</pre>
                            </div>
                        `).join('');
                    }

                    html += '<h2 style="margin-top: 40px;">System Logs</h2>';

                    if (data.system_logs.length === 0) {
                        html += '<p class="no-data">No system logs available</p>';
                    } else {
                        html += data.system_logs.map(log => `
                            <div class="log-entry">
                                <strong>${log.filename}</strong> - ${log.timestamp}
                                <pre>${log.content}</pre>
                            </div>
                        `).join('');
                    }

                    content.innerHTML = html;
                });
        }

        // Add event listeners for filters
        ['filterStartTime', 'filterInstanceId', 'filterTagName', 'filterStatus', 'filterResourceType'].forEach(id => {
            document.getElementById(id).addEventListener('input', () => {
                setTimeout(loadSummary, 500);
            });
        });

        // Initial load
        loadSummary();

        // Auto refresh every 30 seconds
        setInterval(() => {
            const activeTab = document.querySelector('.tab-pane.active').id;
            if (activeTab === 'summary') loadSummary();
            else if (activeTab === 'detailed') loadDetailed();
            else if (activeTab === 'failover') loadFailover();
        }, 30000);
    </script>
</body>
</html>'''

    with open(filepath, 'w') as f:
        f.write(html_content)


if __name__ == '__main__':
    run_server()