# Direct Email Alerting Setup

The monitoring system now sends alerts **directly via email** without requiring SNS.

## Quick Start

### Gmail (Easiest)

1. **Create Gmail App Password:**
   - Go to https://myaccount.google.com/apppasswords
   - Select "Mail" and "Windows Computer" (or any device)
   - Generate app password (16 characters)

2. **Configure monitoring system:**
```yaml
# config/config.yaml
alerts:
  email_enabled: true
  email: your-email@gmail.com,ops-team@example.com
  email_from: aws-monitoring@company.com

  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_user: your-email@gmail.com
  smtp_password: xxxx xxxx xxxx xxxx  # 16-char app password
  smtp_tls: true
```

3. **Run the system:**
```bash
python src/main.py --config config/config.yaml --prefix uat-
```

**That's it!** Alerts will be sent directly to your email.

---

## Configuration Options

### Option 1: Gmail (Free, Easy)

```yaml
alerts:
  email_enabled: true
  email: your-email@gmail.com
  email_from: aws-monitoring@gmail.com

  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_user: your-email@gmail.com
  smtp_password: xxxx xxxx xxxx xxxx  # App password
  smtp_tls: true
```

**Steps:**
1. Go to https://myaccount.google.com/apppasswords
2. Enable 2FA on your Google account if not already done
3. Generate app password for "Mail" and "Windows Computer"
4. Copy the 16-character password into config
5. Done!

### Option 2: Office 365 / Outlook

```yaml
alerts:
  email_enabled: true
  email: ops-team@company.com
  email_from: monitoring@company.com

  smtp_host: smtp.office365.com
  smtp_port: 587
  smtp_user: your-email@company.com
  smtp_password: your-office365-password
  smtp_tls: true
```

**Note:** Use your Office 365 password directly (no app password needed).

### Option 3: SendGrid

```yaml
alerts:
  email_enabled: true
  email: ops-team@company.com
  email_from: monitoring@company.com

  smtp_host: smtp.sendgrid.net
  smtp_port: 587
  smtp_user: apikey  # Always "apikey"
  smtp_password: SG.xxxxxxxxxxxxx  # Your SendGrid API key
  smtp_tls: true
```

**Steps:**
1. Create SendGrid account
2. Generate API key
3. Use "apikey" as username, API key as password

### Option 4: Custom Mail Server

```yaml
alerts:
  email_enabled: true
  email: ops-team@company.com
  email_from: monitoring@company.com

  smtp_host: mail.company.com  # Your company mail server
  smtp_port: 587               # Or 465 for SSL
  smtp_user: username
  smtp_password: password
  smtp_tls: true               # Or false for SSL
```

### Option 5: AWS SES (Native AWS)

```yaml
alerts:
  email_enabled: true
  email: ops-team@company.com
  email_from: monitoring@company.com
  # Don't set smtp_* - SES will be auto-detected
```

**Setup:**
1. Verify email addresses in AWS SES
2. System automatically uses AWS SES if SMTP not configured
3. Uses AWS credentials from default profile

**Verify emails:**
```bash
# Verify sender email
aws ses verify-email-identity --email-address monitoring@company.com

# Verify recipient (if in sandbox mode)
aws ses verify-email-identity --email-address ops-team@company.com
```

---

## Configuration Details

### Core Settings

```yaml
alerts:
  email_enabled: true              # Enable direct email alerts
  email: ops@example.com           # Recipient(s) - comma-separated
  email_from: monitoring@example.com # Sender email address
```

### SMTP Settings (For external mail servers)

```yaml
  smtp_host: smtp.gmail.com        # SMTP server hostname
  smtp_port: 587                   # 587=TLS, 465=SSL
  smtp_user: user@gmail.com        # SMTP username
  smtp_password: app-password      # SMTP password or app-password
  smtp_tls: true                   # Use TLS (true) or SSL (false)
```

### Multiple Recipients

Send alerts to multiple people:

```yaml
alerts:
  email: ops-team@example.com, manager@example.com, slack-integration@example.com
  # Comma-separated email addresses
```

### Environment Variables (Secure)

