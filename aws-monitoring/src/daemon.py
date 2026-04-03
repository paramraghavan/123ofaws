"""
Monitoring daemon - runs health checks in background thread.
Checks resources periodically and triggers alerts on status changes.
"""

import threading
import time
from typing import Dict, List, Any, Optional
from datetime import datetime
from utils.logger import get_logger
from monitors.base_monitor import HealthStatus, ResourceHealth

logger = get_logger(__name__)


class MonitoringDaemon:
    """Background daemon for periodic health checks."""

    def __init__(
        self,
        config: Any,
        monitors: Dict[str, Any],
        alert_manager: Any,
        state_manager: Any
    ):
        """
        Initialize monitoring daemon.

        Args:
            config: Configuration object with check_interval
            monitors: Dictionary of service monitors
            alert_manager: Alert manager for sending notifications
            state_manager: State storage manager
        """
        self.config = config
        self.monitors = monitors
        self.alert_manager = alert_manager
        self.state_manager = state_manager
        self.logger = logger
        self.stop_event = threading.Event()
        self.thread = None
        self.current_state = {}
        self.previous_state = {}
        self._lock = threading.Lock()
        self._resource_map = {}  # Maps service -> [resource_ids]

    def set_resource_map(self, resource_map: Dict[str, List[str]]) -> None:
        """
        Set the resources to monitor for each service.

        Args:
            resource_map: Dict mapping service names to resource lists
        """
        with self._lock:
            self._resource_map = resource_map
        self.logger.info(f"Resource map configured: {self._count_resources(resource_map)} total resources")

    def _count_resources(self, resource_map: Dict[str, List[str]]) -> int:
        """Count total resources across all services."""
        return sum(len(resources) for resources in resource_map.values())

    def start(self) -> None:
        """Start monitoring daemon."""
        self.logger.info("Starting monitoring daemon")
        self.stop_event.clear()
        self.thread = threading.Thread(target=self._run, daemon=True)
        self.thread.start()

    def stop(self) -> None:
        """Gracefully stop monitoring daemon."""
        self.logger.info("Stopping monitoring daemon")
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=10)
        self.logger.info("Monitoring daemon stopped")

    def is_running(self) -> bool:
        """Check if daemon is running."""
        return self.thread and self.thread.is_alive()

    def _run(self) -> None:
        """Main monitoring loop."""
        self.logger.info(f"Monitoring loop started (interval: {self.config.check_interval}s)")

        while not self.stop_event.is_set():
            try:
                self._check_all_services()
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}", exc_info=True)

            # Sleep with interrupt checking
            self.stop_event.wait(self.config.check_interval)

    def _check_all_services(self) -> None:
        """Run health checks for all services."""
        with self._lock:
            resource_map = self._resource_map.copy()

        results = {}

        for service_name, resource_ids in resource_map.items():
            if not resource_ids:
                continue

            if service_name not in self.monitors:
                self.logger.warning(f"No monitor configured for service: {service_name}")
                continue

            try:
                monitor = self.monitors[service_name]
                self.logger.info(f"Checking {service_name} ({len(resource_ids)} resources)")

                health_results = monitor.check_health(resource_ids)
                results[service_name] = [h.to_dict() for h in health_results]

                # Check for alerts on status changes
                for health in health_results:
                    if monitor.should_alert(health):
                        self._handle_alert(service_name, health)

            except Exception as e:
                self.logger.error(f"Error checking {service_name}: {e}", exc_info=True)
                results[service_name] = {
                    'error': str(e),
                    'status': 'unknown',
                    'timestamp': datetime.utcnow().isoformat()
                }

        # Update state (thread-safe)
        with self._lock:
            self.previous_state = self.current_state.copy()
            self.current_state = results

        # Persist state
        self.state_manager.save_state(results)

    def _handle_alert(self, service_name: str, health: ResourceHealth) -> None:
        """
        Handle alert for unhealthy resource.

        Checks if this is a new issue or status change to avoid duplicate alerts.
        """
        try:
            resource_key = f"{service_name}:{health.resource_id}"

            # Check if this is a new or changed alert
            previous_status = self._get_previous_status(service_name, health.resource_id)

            if previous_status != health.status.value:
                self.logger.info(
                    f"Alert triggered for {resource_key}: "
                    f"{previous_status or 'new'} -> {health.status.value}"
                )
                self.alert_manager.send_alert(service_name, health)
            else:
                self.logger.debug(f"Suppressing duplicate alert for {resource_key}")

        except Exception as e:
            self.logger.error(f"Error handling alert: {e}", exc_info=True)

    def _get_previous_status(self, service_name: str, resource_id: str) -> Optional[str]:
        """Get previous status for a resource."""
        try:
            if service_name not in self.previous_state:
                return None

            service_results = self.previous_state[service_name]
            if isinstance(service_results, dict) and 'error' in service_results:
                return None

            if isinstance(service_results, list):
                for result in service_results:
                    if result.get('resource_id') == resource_id:
                        return result.get('status')

        except Exception:
            pass

        return None

    def get_current_state(self) -> Dict[str, Any]:
        """
        Get current monitoring state (thread-safe).

        Returns:
            Dictionary with current health status for all services
        """
        with self._lock:
            return self.current_state.copy()

    def get_state_timestamp(self) -> Optional[datetime]:
        """Get timestamp of last state update."""
        return self.state_manager.get_last_update_time()

    def get_service_state(self, service_name: str) -> Any:
        """Get state for a specific service."""
        with self._lock:
            return self.current_state.get(service_name, {})

    def get_resource_health(self, service_name: str, resource_id: str) -> Optional[Dict]:
        """Get health status for a specific resource."""
        with self._lock:
            service_data = self.current_state.get(service_name, [])

            if isinstance(service_data, list):
                for resource in service_data:
                    if resource.get('resource_id') == resource_id:
                        return resource

        return None

    def get_dashboard_summary(self) -> Dict[str, Any]:
        """Get summary for dashboard display."""
        with self._lock:
            state = self.current_state.copy()

        summary = {
            'timestamp': self.get_state_timestamp().isoformat()
            if self.get_state_timestamp() else None,
            'services': {},
            'total_resources': 0,
            'healthy': 0,
            'degraded': 0,
            'unhealthy': 0,
            'unknown': 0
        }

        for service_name, service_data in state.items():
            if isinstance(service_data, list):
                summary['services'][service_name] = {
                    'count': len(service_data),
                    'healthy': 0,
                    'degraded': 0,
                    'unhealthy': 0,
                    'unknown': 0,
                    'resources': []
                }

                for resource in service_data:
                    status = resource.get('status', 'unknown')
                    summary['services'][service_name][status] += 1
                    summary[status] += 1
                    summary['total_resources'] += 1

                    summary['services'][service_name]['resources'].append({
                        'id': resource.get('resource_id'),
                        'name': resource.get('resource_name'),
                        'status': status,
                        'message': resource.get('message')
                    })

        return summary
