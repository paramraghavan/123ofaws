"""
Interactive failover - let user select which resources to failover.
User sees alerts, then manually chooses which resources to move to secondary region.
"""

from typing import List, Dict, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class InteractiveFailover:
    """Interactive resource selection and failover."""

    def __init__(self, failover_manager, daemon):
        """
        Initialize interactive failover.

        Args:
            failover_manager: FailoverManager instance
            daemon: MonitoringDaemon instance (for current resource state)
        """
        self.failover_manager = failover_manager
        self.daemon = daemon
        self.logger = logger

    def prompt_for_failover(self) -> bool:
        """
        Interactive prompt asking if user wants to failover.

        Returns:
            True if user wants to proceed with failover
        """
        print("\n" + "=" * 70)
        print("⚠️  PRIMARY REGION MONITORING ALERT")
        print("=" * 70)

        heartbeat = self.failover_manager.check_primary_heartbeat()

        print(f"\nPrimary Region: {self.failover_manager.primary_region}")
        print(f"Secondary Region: {self.failover_manager.secondary_region}")
        print(f"\nHeartbeat Status:")
        print(f"  Healthy: {heartbeat['healthy']}")
        print(f"  Age: {heartbeat['heartbeat_age_seconds']} seconds")
        print(f"  Last seen: {heartbeat['last_heartbeat']}")

        if heartbeat['is_primary_down']:
            print(f"\n🚨 PRIMARY REGION APPEARS TO BE DOWN!")
        else:
            print(f"\n⚠️  Primary region heartbeat is stale")

        response = input("\nDo you want to proceed with manual failover? (y/n): ").strip().lower()
        return response == 'y'

    def select_resources_to_failover(self) -> Dict[str, List[str]]:
        """
        Interactively ask user which resources to failover.

        Returns:
            Dictionary: {service_name: [resource_ids_to_failover]}
        """
        selected_resources = {}
        current_state = self.daemon.get_current_state()

        print("\n" + "=" * 70)
        print("SELECT RESOURCES TO FAILOVER")
        print("=" * 70)

        for service_name, service_data in current_state.items():
            if not isinstance(service_data, list) or not service_data:
                continue

            print(f"\n📦 {service_name.upper()} ({len(service_data)} resource(s))")
            print("-" * 70)

            service_selected = []

            for i, resource in enumerate(service_data, 1):
                resource_id = resource.get('resource_id', 'unknown')
                resource_name = resource.get('resource_name', resource_id)
                status = resource.get('status', 'unknown')
                message = resource.get('message', '')

                # Color code status
                status_icon = {
                    'healthy': '✓',
                    'degraded': '⚠️',
                    'unhealthy': '✗',
                    'unknown': '?'
                }.get(status, '?')

                print(f"\n  [{i}] {status_icon} {resource_name}")
                print(f"      ID: {resource_id}")
                print(f"      Status: {status}")
                print(f"      Message: {message}")

                response = input(f"      Failover this resource? (y/n): ").strip().lower()

                if response == 'y':
                    service_selected.append(resource_id)
                    print(f"      ✓ Selected for failover")

            if service_selected:
                selected_resources[service_name] = service_selected

        return selected_resources

    def confirm_failover(self, selected_resources: Dict[str, List[str]]) -> bool:
        """
        Show summary and ask for final confirmation.

        Args:
            selected_resources: Resources selected for failover

        Returns:
            True if user confirms final failover
        """
        print("\n" + "=" * 70)
        print("FAILOVER SUMMARY")
        print("=" * 70)

        total_resources = sum(len(r) for r in selected_resources.values())
        print(f"\nTotal resources to failover: {total_resources}")

        for service_name, resources in selected_resources.items():
            print(f"\n  {service_name.upper()}:")
            for resource_id in resources:
                print(f"    - {resource_id}")

        print(f"\nTarget Region: {self.failover_manager.secondary_region}")
        print("\n⚠️  WARNING: This will move resources to the secondary region.")
        print("    DNS/Routing will be updated to point to secondary region.")
        print("    Once failover starts, it cannot be easily reversed.")

        response = input("\nFinal confirmation - proceed with failover? (yes/no): ").strip().lower()
        return response == 'yes'

    def execute_failover(self, selected_resources: Dict[str, List[str]]) -> Dict[str, Any]:
        """
        Execute failover for selected resources.

        Args:
            selected_resources: Resources to failover

        Returns:
            Failover execution result
        """
        print("\n" + "=" * 70)
        print("EXECUTING FAILOVER")
        print("=" * 70)

        result = {
            'status': 'in_progress',
            'timestamp': __import__('datetime').datetime.utcnow().isoformat(),
            'primary_region': self.failover_manager.primary_region,
            'target_region': self.failover_manager.secondary_region,
            'selected_resources': selected_resources,
            'execution_results': {},
            'errors': []
        }

        for service_name, resource_ids in selected_resources.items():
            print(f"\n🔄 Failing over {service_name.upper()} ({len(resource_ids)} resource(s))...")

            service_results = []
            for resource_id in resource_ids:
                try:
                    print(f"   → {resource_id}...", end=" ", flush=True)

                    failover_result = self.failover_manager.execute_failover(
                        service=service_name,
                        resource_id=resource_id,
                        target_region=self.failover_manager.secondary_region
                    )

                    service_results.append({
                        'resource_id': resource_id,
                        'status': 'success' if failover_result.get('success') else 'failed',
                        'message': failover_result.get('message', 'OK')
                    })

                    print("✓")

                except Exception as e:
                    error_msg = f"Error failing over {resource_id}: {e}"
                    self.logger.error(error_msg)
                    service_results.append({
                        'resource_id': resource_id,
                        'status': 'error',
                        'message': str(e)
                    })
                    result['errors'].append(error_msg)
                    print("✗")

            result['execution_results'][service_name] = service_results

        result['status'] = 'completed' if not result['errors'] else 'completed_with_errors'

        return result

    def print_failover_result(self, result: Dict[str, Any]) -> None:
        """Print failover execution results."""
        print("\n" + "=" * 70)
        print("FAILOVER RESULTS")
        print("=" * 70)

        print(f"\nStatus: {result['status']}")
        print(f"Primary Region: {result['primary_region']}")
        print(f"Target Region: {result['target_region']}")

        print("\nExecution Results:")
        for service_name, service_results in result['execution_results'].items():
            print(f"\n  {service_name.upper()}:")
            for res in service_results:
                status_icon = "✓" if res['status'] == 'success' else "✗"
                print(f"    {status_icon} {res['resource_id']}: {res['message']}")

        if result['errors']:
            print(f"\nErrors ({len(result['errors'])}):")
            for error in result['errors']:
                print(f"  ✗ {error}")

        print("\n" + "=" * 70)
        print("NEXT STEPS:")
        print("-" * 70)
        print("1. Verify failover resources are running in secondary region")
        print("2. Test application functionality")
        print("3. Update documentation/runbooks")
        print("4. Investigate primary region failure")
        print("5. Plan failback when primary recovers")
        print("=" * 70 + "\n")

    def run_interactive_failover(self) -> bool:
        """
        Run complete interactive failover workflow.

        Returns:
            True if failover completed successfully
        """
        # Step 1: Alert and ask to proceed
        if not self.prompt_for_failover():
            print("\n✓ Failover cancelled by user")
            return False

        # Step 2: Select resources
        selected_resources = self.select_resources_to_failover()

        if not selected_resources:
            print("\n⚠️  No resources selected for failover")
            return False

        print(f"\n✓ {sum(len(r) for r in selected_resources.values())} resource(s) selected")

        # Step 3: Confirm
        if not self.confirm_failover(selected_resources):
            print("\n✗ Failover cancelled by user")
            return False

        # Step 4: Execute
        result = self.execute_failover(selected_resources)

        # Step 5: Display results
        self.print_failover_result(result)

        return result['status'] in ['completed', 'completed_with_errors']
