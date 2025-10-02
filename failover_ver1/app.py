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


def get_status_table_data():
    """Extract status data in table format"""
    logs = read_jsonl_file(Config.STATUS_LOG_FILE)
    table_data = []

    for log in logs:
        timestamp = log.get('timestamp', '')

        # Process EC2 instances
        for instance in log.get('ec2_instances', []):
            tags = instance.get('tags', {})
            tag_name = tags.get('Name', 'N/A')

            table_data.append({
                'failover_run_time': timestamp,
                'instance_id': instance.get('instance_id', 'N/A'),
                'tag_name': tag_name,
                'status': instance.get('state', 'unknown'),
                'type': 'EC2'
            })

        # Process EMR clusters
        for cluster in log.get('emr_clusters', []):
            table_data.append({
                'failover_run_time': timestamp,
                'instance_id': cluster.get('cluster_id', 'N/A'),
                'tag_name': cluster.get('name', 'N/A'),
                'status': cluster.get('state', 'unknown'),
                'type': 'EMR'
            })

        # Process RDS instances
        for rds in log.get('rds_instances', []):
            table_data.append({
                'failover_run_time': timestamp,
                'instance_id': rds.get('instance_id', 'N/A'),
                'tag_name': f"{rds.get('engine', 'N/A')} - {rds.get('instance_class', 'N/A')}",
                'status': rds.get('status', 'unknown'),
                'type': 'RDS'
            })

        # Process Lambda functions
        for func in log.get('lambda_functions', []):
            table_data.append({
                'failover_run_time': timestamp,
                'instance_id': func.get('function_name', 'N/A'),
                'tag_name': func.get('runtime', 'N/A'),
                'status': func.get('state', 'unknown'),
                'type': 'Lambda'
            })

        # Process ECS services
        for ecs in log.get('ecs_services', []):
            table_data.append({
                'failover_run_time': timestamp,
                'instance_id': ecs.get('service_name', 'N/A'),
                'tag_name': f"{ecs.get('cluster_name', 'N/A')} ({ecs.get('running_count', 0)}/{ecs.get('desired_count', 0)})",
                'status': ecs.get('status', 'unknown'),
                'type': 'ECS'
            })

        # Process ElastiCache clusters
        for cache in log.get('elasticache_clusters', []):
            table_data.append({
                'failover_run_time': timestamp,
                'instance_id': cache.get('cluster_id', 'N/A'),
                'tag_name': f"{cache.get('engine', 'N/A')} - {cache.get('node_type', 'N/A')}",
                'status': cache.get('status', 'unknown'),
                'type': 'ElastiCache'
            })

        # Process Auto Scaling Groups
        for asg in log.get('auto_scaling_groups', []):
            table_data.append({
                'failover_run_time': timestamp,
                'instance_id': asg.get('asg_name', 'N/A'),
                'tag_name': f"{asg.get('instance_count', 0)}/{asg.get('desired_capacity', 0)} instances",
                'status': 'ACTIVE' if asg.get('instance_count', 0) >= asg.get('min_size', 0) else 'DEGRADED',
                'type': 'ASG'
            })

    return table_data


def get_custom_resources_table_data():
    """Extract custom resource data in table format"""
    logs = read_jsonl_file(Config.CUSTOM_RESOURCES_LOG_FILE)
    table_data = []

    for log in logs:
        timestamp = log.get('timestamp', '')

        # Process each custom resource
        for resource in log.get('custom_resources', []):
            resource_name = (resource.get('name') or
                             resource.get('url') or
                             f"{resource.get('host', 'N/A')}:{resource.get('port', 'N/A')}")

            table_data.append({
                'timestamp': timestamp,
                'resource_name': resource_name,
                'resource_type': resource.get('resource_type', 'UNKNOWN'),
                'status': resource.get('status', 'unknown'),
                'response_time_ms': resource.get('response_time_ms'),
                'error': resource.get('error', '')
            })

    return table_data


def analyze_custom_resources(logs):
    """Analyze custom resource logs and generate insights"""
    if not logs:
        return {}

    total_checks = 0
    healthy = 0
    unhealthy = 0
    resource_types = []

    for log in logs:
        total_checks += log.get('summary', {}).get('total_resources', 0)
        healthy += log.get('summary', {}).get('healthy', 0)
        unhealthy += log.get('summary', {}).get('unhealthy', 0)

        for resource in log.get('custom_resources', []):
            resource_types.append(resource.get('resource_type', 'UNKNOWN'))

    analysis = {
        'total_checks': total_checks,
        'total_healthy': healthy,
        'total_unhealthy': unhealthy,
        'success_rate': f"{(healthy / total_checks * 100):.1f}%" if total_checks > 0 else 'N/A',
        'resource_type_distribution': dict(Counter(resource_types)),
        'latest_check': logs[-1] if logs else {}
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


@app.route('/api/status-table')
def get_status_table():
    """API endpoint to get status table data"""
    table_data = get_status_table_data()
    # Return most recent entries
    limit = request.args.get('limit', 100, type=int)
    return jsonify({
        'data': table_data[-limit:] if len(table_data) > limit else table_data,
        'count': len(table_data)
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


@app.route('/api/custom-resources')
def get_custom_resources():
    """API endpoint to get custom resource logs"""
    limit = request.args.get('limit', 50, type=int)
    logs = read_jsonl_file(Config.CUSTOM_RESOURCES_LOG_FILE, limit=limit)
    return jsonify({
        'logs': logs,
        'count': len(logs)
    })


@app.route('/api/custom-resources-table')
def get_custom_resources_table():
    """API endpoint to get custom resources table data"""
    table_data = get_custom_resources_table_data()
    # Return most recent entries
    limit = request.args.get('limit', 100, type=int)
    return jsonify({
        'data': table_data[-limit:] if len(table_data) > limit else table_data,
        'count': len(table_data)
    })


@app.route('/api/analysis/custom-resources')
def get_custom_resources_analysis():
    """API endpoint to get custom resource analysis"""
    logs = read_jsonl_file(Config.CUSTOM_RESOURCES_LOG_FILE)
    analysis = analyze_custom_resources(logs)
    return jsonify(analysis)


if __name__ == '__main__':
    Config.init_app()
    app.run(host=Config.FLASK_HOST, port=Config.FLASK_PORT, debug=Config.DEBUG)