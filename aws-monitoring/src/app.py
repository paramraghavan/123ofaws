"""
Flask application for AWS Monitoring Dashboard.
"""

from flask import Flask
from web.routes import create_blueprints
from utils.logger import get_logger

logger = get_logger(__name__)


def create_app(daemon, failover_manager):
    """
    Create and configure Flask application.

    Args:
        daemon: MonitoringDaemon instance
        failover_manager: FailoverManager instance

    Returns:
        Configured Flask app
    """
    app = Flask(__name__, template_folder='web/templates', static_folder='web/static')
    app.config['JSON_SORT_KEYS'] = False

    # Register blueprints
    blueprints = create_blueprints(daemon, failover_manager)
    for bp in blueprints:
        app.register_blueprint(bp)

    logger.info("Flask application created and configured")

    return app
