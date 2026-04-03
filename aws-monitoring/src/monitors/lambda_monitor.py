"""Monitor AWS Lambda functions."""

from typing import List, Dict, Any
from monitors.base_monitor import BaseMonitor, ResourceHealth, HealthStatus
from botocore.exceptions import ClientError


class LambdaMonitor(BaseMonitor):
    """Monitor Lambda function health and performance."""

    @property
    def service_name(self) -> str:
        return 'lambda'

    def check_health(self, resources: List[str]) -> List[ResourceHealth]:
        """
        Check health of Lambda functions.

        Args:
            resources: List of function names or ARNs

        Returns:
            List of ResourceHealth objects
        """
        health_results = []

        for resource in resources:
            try:
                function_name = self._extract_function_name(resource)
                health = self._check_function_health(function_name)
                health_results.append(health)
            except Exception as e:
                self.logger.error(f"Error checking Lambda {resource}: {e}")
                health_results.append(
                    ResourceHealth(
                        resource_id=resource,
                        resource_name=resource,
                        resource_type='Lambda',
                        status=HealthStatus.UNKNOWN,
                        message=str(e),
                        region=self.region
                    )
                )

        return health_results

    def _check_function_health(self, function_name: str) -> ResourceHealth:
        """Check health of a single Lambda function."""
        try:
            # Get function configuration
            response = self.client.get_function_configuration(
                FunctionName=function_name
            )

            # Check function state
            if response.get('State') != 'Active':
                return ResourceHealth(
                    resource_id=function_name,
                    resource_name=function_name,
                    resource_type='Lambda',
                    status=HealthStatus.UNHEALTHY,
                    message=f"Function state is {response.get('State')}",
                    region=self.region
                )

            # Get error rate from CloudWatch
            error_rate = self.get_cloudwatch_metrics(
                function_name,
                'Errors',
                'Sum',
                5
            )
            invocations = self.get_cloudwatch_metrics(
                function_name,
                'Invocations',
                'Sum',
                5
            )

            # Calculate error percentage
            error_percentage = 0
            if invocations and invocations > 0:
                error_percentage = (error_rate or 0) / invocations * 100

            # Check error threshold
            error_threshold = self._get_threshold('error_rate', 5.0)
            if error_percentage > error_threshold:
                return ResourceHealth(
                    resource_id=function_name,
                    resource_name=function_name,
                    resource_type='Lambda',
                    status=HealthStatus.DEGRADED,
                    message=f"Error rate {error_percentage:.2f}% exceeds threshold {error_threshold}%",
                    metrics={'error_rate': error_percentage},
                    region=self.region
                )

            # Check duration threshold
            duration = self.get_cloudwatch_metrics(
                function_name,
                'Duration',
                'Average',
                5
            )
            duration_threshold = self._get_threshold('duration', 55000)
            if duration and duration > duration_threshold:
                return ResourceHealth(
                    resource_id=function_name,
                    resource_name=function_name,
                    resource_type='Lambda',
                    status=HealthStatus.DEGRADED,
                    message=f"Average duration {duration:.0f}ms exceeds threshold {duration_threshold}ms",
                    metrics={'duration': duration},
                    region=self.region
                )

            # Function is healthy
            return ResourceHealth(
                resource_id=function_name,
                resource_name=function_name,
                resource_type='Lambda',
                status=HealthStatus.HEALTHY,
                message="Function is active and performing normally",
                metrics={
                    'invocations': invocations,
                    'errors': error_rate,
                    'error_rate_percent': error_percentage,
                    'duration': duration
                },
                region=self.region
            )

        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                status = HealthStatus.UNHEALTHY
                message = "Function not found"
            else:
                status = HealthStatus.UNKNOWN
                message = f"AWS error: {e}"
        except Exception as e:
            status = HealthStatus.UNKNOWN
            message = str(e)

        return ResourceHealth(
            resource_id=function_name,
            resource_name=function_name,
            resource_type='Lambda',
            status=status,
            message=message,
            region=self.region
        )

    def _extract_function_name(self, resource: str) -> str:
        """Extract function name from ARN or name."""
        if resource.startswith('arn:'):
            # Extract from ARN: arn:aws:lambda:region:account:function:name
            return resource.split(':')[-1]
        return resource

    def _get_cloudwatch_namespace(self) -> str:
        return 'AWS/Lambda'

    def _get_cloudwatch_dimensions(self, resource_id: str) -> List[Dict[str, str]]:
        function_name = self._extract_function_name(resource_id)
        return [{'Name': 'FunctionName', 'Value': function_name}]