Instead of storing passwords in config file:

```bash
# Set in environment
export ALERTING_SMTP_PASSWORD="your-app-password"
```

Then in config:
```yaml
alerts:
  email_enabled: true
  email: ops@example.com
  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_user: your-email@gmail.com
  smtp_password: ${ALERTING_SMTP_PASSWORD}  # Or use env var directly
```

---

## Alert Examples

### Lambda Error Alert

```
From: aws-monitoring@company.com
To: ops-team@example.com
Subject: ✗ [LAMBDA] my-function is unhealthy

AWS Monitoring Alert

Service: LAMBDA
Resource: my-function
Resource ID: arn:aws:lambda:us-east-1:123456789:function:my-function
Status: UNHEALTHY
Message: Error rate 12.5% exceeds threshold 5%

Timestamp: 2026-04-03T15:30:45.123456
Region: us-east-1

Metrics:
  error_rate: 12.5
  errors: 5
  invocations: 40
  duration: 1234.5

Please investigate and take appropriate action.

---
AWS Monitoring System
Email Alerter
```

### Snowflake Down Alert

```
From: aws-monitoring@company.com
To: ops-team@example.com
Subject: ✗ [SNOWFLAKE] COMPUTE_WH is unhealthy

AWS Monitoring Alert

Service: SNOWFLAKE
Resource: COMPUTE_WH
Resource ID: COMPUTE_WH
Status: UNHEALTHY
Message: Cannot connect to Snowflake

Timestamp: 2026-04-03T15:35:22.654321
Region: us-east-1

Metrics:
  (no metrics available)

Please investigate and take appropriate action.

---
AWS Monitoring System
Email Alerter
```

### Control-M Job Failed Alert

```
From: aws-monitoring@company.com
To: ops-team@example.com
Subject: ✗ [CONTROLM] DAILY_BATCH is unhealthy

AWS Monitoring Alert

Service: CONTROLM
Resource: DAILY_BATCH
Resource ID: DAILY_BATCH
Status: UNHEALTHY
Message: Job DAILY_BATCH Failed

Timestamp: 2026-04-03T15:40:10.987654
Region: us-east-1

Metrics:
  status: Failed
  type: job

Please investigate and take appropriate action.

---
AWS Monitoring System
Email Alerter
```

---

## Testing Email Configuration

### Test Email Delivery

```bash
# Send test email to verify configuration
python -c "
import sys
sys.path.insert(0, 'src')

from config_loader import ConfigLoader
from alerts.email_alerter import EmailAlerter

config = ConfigLoader.load('config/config.yaml')
alerter = EmailAlerter(
    to_email=config.alerts.email,
    from_email=config.alerts.email_from,
    smtp_host=config.alerts.smtp_host,
    smtp_port=config.alerts.smtp_port,
    smtp_user=config.alerts.smtp_user,
    smtp_password=config.alerts.smtp_password,
    use_tls=config.alerts.smtp_tls
)

try:
    alerter.send_test('Testing email configuration')
    print('✓ Test email sent successfully')
except Exception as e:
    print(f'✗ Error sending test email: {e}')
"
```

### Common Test Scenarios

```bash
# Test with Gmail
python src/main.py --config config/config.yaml --prefix test- &
# Let it run, should send email within check interval

# Watch logs
tail -f /tmp/monitoring.log | grep -i email
```

---

## Troubleshooting

### "SMTP authentication failed"

```
Error: (401, b'4.7.8 Please log in with your web browser...')
```

**Solution for Gmail:**
- You must use **App Password**, not your regular Gmail password
- Generate at https://myaccount.google.com/apppasswords
- Two-factor authentication must be enabled

### "Connection refused"

```
Error: [Errno 111] Connection refused
```

**Check:**
1. SMTP hostname is correct
2. Port is correct (587 for TLS, 465 for SSL)
3. Firewall allows outgoing connections on that port

### "Relay access denied"

```
Error: 550 5.7.1 Relay access denied
```

**Solution:**
- Username/password authentication may be required
- Verify `smtp_user` and `smtp_password` in config
- Check with mail server administrator

