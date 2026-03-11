import boto3
import json
import os
from botocore.exceptions import ClientError

LOG_BUCKET = os.environ.get('LOG_BUCKET', '')
TEMPLATE_FILE = 'dashboard_template.html'


def lambda_handler(event, context):
    """Generate static dashboard from latest status"""
    try:
        if not LOG_BUCKET:
            return {
                'statusCode': 500,
                'body': json.dumps({'error': 'LOG_BUCKET not configured'})
            }

        # Read latest status
        status = read_status()

        # Generate HTML dashboard
        html = generate_html(status)

        # Upload dashboard to S3
        upload_dashboard(html)

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Dashboard generated successfully'})
        }

    except Exception as e:
        print(f"Error in generate_dashboard: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }


def read_status():
    """Read latest status from S3"""
    s3 = boto3.client('s3')

    try:
        response = s3.get_object(Bucket=LOG_BUCKET, Key='status/latest.json')
        status = json.loads(response['Body'].read().decode('utf-8'))
        return status
    except ClientError as e:
        print(f"Error reading status from S3: {str(e)}")
        # Return default status if file not found
        return {
            'timestamp': 'N/A',
            's3_buckets': [],
            'ec2_instances': [],
            'emr_clusters': [],
            'error': 'No status data available'
        }


def generate_html(status):
    """Generate HTML from status data"""
    try:
        # Read template from Lambda code directory
        with open(TEMPLATE_FILE, 'r') as f:
            template = f.read()
    except FileNotFoundError:
        print(f"Template file {TEMPLATE_FILE} not found, using inline template")
        template = get_default_template()

    # Escape JSON for JavaScript
    status_json = json.dumps(status, indent=2)

    # Replace placeholder with actual status data
    html = template.replace('{{STATUS_JSON}}', status_json)

    return html


def get_default_template():
    """Return default template if file not found"""
    return '''<!DOCTYPE html>
<html>
<head>
    <title>AWS Monitoring Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        h1 { color: #232f3e; border-bottom: 2px solid #ff9900; padding-bottom: 10px; }
        h2 { color: #232f3e; margin-top: 30px; }
        .timestamp { color: #666; font-size: 14px; margin: 10px 0; }
        .status-ok { color: #28a745; font-weight: bold; }
        .status-fail { color: #dc3545; font-weight: bold; }
        .status-unknown { color: #ffc107; font-weight: bold; }
        table { border-collapse: collapse; width: 100%; margin: 15px 0; }
        th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
        th { background-color: #232f3e; color: white; font-weight: bold; }
        tr:nth-child(even) { background-color: #f9f9f9; }
        tr:hover { background-color: #f0f0f0; }
        .no-data { color: #999; font-style: italic; padding: 20px; text-align: center; }
        .error { background-color: #f8d7da; color: #721c24; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .refresh-info { color: #666; font-size: 12px; margin-top: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>AWS Resource Monitoring Dashboard</h1>
        <div class="timestamp">Last Updated: <span id="timestamp">Loading...</span></div>

        <h2>S3 Buckets</h2>
        <table id="s3-table"></table>

        <h2>EC2 Instances</h2>
        <table id="ec2-table"></table>

        <h2>EMR Clusters</h2>
        <table id="emr-table"></table>

        <p class="refresh-info">Page auto-refreshes every 60 seconds. Last check: <span id="last-refresh"></span></p>
    </div>

    <script>
        const status = {{STATUS_JSON}};

        // Display timestamp
        document.getElementById('timestamp').textContent = status.timestamp || 'N/A';
        document.getElementById('last-refresh').textContent = new Date().toLocaleTimeString();

        // Render tables
        if (status.error) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'error';
            errorDiv.textContent = 'Error: ' + status.error;
            document.querySelector('.container').insertBefore(errorDiv, document.querySelector('h2'));
        } else {
            renderTable('s3-table', status.s3_buckets || [], ['name', 'status', 'region']);
            renderTable('ec2-table', status.ec2_instances || [], ['id', 'state', 'type', 'az']);
            renderTable('emr-table', status.emr_clusters || [], ['id', 'name', 'status']);
        }

        function renderTable(tableId, data, columns) {
            const table = document.getElementById(tableId);

            if (data.length === 0) {
                table.innerHTML = '<tr><td class="no-data" colspan="4">No resources found</td></tr>';
                return;
            }

            let html = '<tr>';
            columns.forEach(col => html += `<th>${col}</th>`);
            html += '</tr>';

            data.forEach(row => {
                html += '<tr>';
                columns.forEach(col => {
                    const value = row[col] || '-';
                    const statusValues = ['available', 'running', 'ok'];
                    const failureValues = ['failed', 'stopped', 'terminated', 'terminated_with_errors', 'stopping'];
                    let cssClass = 'status-unknown';

                    if (statusValues.includes(String(value).toLowerCase())) {
                        cssClass = 'status-ok';
                    } else if (failureValues.includes(String(value).toLowerCase())) {
                        cssClass = 'status-fail';
                    }

                    html += `<td class="${cssClass}">${value}</td>`;
                });
                html += '</tr>';
            });

            table.innerHTML = html;
        }

        // Auto-refresh every 60 seconds
        setTimeout(() => location.reload(), 60000);
    </script>
</body>
</html>'''


def upload_dashboard(html):
    """Upload dashboard HTML to S3"""
    s3 = boto3.client('s3')

    try:
        s3.put_object(
            Bucket=LOG_BUCKET,
            Key='dashboard/index.html',
            Body=html.encode('utf-8'),
            ContentType='text/html'
        )
        print(f"Dashboard uploaded to s3://{LOG_BUCKET}/dashboard/index.html")
    except ClientError as e:
        print(f"Error uploading dashboard to S3: {str(e)}")
        raise
