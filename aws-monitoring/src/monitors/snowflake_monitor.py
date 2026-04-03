"""Monitor Snowflake service and database health."""

from typing import List, Dict, Any, Optional
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from utils.logger import get_logger
import os

logger = get_logger(__name__)


class SnowflakeMonitor(BaseMonitor):
    """Monitor Snowflake database and warehouse health."""

    @property
    def service_name(self) -> str:
        return 'snowflake'

    def __init__(self, session_manager, config: Dict[str, Any]):
        """
        Initialize Snowflake monitor.

        Args:
            session_manager: AWSSessionManager instance
            config: Service-specific configuration including Snowflake credentials
        """
        super().__init__(session_manager, config)
        self.logger = logger

        # Snowflake connection details from config
        self.snowflake_account = config.get('snowflake_account')
        self.snowflake_user = config.get('snowflake_user', os.getenv('SNOWFLAKE_USER'))
        self.snowflake_password = config.get('snowflake_password', os.getenv('SNOWFLAKE_PASSWORD'))
        self.snowflake_warehouse = config.get('snowflake_warehouse', 'COMPUTE_WH')
        self.snowflake_database = config.get('snowflake_database')

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """
        Check health of Snowflake databases and warehouses.

        Args:
            resources: List of warehouse names or database names

        Returns:
            List of ResourceHealth objects
        """
        health_results = []

        for resource in resources:
            try:
                health = self._check_snowflake_resource(resource)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking Snowflake {resource}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=resource,
                        resource_name=resource,
                        resource_type='Snowflake',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_snowflake_resource(self, resource_name: str) -> ResourceHealth:
        """Check health of a Snowflake resource (warehouse or database)."""
        try:
            # Import snowflake connector
            try:
                import snowflake.connector
            except ImportError:
                return ResourceHealth(
                    resource_id=resource_name,
                    resource_name=resource_name,
                    resource_type='Snowflake',
                    status=HealthStatus.UNKNOWN,
                    message="snowflake-connector-python not installed. "
                           "Install with: pip install snowflake-connector-python",
                    region=self.region
                )

            if not self.snowflake_account:
                return ResourceHealth(
                    resource_id=resource_name,
                    resource_name=resource_name,
                    resource_type='Snowflake',
                    status=HealthStatus.UNKNOWN,
                    message="Snowflake account not configured. "
                           "Set snowflake_account in config or SNOWFLAKE_ACCOUNT env var",
                    region=self.region
                )

            # Connect to Snowflake
            try:
                ctx = snowflake.connector.connect(
                    user=self.snowflake_user,
                    password=self.snowflake_password,
                    account=self.snowflake_account,
                    warehouse=self.snowflake_warehouse,
                    database=self.snowflake_database
                )
            except Exception as e:
                return ResourceHealth(
                    resource_id=resource_name,
                    resource_name=resource_name,
                    resource_type='Snowflake',
                    status=HealthStatus.UNHEALTHY,
                    message=f"Failed to connect to Snowflake: {str(e)}",
                    region=self.region
                )

            try:
                # Check if resource is a warehouse
                cs = ctx.cursor()
                cs.execute(f"SHOW WAREHOUSES LIKE '{resource_name}'")
                warehouses = cs.fetchall()

                if warehouses:
                    warehouse = warehouses[0]
                    warehouse_name = warehouse[0]
                    warehouse_state = warehouse[4]  # State is at index 4

                    metrics = {
                        'warehouse': warehouse_name,
                        'state': warehouse_state,
                        'type': 'warehouse'
                    }

                    if warehouse_state != 'AVAILABLE':
                        return ResourceHealth(
                            resource_id=resource_name,
                            resource_name=resource_name,
                            resource_type='Snowflake',
                            status=HealthStatus.DEGRADED if warehouse_state == 'SUSPENDED' else HealthStatus.UNHEALTHY,
                            message=f"Warehouse state is {warehouse_state}",
                            metrics=metrics,
                            region=self.region
                        )

                    # Warehouse is healthy
                    return ResourceHealth(
                        resource_id=resource_name,
                        resource_name=resource_name,
                        resource_type='Snowflake',
                        status=HealthStatus.HEALTHY,
                        message=f"Warehouse {warehouse_name} is {warehouse_state}",
                        metrics=metrics,
                        region=self.region
                    )

                # Check if resource is a database
                cs.execute(f"SHOW DATABASES LIKE '{resource_name}'")
                databases = cs.fetchall()

                if databases:
                    database = databases[0]
                    database_name = database[0]

                    metrics = {
                        'database': database_name,
                        'type': 'database'
                    }

                    return ResourceHealth(
                        resource_id=resource_name,
                        resource_name=resource_name,
                        resource_type='Snowflake',
                        status=HealthStatus.HEALTHY,
                        message=f"Database {database_name} is accessible",
                        metrics=metrics,
                        region=self.region
                    )

                # Resource not found
                return ResourceHealth(
                    resource_id=resource_name,
                    resource_name=resource_name,
                    resource_type='Snowflake',
                    status=HealthStatus.UNHEALTHY,
                    message=f"Warehouse or database '{resource_name}' not found",
                    region=self.region
                )

            finally:
                ctx.close()

        except Exception as e:
            self.logger.error(f"Error checking Snowflake resource {resource_name}: {e}")
            return ResourceHealth(
                resource_id=resource_name,
                resource_name=resource_name,
                resource_type='Snowflake',
                status=HealthStatus.UNKNOWN,
                message=str(e),
                region=self.region
            )

    def _get_cloudwatch_namespace(self) -> str:
        return 'Snowflake'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'WarehouseName', 'Value': resource_id}]