### Email not received

**Check:**
1. Recipient email address is correct
2. No typos in `email:` field
3. Check spam/junk folder
4. Verify sender email is whitelisted
5. Check logs for delivery errors

### "Certificate verification failed"

```
Error: SSL: CERTIFICATE_VERIFY_FAILED
```

**Solution:**
- For self-signed certificates, may need to configure Python SSL
- For production, ensure valid SSL certificates
- Check `smtp_tls` setting (true for TLS, false for SSL)

---

## Security Best Practices

### 1. Never Store Passwords in Git

❌ Bad:
```yaml
alerts:
  smtp_password: my-actual-password  # Don't commit this!
```

✅ Good - Use environment variables:
```bash
export ALERT_SMTP_PASSWORD="my-password"
```

✅ Better - Use app-specific passwords:
```bash
# Gmail
export ALERT_SMTP_PASSWORD="xxxx xxxx xxxx xxxx"  # 16-char app password
```

### 2. Use TLS/SSL

```yaml
alerts:
  smtp_tls: true           # Use TLS (port 587)
  # OR
  smtp_port: 465           # SSL (explicit)
  smtp_tls: false
```

### 3. Rotate Credentials

```bash
# Update password regularly
# For Gmail: Generate new app password at myaccount.google.com
# Delete old app passwords

# Update environment variable
export ALERT_SMTP_PASSWORD="new-password"

# Restart monitoring system
python src/main.py --config config/config.yaml --prefix uat-
```

### 4. Restrict Recipient Emails

```yaml
# Only internal monitoring team
alerts:
  email: ops-team@company.com, security@company.com
  # Don't send to external or untrusted addresses
```

### 5. Use AWS SES for AWS-only Deployments

```yaml
alerts:
  email_enabled: true
  email: ops@company.com
  email_from: monitoring@company.com
  # Don't set smtp_* - uses AWS credentials
```

**Benefits:**
- Uses IAM credentials (no plain-text passwords)
- Integrated with AWS (no external dependencies)
- Can use SES sending limits and rules

---

## Complete Example Configs

### Small Team (Gmail)

```yaml
# config/team-monitoring.yaml
aws:
  primary_region: us-east-1

monitoring:
  check_interval: 300

cloudformation:
  stack_prefixes:
    - uat-top
    - uat-bot

services:
  lambda:
    enabled: true
  ec2:
    enabled: true
  s3:
    enabled: true

alerts:
  email_enabled: true
  email: ops-team@company.com
  email_from: aws-monitoring@company.com

  smtp_host: smtp.gmail.com
  smtp_port: 587
  smtp_user: monitoring@gmail.com
  smtp_password: xxxx xxxx xxxx xxxx
  smtp_tls: true
```

### Enterprise (Office 365 + Multiple Recipients)

```yaml
# config/enterprise-monitoring.yaml
aws:
  primary_region: us-east-1
  profile: production

monitoring:
  check_interval: 300

cloudformation:
  stack_prefixes:
    - prod-us-east
    - prod-us-west

services:
  # All 13 AWS services + 2 external
  lambda:
    enabled: true
  # ... other services ...

alerts:
  email_enabled: true
  email: ops-team@company.com, security@company.com, exec@company.com
  email_from: monitoring@company.com

  smtp_host: smtp.office365.com
  smtp_port: 587
  smtp_user: monitoring@company.com
  smtp_password: ${OFFICE365_PASSWORD}
  smtp_tls: true
```

### AWS-Native (SES)

```yaml
# config/aws-native-monitoring.yaml
aws:
  primary_region: us-east-1
  profile: production

alerts:
  email_enabled: true
  email: ops-team@company.com
  email_from: monitoring@company.com
  # No SMTP settings - uses AWS SES
```

---

## Next Steps

1. ✅ Configure email settings in `config/config.yaml`
2. ✅ Test with `python -c "...alerter.send_test(...)"`
3. ✅ Run monitoring system
4. ✅ Verify alerts are received
5. ✅ Later: Add PagerDuty integration (if needed)

**Email alerting is live and ready!** 🚀
