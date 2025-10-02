#!/usr/bin/env python3
"""
Example script showing how to monitor custom/non-AWS resources
alongside AWS resources using the Failover Manager
"""

from failover import AWSFailoverManager


def check_application_health(app_url):
    """Custom function to check application health"""
    import requests
    try:
        response = requests.get(f"{app_url}/api/health", timeout=5)
        data = response.json()
        # Check if all components are healthy
        return all(component['status'] == 'healthy' for component in data.get('components', []))
    except:
        return False


def check_disk_space(path='/data', min_free_gb=100):
    """Check if disk has minimum free space"""
    import shutil
    stat = shutil.disk_usage(path)
    free_gb = stat.free / (1024 ** 3)
    return free_gb >= min_free_gb


def main():
    print("=" * 60)
    print("Custom Resource Monitoring Example")
    print("=" * 60)

    # Initialize manager
    manager = AWSFailoverManager()

    # ============================================
    # PART 1: Monitor AWS Resources
    # ============================================
    print("\n[1] Checking AWS Resources...")

    instances = manager.detect_ec2_instances()
    clusters = manager.detect_emr_clusters()
    aws_status = manager.log_status(instances, clusters)

    print(f"✓ EC2 Instances: {aws_status['summary']['total_ec2']} "
          f"(Running: {aws_status['summary']['ec2_running']})")
    print(f"✓ EMR Clusters: {aws_status['summary']['total_emr']} "
          f"(Active: {aws_status['summary']['emr_active']})")

    # ============================================
    # PART 2: Monitor HTTP/HTTPS Endpoints
    # ============================================
    print("\n[2] Checking HTTP/HTTPS Endpoints...")

    custom_resources = []

    # Check web applications
    endpoints = [
        'https://api.example.com/health',
        'https://www.example.com',
        'https://admin.example.com/status',
        'http://internal-app.local:8080/health'
    ]

    for endpoint in endpoints:
        result = manager.check_http_endpoint(endpoint)
        custom_resources.append(result)
        status_icon = "✓" if result['status'] == 'HEALTHY' else "✗"
        print(f"  {status_icon} {endpoint}: {result['status']} "
              f"({result['response_time_ms']}ms)" if result[
            'response_time_ms'] else f"  {status_icon} {endpoint}: {result['status']}")

    # ============================================
    # PART 3: Monitor TCP Ports
    # ============================================
    print("\n[3] Checking TCP Ports...")

    # Check database and service ports
    tcp_checks = [
        ('mysql-primary.example.com', 3306, 'MySQL Primary'),
        ('mysql-replica.example.com', 3306, 'MySQL Replica'),
        ('postgres.example.com', 5432, 'PostgreSQL'),
        ('redis.example.com', 6379, 'Redis Cache'),
        ('mongodb.example.com', 27017, 'MongoDB'),
        ('app-server.local', 8080, 'Application Server')
    ]

    for host, port, name in tcp_checks:
        result = manager.check_tcp_port(host, port)
        custom_resources.append(result)
        status_icon = "✓" if result['status'] == 'OPEN' else "✗"
        print(f"  {status_icon} {name} ({host}:{port}): {result['status']}")

    # ============================================
    # PART 4: Monitor Database Connections
    # ============================================
    print("\n[4] Checking Database Connections...")

    # MySQL check
    # mysql_result = manager.check_database_connection(
    #     'mysql',
    #     host='mysql.example.com',
    #     user='monitor',
    #     password='your-password',
    #     database='production'
    # )
    # custom_resources.append(mysql_result)
    # print(f"  {'✓' if mysql_result['status'] == 'CONNECTED' else '✗'} "
    #       f"MySQL: {mysql_result['status']}")

    # PostgreSQL check
    # pg_result = manager.check_database_connection(
    #     'postgresql',
    #     host='postgres.example.com',
    #     user='monitor',
    #     password='your-password',
    #     database='app_db'
    # )
    # custom_resources.append(pg_result)
    # print(f"  {'✓' if pg_result['status'] == 'CONNECTED' else '✗'} "
    #       f"PostgreSQL: {pg_result['status']}")

    # Redis check
    # redis_result = manager.check_database_connection(
    #     'redis',
    #     host='redis.example.com',
    #     port=6379,
    #     password='redis-password'
    # )
    # custom_resources.append(redis_result)
    # print(f"  {'✓' if redis_result['status'] == 'CONNECTED' else '✗'} "
    #       f"Redis: {redis_result['status']}")

    print("  (Database connection checks commented out - configure as needed)")

    # ============================================
    # PART 5: Monitor Custom Resources
    # ============================================
    print("\n[5] Checking Custom Resources...")

    # Check application health with custom function
    # app_result = manager.check_custom_resource(
    #     'Application Health',
    #     check_application_health,
    #     app_url='https://app.example.com'
    # )
    # custom_resources.append(app_result)
    # print(f"  {'✓' if app_result['status'] == 'HEALTHY' else '✗'} "
    #       f"Application: {app_result['status']}")

    # Check disk space
    # disk_result = manager.check_custom_resource(
    #     'Disk Space /data',
    #     check_disk_space,
    #     path='/data',
    #     min_free_gb=100
    # )
    # custom_resources.append(disk_result)
    # print(f"  {'✓' if disk_result['status'] == 'HEALTHY' else '✗'} "
    #       f"Disk Space: {disk_result['status']}")

    print("  (Custom resource checks commented out - configure as needed)")

    # ============================================
    # PART 6: Log All Custom Resource Statuses
    # ============================================
    print("\n[6] Logging Custom Resource Status...")

    if custom_resources:
        custom_status = manager.log_custom_status(custom_resources, append_to_status=True)

        print(f"\nCustom Resources Summary:")
        print(f"  Total Resources: {custom_status['summary']['total_resources']}")
        print(f"  Healthy: {custom_status['summary']['healthy']}")
        print(f"  Unhealthy: {custom_status['summary']['unhealthy']}")

        # Show unhealthy resources
        unhealthy = [r for r in custom_resources
                     if r['status'] not in ['HEALTHY', 'CONNECTED', 'OPEN']]

        if unhealthy:
            print("\n⚠️  Unhealthy Resources:")
            for resource in unhealthy:
                resource_name = (resource.get('name') or
                                 resource.get('url') or
                                 f"{resource.get('host')}:{resource.get('port')}")
                print(f"  • {resource_name}")
                print(f"    Status: {resource['status']}")
                if resource.get('error'):
                    print(f"    Error: {resource['error']}")
        else:
            print("\n✓ All custom resources are healthy!")

    # ============================================
    # PART 7: Combined Health Report
    # ============================================
    print("\n" + "=" * 60)
    print("Overall Health Report")
    print("=" * 60)

    aws_healthy = (aws_status['summary']['ec2_running'] == aws_status['summary']['total_ec2'] and
                   aws_status['summary']['emr_active'] == aws_status['summary']['total_emr'])

    custom_healthy = (custom_status['summary']['unhealthy'] == 0) if custom_resources else True

    print(f"AWS Resources: {'✓ HEALTHY' if aws_healthy else '⚠ ISSUES DETECTED'}")
    if custom_resources:
        print(f"Custom Resources: {'✓ HEALTHY' if custom_healthy else '⚠ ISSUES DETECTED'}")

    overall_status = "✓ ALL SYSTEMS HEALTHY" if (aws_healthy and custom_healthy) else "⚠ ATTENTION REQUIRED"
    print(f"\nOverall Status: {overall_status}")
    print("=" * 60)


if __name__ == "__main__":
    main()