"""
Base monitor class for all AWS service monitors.
Provides common functionality and abstract methods.
"""

from abc import ABC, abstractmethod
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from utils.logger import get_logger
from utils.aws_session import AWSSessionManager


class HealthStatus(Enum):
    """Health status indicators."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class ResourceHealth:
    """Health status of a single resource."""
    resource_id: str
    resource_name: str
    resource_type: str
    status: HealthStatus
    message: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    region: str = 'us-east-1'

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'resource_id': self.resource_id,
            'resource_name': self.resource_name,
            'resource_type': self.resource_type,
            'status': self.status.value,
            'message': self.message,
            'metrics': self.metrics,
            'timestamp': self.timestamp.isoformat(),
            'region': self.region
        }


class BaseMonitor(ABC):
    """Abstract base class for all service monitors."""

    def __init__(self, session_manager: AWSSessionManager, config: Dict[str, Any]):
        """
        Initialize monitor.

        Args:
            session_manager: AWSSessionManager instance
            config: Service-specific configuration
        """
        self.session_manager = session_manager
        self.config = config
        self.logger = get_logger(self.__class__.__name__)
        self.region = session_manager.region
        self.client = session_manager.get_client(self.service_name)
        self.cloudwatch = session_manager.get_client('cloudwatch')

    @property
    @abstractmethod
    def service_name(self) -> str:
        """
        AWS service name (e.g., 'lambda', 'ec2').
        Must be implemented by subclass.
        """
        pass

    @abstractmethod
    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """
        Check health of provided resources.

        Args:
            resources: List of resource IDs/ARNs to check

        Returns:
            List of ResourceHealth objects
        """
        pass

    def should_alert(self, health: ResourceHealth) -> bool:
        """
        Determine if resource health warrants an alert.

        Args:
            health: ResourceHealth object

        Returns:
            True if alert should be sent
        """
        return health.status in [HealthStatus.UNHEALTHY, HealthStatus.DEGRADED]

    def get_cloudwatch_metrics(
        self,
        resource_id: str,
        metric_name: str,
        statistic: str = 'Average',
        period_minutes: int = 5
    ) -> Optional[float]:
        """
        Get CloudWatch metric for a resource.

        Args:
            resource_id: Resource identifier
            metric_name: CloudWatch metric name
            statistic: Statistic to retrieve (Average, Sum, Maximum, etc.)
            period_minutes: Period in minutes to look back

        Returns:
            Metric value or None if not available
        """
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=period_minutes)

            response = self.cloudwatch.get_metric_statistics(
                Namespace=self._get_cloudwatch_namespace(),
                MetricName=metric_name,
                Dimensions=self._get_cloudwatch_dimensions(resource_id),
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=[statistic]
            )

            if response.get('Datapoints'):
                # Return latest datapoint
                return response['Datapoints'][-1].get(statistic)

        except Exception as e:
            self.logger.debug(f"Error getting metric {metric_name}: {e}")

        return None

    @abstractmethod
    def _get_cloudwatch_namespace(self) -> str:
        """
        Get CloudWatch namespace for this service.
        Example: 'AWS/Lambda'
        """
        pass

    @abstractmethod
    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        """
        Get CloudWatch dimensions for a resource.
        Example: [{'Name': 'FunctionName', 'Value': 'my-function'}]
        """
        pass

    def _check_threshold(
        self,
        value: float,
        threshold: float,
        operator: str = 'greater_than'
    ) -> bool:
        """
        Check if a value exceeds a threshold.

        Args:
            value: Actual value
            threshold: Threshold value
            operator: 'greater_than' or 'less_than'

        Returns:
            True if threshold is exceeded
        """
        if value is None:
            return False

        if operator == 'greater_than':
            return value > threshold
        elif operator == 'less_than':
            return value < threshold
        return False

    def _get_threshold(self, threshold_key: str, default: float = None) -> Optional[float]:
        """Get threshold value from config."""
        return self.config.get('thresholds', {}).get(threshold_key, default)

    def _log_health_check(self, resource_id: str, status: HealthStatus, message: str):
        """Log health check result."""
        level = 'warning' if status != HealthStatus.HEALTHY else 'debug'
        log_func = getattr(self.logger, level)
        log_func(f"{resource_id}: {status.value} - {message}")
