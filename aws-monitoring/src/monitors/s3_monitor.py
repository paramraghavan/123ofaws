"""Monitor AWS S3 buckets."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class S3Monitor(BaseMonitor):
    """Monitor S3 bucket health and configuration."""

    @property
    def service_name(self) -> str:
        return 's3'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """
        Check health of S3 buckets.

        Args:
            resources: List of bucket names

        Returns:
            List of ResourceHealth objects
        """
        health_results = []

        for bucket_name in resources:
            try:
                health = self._check_bucket_health(bucket_name)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking S3 {bucket_name}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=bucket_name,
                        resource_name=bucket_name,
                        resource_type='S3',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_bucket_health(self, bucket_name: str) -> ResourceHealth:
        """Check health of a single S3 bucket."""
        try:
            # Test bucket access
            response = self.client.head_bucket(Bucket=bucket_name)

            metrics = {'accessible': True}
            issues = []

            # Check versioning (if required)
            if self._get_threshold('versioning_enabled', False):
                versioning = self.client.get_bucket_versioning(Bucket=bucket_name)
                is_versioned = versioning.get('Status') == 'Enabled'
                metrics['versioning_enabled'] = is_versioned
                if not is_versioned:
                    issues.append("Versioning is not enabled")

            # Check encryption (if required)
            if self._get_threshold('encryption_enabled', False):
                try:
                    encryption = self.client.get_bucket_encryption(Bucket=bucket_name)
                    is_encrypted = bool(encryption.get('ServerSideEncryptionConfiguration'))
                    metrics['encryption_enabled'] = is_encrypted
                    if not is_encrypted:
                        issues.append("Encryption is not enabled")
                except ClientError as e:
                    if e.response['Error']['Code'] == 'ServerSideEncryptionConfigurationNotFoundError':
                        metrics['encryption_enabled'] = False
                        issues.append("Encryption is not enabled")
                    else:
                        raise

            # Check public access block (recommended)
            try:
                public_access = self.client.get_public_access_block(Bucket=bucket_name)
                block_config = public_access.get('PublicAccessBlockConfiguration', {})
                is_blocked = all(block_config.values())
                metrics['public_access_blocked'] = is_blocked
                if not is_blocked:
                    issues.append("Public access is not fully blocked")
            except ClientError:
                metrics['public_access_blocked'] = False

            # Determine status
            if issues:
                status = HealthStatus.DEGRADED
                message = "; ".join(issues)
            else:
                status = HealthStatus.HEALTHY
                message = "Bucket is accessible and properly configured"

            return ResourceHealth(
                resource_id=bucket_name,
                resource_name=bucket_name,
                resource_type='S3',
                status=status,
                message=message,
                metrics=metrics,
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchBucket':
                status = HealthStatus.UNHEALTHY
                message = "Bucket does not exist"
            elif e.response['Error']['Code'] == 'Forbidden':
                status = HealthStatus.UNHEALTHY
                message = "Access denied to bucket"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=bucket_name,
            resource_name=bucket_name,
            resource_type='S3',
            status=status,
            message=message,
            region=self.region
        )

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/S3'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        return [
            {'Name': 'BucketName', 'Value': resource_id},
            {'Name': 'StorageType', 'Value': 'StandardStorage'}
        ]
