from flask import Flask, render_template, jsonify, request
import json
import os
from datetime import datetime
from collections import Counter, defaultdict
from config import Config

app = Flask(__name__)
app.config.from_object(Config)


def read_jsonl_file(filepath, limit=None):
    """Read JSONL file and return list of records"""
    records = []
    if not os.path.exists(filepath):
        return records

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()
            if limit:
                lines = lines[-limit:]
            for line in lines:
                if line.strip():
                    records.append(json.loads(line))
    except Exception as e:
        print(f"Error reading file {filepath}: {str(e)}")

    return records


def analyze_status_logs(logs):
    """Analyze status logs and generate insights"""
    if not logs:
        return {}

    ec2_states = []
    emr_states = []
    timestamps = []

    for log in logs:
        timestamps.append(log.get('timestamp', ''))
        for instance in log.get('ec2_instances', []):
            ec2_states.append(instance.get('state', 'unknown'))
        for cluster in log.get('emr_clusters', []):
            emr_states.append(cluster.get('state', 'unknown'))

    analysis = {
        'total_logs': len(logs),
        'date_range': {
            'start': min(timestamps) if timestamps else 'N/A',
            'end': max(timestamps) if timestamps else 'N/A'
        },
        'ec2_state_distribution': dict(Counter(ec2_states)),
        'emr_state_distribution': dict(Counter(emr_states)),
        'latest_summary': logs[-1].get('summary', {}) if logs else {}
    }

    return analysis


def analyze_failover_logs(logs):
    """Analyze failover logs and generate insights"""
    if not logs:
        return {}

    total_ec2_attempts = 0
    total_emr_attempts = 0
    ec2_successes = 0
    emr_successes = 0

    for log in logs:
        ec2_results = log.get('ec2_results', {})
        emr_results = log.get('emr_results', {})

        total_ec2_attempts += len(ec2_results)
        total_emr_attempts += len(emr_results)

        ec2_successes += sum(1 for v in ec2_results.values() if v == 'SUCCESS')
        emr_successes += sum(1 for v in emr_results.values() if v != 'FAILED')

    analysis = {
        'total_failovers': len(logs),
        'ec2_stats': {
            'total_attempts': total_ec2_attempts,
            'successes': ec2_successes,
            'failures': total_ec2_attempts - ec2_successes,
            'success_rate': f"{(ec2_successes / total_ec2_attempts * 100):.1f}%" if total_ec2_attempts > 0 else 'N/A'
        },
        'emr_stats': {
            'total_attempts': total_emr_attempts,
            'successes': emr_successes,
            'failures': total_emr_attempts - emr_successes,
            'success_rate': f"{(emr_successes / total_emr_attempts * 100):.1f}%" if total_emr_attempts > 0 else 'N/A'
        },
        'latest_failover': logs[-1] if logs else {}
    }

    return analysis


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/api/status-logs')
def get_status_logs():
    """API endpoint to get status logs"""
    limit = request.args.get('limit', 50, type=int)
    logs = read_jsonl_file(Config.STATUS_LOG_FILE, limit=limit)
    return jsonify({
        'logs': logs,
        'count': len(logs)
    })


@app.route('/api/failover-logs')
def get_failover_logs():
    """API endpoint to get failover logs"""
    limit = request.args.get('limit', 50, type=int)
    logs = read_jsonl_file(Config.FAILOVER_LOG_FILE, limit=limit)
    return jsonify({
        'logs': logs,
        'count': len(logs)
    })


@app.route('/api/analysis/status')
def get_status_analysis():
    """API endpoint to get status log analysis"""
    logs = read_jsonl_file(Config.STATUS_LOG_FILE)
    analysis = analyze_status_logs(logs)
    return jsonify(analysis)


@app.route('/api/analysis/failover')
def get_failover_analysis():
    """API endpoint to get failover log analysis"""
    logs = read_jsonl_file(Config.FAILOVER_LOG_FILE)
    analysis = analyze_failover_logs(logs)
    return jsonify(analysis)


@app.route('/api/logs/text')
def get_text_logs():
    """API endpoint to get plain text logs"""
    limit = request.args.get('limit', 100, type=int)

    if not os.path.exists(Config.LOG_FILE):
        return jsonify({'logs': []})

    try:
        with open(Config.LOG_FILE, 'r') as f:
            lines = f.readlines()
            lines = lines[-limit:]
        return jsonify({'logs': lines})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/current-status')
def get_current_status():
    """API endpoint to get most recent status"""
    logs = read_jsonl_file(Config.STATUS_LOG_FILE, limit=1)
    if logs:
        return jsonify(logs[0])
    return jsonify({})


if __name__ == '__main__':
    Config.init_app()
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.DEBUG)
