"""Monitor AWS KMS keys."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class KMSMonitor(BaseMonitor):
    """Monitor KMS key health and status."""

    @property
    def service_name(self) -> str:
        return 'kms'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """Check health of KMS keys."""
        health_results = []

        for key_id in resources:
            try:
                health = self._check_key_health(key_id)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking KMS {key_id}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=key_id,
                        resource_name=key_id,
                        resource_type='KMS',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_key_health(self, key_id: str) -> ResourceHealth:
        """Check health of a single KMS key."""
        try:
            # Get key metadata
            response = self.client.describe_key(KeyId=key_id)
            key_metadata = response.get('KeyMetadata', {})

            key_state = key_metadata.get('KeyState')
            key_arn = key_metadata.get('Arn')
            key_usage = key_metadata.get('KeyUsage')
            key_manager = key_metadata.get('KeyManager')

            metrics = {
                'state': key_state,
                'usage': key_usage,
                'manager': key_manager,
                'arn': key_arn
            }

            # Check key state
            if key_state == 'Disabled':
                return ResourceHealth(
                    resource_id=key_id,
                    resource_name=key_id,
                    resource_type='KMS',
                    status=HealthStatus.UNHEALTHY,
                    message="Key is disabled",
                    metrics=metrics,
                    region=self.region
                )

            if key_state == 'PendingDeletion':
                return ResourceHealth(
                    resource_id=key_id,
                    resource_name=key_id,
                    resource_type='KMS',
                    status=HealthStatus.DEGRADED,
                    message="Key is pending deletion",
                    metrics=metrics,
                    region=self.region
                )

            if key_state != 'Enabled':
                return ResourceHealth(
                    resource_id=key_id,
                    resource_name=key_id,
                    resource_type='KMS',
                    status=HealthStatus.UNKNOWN,
                    message=f"Key state is {key_state}",
                    metrics=metrics,
                    region=self.region
                )

            # Check key rotation
            try:
                rotation_response = self.client.get_key_rotation_status(KeyId=key_id)
                rotation_enabled = rotation_response.get('KeyRotationEnabled', False)
                metrics['rotation_enabled'] = rotation_enabled

                if not rotation_enabled and key_manager == 'CUSTOMER':
                    return ResourceHealth(
                        resource_id=key_id,
                        resource_name=key_id,
                        resource_type='KMS',
                        status=HealthStatus.DEGRADED,
                        message="Customer managed key has rotation disabled",
                        metrics=metrics,
                        region=self.region
                    )
            except Exception as e:
                self.logger.debug(f"Could not check key rotation: {e}")

            status = HealthStatus.HEALTHY
            message = f"Key is {key_state} and {key_usage}"

            return ResourceHealth(
                resource_id=key_id,
                resource_name=key_id,
                resource_type='KMS',
                status=status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'NotFoundException':
                status = HealthStatus.UNHEALTHY
                message = "Key does not exist"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=key_id,
            resource_name=key_id,
            resource_type='KMS',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/KMS'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [{'Name': 'KeyId', 'Value': resource_id}]
