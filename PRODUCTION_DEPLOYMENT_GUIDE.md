# PRODUCTION DEPLOYMENT GUIDE
# M-Pesa Payment Integration for Charlady Platform

## Table of Contents
1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Database Preparation](#database-preparation)
3. [M-Pesa Production Credentials](#mpesa-production-credentials)
4. [Environment Configuration](#environment-configuration)
5. [Celery Setup](#celery-setup)
6. [Deployment Steps](#deployment-steps)
7. [Post-Deployment Verification](#post-deployment-verification)
8. [Monitoring & Alerts](#monitoring--alerts)
9. [Rollback Procedures](#rollback-procedures)

---

## PRE-DEPLOYMENT CHECKLIST

### Code Review
- [ ] All code reviewed and tested in staging
- [ ] QA test suite (QA-001 to QA-027) completed and passed
- [ ] No uncommitted code changes
- [ ] Git history clean and deployable

### Testing
- [ ] Unit tests passing: `python manage.py test`
- [ ] Integration tests passing: `python test_integration.py`
- [ ] Manual QA scenarios completed (see QA_TEST_SCENARIOS.py)
- [ ] Tested with both sandbox and production M-Pesa credentials

### Infrastructure
- [ ] Database backed up
- [ ] Redis running and accessible
- [ ] Celery worker configured and tested
- [ ] Django DEBUG = False in production settings
- [ ] ALLOWED_HOSTS configured correctly

### Security
- [ ] CSRF middleware enabled
- [ ] HTTPS enforced
- [ ] Secret key rotated
- [ ] M-Pesa IP whitelist configured
- [ ] Database credentials secured in .env

---

## DATABASE PREPARATION

### Backup Current Database
```bash
# PostgreSQL backup
pg_dump charlady_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Or using Django
python manage.py dumpdata > backup_$(date +%Y%m%d_%H%M%S).json
```

### Deploy New Migrations
```bash
# Run all pending migrations
python manage.py migrate --no-input

# Check migration status
python manage.py showmigrations
```

### Verify Schema
```bash
# Check new tables exist
python manage.py dbshell
\dt payments_usersubscription;
\dt payments_monthlycontribution;
\d accounts_customuser;  # Check for new columns
\d payments_payment;  # Check for new columns
```

---

## M-PESA PRODUCTION CREDENTIALS

### Get Credentials from Daraja
1. Visit: https://www.pesapal.com/
2. Switch from Sandbox to Production
3. Retrieve:
   - Consumer Key
   - Consumer Secret
   - Can be obtained from M-Pesa portal for B2C/STK scenarios

### Update Environment Variables
Create `.env` file in project root:

```bash
# M-PESA PRODUCTION CONFIGURATION
MPESA_CONSUMER_KEY=your_production_consumer_key_here
MPESA_CONSUMER_SECRET=your_production_consumer_secret_here
MPESA_PASSKEY=your_production_passkey_here
MPESA_SHORT_CODE=your_production_shortcode_here
MPESA_ENVIRONMENT=production
MPESA_CALLBACK_URL=https://charlady.co.ke/payments/mpesa-callback/
PAYMENT_TIMEOUT_MINUTES=5

# SECURITY
DEBUG=False
SECRET_KEY=your_new_secret_key_here
ALLOWED_HOSTS=charlady.co.ke,www.charlady.co.ke

# DATABASE
DATABASE_URL=postgresql://user:password@host:port/charlady_db

# EMAIL (for reminders)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_password

# REDIS (for Celery)
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Verify Credentials
```bash
python manage.py shell
from payments.mpesa_service import get_mpesa_client
client = get_mpesa_client()
print(f"Environment: {client.environment}")  # Should print: production
print(f"Short Code: {client.short_code}")    # Should print: your production short code
```

---

## ENVIRONMENT CONFIGURATION

### Production Settings
Update `housekeeper_connect/settings.py`:

```python
# DEBUG OFF
DEBUG = False

# ALLOWED HOSTS
ALLOWED_HOSTS = ['charlady.co.ke', 'www.charlady.co.ke']

# HTTPS
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_SECURITY_POLICY = {...}

# M-PESA CALLBACK URL
MPESA_CALLBACK_URL = 'https://charlady.co.ke/payments/mpesa-callback/'

# LOGGING (for monitoring)
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'WARNING',
            'class': 'logging.FileHandler',
            'filename': '/var/log/charlady/payments.log',
            'formatter': 'verbose',
        },
        'sentry': {
            'level': 'ERROR',
            'class': 'raven.contrib.django.raven_compat.DjangoClient',
        },
    },
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'root': {
        'handlers': ['file', 'sentry'],
        'level': 'INFO',
    },
}
```

---

## CELERY SETUP

### Install Celery & Redis
```bash
pip install celery redis
```

### Start Celery Worker
```bash
# In background
celery -A housekeeper_connect worker --loglevel=info &

# Or with systemd service
sudo systemctl start celery_worker
sudo systemctl enable celery_worker
```

### Start Celery Beat
```bash
# In background
celery -A housekeeper_connect beat --loglevel=info &

# Or with systemd service
sudo systemctl start celery_beat
sudo systemctl enable celery_beat
```

### Verify Tasks Running
```bash
# Check Celery can reach Redis
python manage.py shell
from celery import current_app
current_app.connection().connect()

# Test task
from payments.tasks import calculate_monthly_contributions
calculate_monthly_contributions.delay()  # Should show as pending
```

---

## DEPLOYMENT STEPS

### 1. Database Migration
```bash
# Apply migrations
python manage.py migrate --no-input

# Create superuser if needed
python manage.py createsuperuser --no-input \
  --username admin \
  --email admin@charlady.co.ke
```

### 2. Load Production Data
```bash
# If migrating from another system
python manage.py loaddata backup.json

# Or start fresh
python manage.py shell <<'EOF'
from payments.models import PaymentPlan
PaymentPlan.objects.get_or_create(
    plan_type='verification',
    target_group='worker',
    defaults={'name': 'Verification Badge', 'price': 250, 'duration_days': 365}
)
EOF
```

### 3. Collect Static Files
```bash
python manage.py collectstatic --no-input
```

### 4. Start Services
```bash
# Django application
gunicorn housekeeper_connect.wsgi --bind 0.0.0.0:8000

# Or use deployment platform (Heroku, Render, etc.)
git push heroku main
```

---

## POST-DEPLOYMENT VERIFICATION

### Run Test Suite
```bash
# Integration tests
python test_integration.py

# Should see:
# ============================================================
# ALL TESTS PASSED ✓
# ============================================================
```

### Verify M-Pesa Connectivity
```bash
python manage.py shell
from payments.mpesa_service import get_mpesa_client
client = get_mpesa_client()

# Test authentication
try:
    token = client.authenticate()
    print(f"✓ M-Pesa authenticated: {token[:20]}...")
except Exception as e:
    print(f"✗ Authentication failed: {e}")
```

### Test Payment Flow (Small Amount)
1. Login as worker: `test_worker@charlady.co.ke`
2. Navigate: `/payments/membership/checkout/`
3. Test amount: 1 KES (or whatever minimum for testing)
4. Complete M-Pesa payment
5. Verify:
   - [ ] Badge granted: `user.is_paid_verified = True`
   - [ ] Payment saved: `Payment.mpesa_transaction_id` populated
   - [ ] Success page shows badge confirmation

### Check Celery Tasks
```bash
# List active tasks
celery -A housekeeper_connect inspect active

# Check scheduled tasks
celery -A housekeeper_connect inspect scheduled
```

### Monitor Logs
```bash
# Watch real-time logs
tail -f /var/log/charlady/payments.log

# Check for errors
grep ERROR /var/log/charlady/payments.log | tail -20
```

---

## MONITORING & ALERTS

### Key Metrics to Monitor

1. **Payment Success Rate**
   ```
   Query: Payment.objects.filter(status='completed').count() / Payment.objects.count()
   Alert if < 95% for 1 hour
   ```

2. **M-Pesa Callback Latency**
   ```
   Query: (Payment.payment_verified_at - Payment.stk_initiated_at).seconds
   Alert if > 60 seconds (avg)
   ```

3. **Failed Payments**
   ```
   Query: Payment.objects.filter(status='failed').count()
   Alert if > 10 in 1 hour
   ```

4. **Celery Task Health**
   ```
   Query: celery inspect active_tasks
   Alert if tasks stuck in queue > 5 minutes
   ```

### Setup Sentry for Error Tracking
```python
# In settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your_sentry_dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False
)
```

### Setup DataDog Monitoring
```bash
pip install datadog
# Configure in settings.py
```

### Log Analysis
```bash
# Count failed payments today
grep "failed" /var/log/charlady/payments.log | wc -l

# Check callback processing
grep "callback received" /var/log/charlady/payments.log | wc -l

# Monitor M-Pesa errors
grep "M-Pesa" /var/log/charlady/payments.log | grep -i error
```

---

## ROLLBACK PROCEDURES

### Emergency Rollback (Last 15 Minutes)
```bash
# Stop current deployment
docker stop charlady_app

# Restore previous code
git checkout HEAD~1

# Restore database if needed
psql charlady_db < backup_previous.sql

# Restart with previous version
docker start charlady_app
```

### Database Rollback (if migration fails)
```bash
# Revert last migration
python manage.py migrate payments 0005  # Go back to migration 0005

# Or restore from backup
py manage.py flush --no-input
python manage.py loaddata backup_previous.json
```

### M-Pesa Credential Rollback
```bash
# Revert to sandbox credentials
export MPESA_ENVIRONMENT=sandbox
export MPESA_CONSUMER_KEY=sandbox_key
export MPESA_CONSUMER_SECRET=sandbox_secret

# Restart services
sudo systemctl restart charlady_app
```

---

## SUCCESS CRITERIA

- [ ] 100% integration tests passing
- [ ] 0 critical logs in first hour
- [ ] First live payment succeeds
- [ ] Admin dashboard accessible
- [ ] Celery tasks running on schedule
- [ ] No database errors
- [ ] M-Pesa callbacks processing correctly
- [ ] Worker badges granting automatically
- [ ] Monthly contributions calculated

---

## CONTACTS & SUPPORT

**M-Pesa Issues**: support@safaricom.co.ke
**Platform Issues**: devops@charlady.co.ke
**Payment Issues**: payments@charlady.co.ke

---

**Last Updated**: April 17, 2026
**Deployment Version**: 1.0.0
**Status**: ✓ PRODUCTION READY
