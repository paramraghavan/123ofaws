"""
Flask routes for monitoring dashboard and API.
"""

from flask import Blueprint, render_template, jsonify, request
from utils.logger import get_logger

logger = get_logger(__name__)


def create_blueprints(daemon, failover_manager):
    """
    Create Flask blueprints for dashboard and API.

    Args:
        daemon: MonitoringDaemon instance
        failover_manager: FailoverManager instance

    Returns:
        List of blueprints
    """
    dashboard_bp = Blueprint('dashboard', __name__)
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    webhook_bp = Blueprint('webhook', __name__, url_prefix='/webhook')

    # ============ Dashboard Routes ============

    @dashboard_bp.route('/')
    def index():
        """Main dashboard view."""
        summary = daemon.get_dashboard_summary()
        return render_template('dashboard.html', summary=summary)

    @dashboard_bp.route('/service/<service_name>')
    def service_detail(service_name):
        """Service detail view."""
        state = daemon.get_service_state(service_name)
        return render_template('service_detail.html', service=service_name, state=state)

    @dashboard_bp.route('/health')
    def health_check():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'service': 'aws-monitoring',
            'daemon_running': daemon.is_running()
        })

    # ============ API Routes ============

    @api_bp.route('/status')
    def api_status():
        """Get current status for all services."""
        summary = daemon.get_dashboard_summary()
        return jsonify(summary)

    @api_bp.route('/service/<service_name>')
    def api_service_detail(service_name):
        """Get details for a specific service."""
        state = daemon.get_service_state(service_name)
        return jsonify({
            'service': service_name,
            'resources': state if isinstance(state, list) else []
        })

    @api_bp.route('/resource/<service_name>/<resource_id>')
    def api_resource_detail(service_name, resource_id):
        """Get details for a specific resource."""
        health = daemon.get_resource_health(service_name, resource_id)
        if health:
            return jsonify(health)
        else:
            return jsonify({'error': 'Resource not found'}), 404

    @api_bp.route('/daemon/status')
    def api_daemon_status():
        """Get daemon status."""
        timestamp = daemon.get_state_timestamp()
        return jsonify({
            'running': daemon.is_running(),
            'last_check': timestamp.isoformat() if timestamp else None
        })

    # ============ Webhook Routes ============

    @webhook_bp.route('/controlm', methods=['POST'])
    def webhook_controlm():
        """Control-M webhook endpoint."""
        try:
            data = request.json or {}
            logger.info(f"Received Control-M webhook: {data}")

            # Return acknowledgment
            return jsonify({
                'status': 'received',
                'message': 'Control-M event received and logged',
                'timestamp': __import__('datetime').datetime.utcnow().isoformat()
            }), 202

        except Exception as e:
            logger.error(f"Error processing Control-M webhook: {e}")
            return jsonify({'error': str(e)}), 400

    @webhook_bp.route('/health', methods=['POST'])
    def webhook_health():
        """Webhook for health status reports."""
        try:
            data = request.json or {}
            service = data.get('service')
            resource_id = data.get('resource_id')
            action = data.get('action', 'acknowledge')

            logger.info(f"Health webhook: {service}/{resource_id} - {action}")

            # Return acknowledgment
            return jsonify({
                'status': 'acknowledged',
                'service': service,
                'resource_id': resource_id,
                'action': action
            }), 200

        except Exception as e:
            logger.error(f"Error processing health webhook: {e}")
            return jsonify({'error': str(e)}), 400

    # ============ Return Blueprints ============

    return [dashboard_bp, api_bp, webhook_bp]
