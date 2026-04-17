# MONITORING AND DEBUGGING GUIDE
# M-Pesa Payment Integration - Production Operations

## Quick Diagnostics

### 1. Payment Status Health Check
```bash
python manage.py shell <<'EOF'
from payments.models import Payment
from django.utils import timezone
from datetime import timedelta

# Check payment volumes
today = timezone.now().date()
today_payments = Payment.objects.filter(stk_initiated_at__date=today)

print(f"📊 PAYMENT STATS (Today: {today})")
print(f"Total initiated: {today_payments.count()}")
print(f"Completed: {today_payments.filter(status='completed').count()}")
print(f"Failed: {today_payments.filter(status='failed').count()}")
print(f"Pending: {today_payments.filter(status='pending').count()}")

# Calculate success rate
completed = today_payments.filter(status='completed').count()
total = today_payments.count()
if total > 0:
    success_rate = (completed / total) * 100
    print(f"Success Rate: {success_rate:.1f}%")
    
    if success_rate < 95:
        print("⚠️  WARNING: Success rate below 95%!")

# Check for timeout issues
old_pending = today_payments.filter(
    status='pending',
    stk_initiated_at__lt=timezone.now() - timedelta(minutes=5)
)
if old_pending.exists():
    print(f"⚠️  {old_pending.count()} payments stuck in pending for >5 mins")

EOF
```

### 2. Celery Task Health Check
```bash
# Check active tasks
celery -A housekeeper_connect inspect active

# Check scheduled tasks
celery -A housekeeper_connect inspect scheduled

# Check registered tasks
celery -A housekeeper_connect inspect registered

# Example output:
# [2026-04-17 14:00:00] Active tasks:[]
# [2026-04-17 09:00] Scheduled: calculate-monthly-contributions completed
```

### 3. M-Pesa Connection Verification
```bash
python manage.py shell <<'EOF'
from payments.mpesa_service import get_mpesa_client
import datetime

print("🔌 M-PESA CONNECTION CHECK")
print("=" * 50)

try:
    client = get_mpesa_client()
    print(f"✓ Client initialized")
    print(f"  Environment: {client.environment}")
    print(f"  Short Code: {client.short_code}")
    
    # Try to authenticate
    token = client.authenticate()
    if token:
        print(f"✓ Authentication successful")
        print(f"  Token: {token[:30]}...")
        print(f"  Token expires in: ~3599 seconds")
    else:
        print(f"✗ Authentication returned None")
        
except Exception as e:
    print(f"✗ CONNECTION FAILED")
    print(f"  Error: {str(e)}")
    print(f"  Type: {type(e).__name__}")
    
EOF
```

### 4. Redis Connection Check
```bash
python manage.py shell <<'EOF'
import redis
from django.conf import settings

print("🔌 REDIS CONNECTION CHECK")
print("=" * 50)

try:
    # Parse CELERY_BROKER_URL to get connection details
    from celery import current_app
    
    # Try to ping
    from celery import Celery
    app = Celery('housekeeper_connect')
    app.conf.update(settings.CELERY_BROKER_URL)
    
    with app.connection() as conn:
        print(f"✓ Redis connected")
        
    # Check Celery can reach it
    print(f"✓ Celery broker accessible")
    print(f"  Broker: {settings.CELERY_BROKER_URL}")
    print(f"  Backend: {settings.CELERY_RESULT_BACKEND}")
    
except Exception as e:
    print(f"✗ REDIS CONNECTION FAILED")
    print(f"  Error: {str(e)}")
    print(f"  Ensure Redis is running: redis-cli ping")
    
EOF
```

### 5. Database Connection Check
```bash
python manage.py dbshell <<'EOF'
SELECT 1;  -- Returns 1 if connected
\dt payments_payment;  -- Show payment table
SELECT COUNT(*) FROM payments_payment WHERE status='completed';
EOF
```

---

## Common Issues & Solutions

### Issue: "Payment stuck in pending for 10+ minutes"

**Step 1: Check M-Pesa logs**
```bash
python manage.py shell <<'EOF'
from payments.models import Payment
from django.utils import timezone
from datetime import timedelta

stuck = Payment.objects.filter(
    status='pending',
    stk_initiated_at__lt=timezone.now() - timedelta(minutes=10)
)

for payment in stuck:
    print(f"Payment {payment.id}:")
    print(f"  Amount: {payment.amount} KES")
    print(f"  Phone: {payment.phone}")
    print(f"  Initiated: {payment.stk_initiated_at}")
    print(f"  Last callback: {payment.last_callback_at}")
    print(f"  M-Pesa ID: {payment.mpesa_transaction_id}")
    print()

EOF
```

**Step 2: Check callback logs**
```bash
# Look for this payment's callback attempt
grep "payment.*{id}" /var/log/charlady/payments.log | head -20
```

**Step 3: Manual resolution**
```bash
python manage.py shell <<'EOF'
from payments.models import Payment

payment = Payment.objects.get(id=123)  # Use stuck payment ID

# Option A: Mark as failed if truly stuck
payment.status = 'failed'
payment.failure_reason = 'M-Pesa callback not received after 10 minutes'
payment.save()

# Option B: Retry callback from M-Pesa callback with test data
# (Contact M-Pesa support to resend callback)

EOF
```

---

### Issue: "Celery tasks not running"

**Step 1: Check if Celery Beat is running**
```bash
ps aux | grep celery
# Should show:
# celery worker
# celery beat

# If not:
celery -A housekeeper_connect worker --loglevel=info &
celery -A housekeeper_connect beat --loglevel=info &
```

**Step 2: Check Celery Beat schedule**
```bash
python manage.py shell <<'EOF'
from django_celery_beat.models import PeriodicTask, CrontabSchedule

for task in PeriodicTask.objects.all():
    print(f"Task: {task.name}")
    print(f"  Enabled: {task.enabled}")
    print(f"  Last run: {task.last_run_at}")
    print(f"  Total runs: {task.total_run_count}")
    print()

EOF
```

**Step 3: Manually trigger a task**
```bash
python manage.py shell <<'EOF'
from payments.tasks import calculate_monthly_contributions

# This should show task ID
result = calculate_monthly_contributions.delay()
print(f"Task ID: {result.id}")

# Check if queued
import time
time.sleep(2)
print(f"State: {result.state}")  # Should change from PENDING to SUCCESS

EOF
```

---

### Issue: "M-Pesa authentication failing"

**Step 1: Verify credentials**
```bash
python manage.py shell <<'EOF'
from django.conf import settings

print("M-Pesa Credentials:")
print(f"  Environment: {settings.MPESA_ENVIRONMENT}")
print(f"  Consumer Key: {settings.MPESA_CONSUMER_KEY[:10]}...")
print(f"  Consumer Secret: {settings.MPESA_CONSUMER_SECRET[:10]}...")
print(f"  Endpoint: {settings.MPESA_API_ENDPOINT}")

# These must be complete and correct
if len(settings.MPESA_CONSUMER_KEY) < 20:
    print("⚠️  Consumer Key seems too short!")
if len(settings.MPESA_CONSUMER_SECRET) < 20:
    print("⚠️  Consumer Secret seems too short!")

EOF
```

**Step 2: Test with curl**
```bash
# Get M-Pesa token directly
curl -X GET "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials" \
  -H "Authorization: Basic $(echo -n '$CONSUMER_KEY:$CONSUMER_SECRET' | base64)" \
  -H "Content-Type: application/json"

# If it returns 401: Check credentials
# If it returns 200: Credentials work, issue is in client code
```

**Step 3: Update credentials if needed**
```bash
# Update environment variables
export MPESA_CONSUMER_KEY=new_key_from_daraja
export MPESA_CONSUMER_SECRET=new_secret_from_daraja

# Restart Django
sudo systemctl restart charlady_app
```

---

### Issue: "Badge not being granted to user"

**Step 1: Check Payment → Signal chain**
```bash
python manage.py shell <<'EOF'
from payments.models import Payment
from accounts.models import CustomUser

# Find completed payment
payment = Payment.objects.filter(
    status='completed',
    user__username='worker_username'
).first()

if not payment:
    print("No completed payment found")
else:
    print(f"Payment: {payment.id} - {payment.status}")
    print(f"Amount: {payment.amount}")
    print(f"User: {payment.user.email}")
    print(f"User badge status: {payment.user.is_paid_verified}")
    
    # Check if badge should be granted
    payment_plan = payment.payment_plan
    if payment_plan and payment_plan.grants_badge:
        print(f"Plan grants badge: True")
        if not payment.user.is_paid_verified:
            print("⚠️  ERROR: Badge not granted despite plan requiring it!")
    
EOF
```

**Step 2: Manually grant badge if signal failed**
```bash
python manage.py shell <<'EOF'
from accounts.models import CustomUser

user = CustomUser.objects.get(email='worker@email.com')
user.is_paid_verified = True
user.save()

print(f"✓ Badge granted to {user.email}")

EOF
```

**Step 3: Check signal registration**
```bash
python manage.py shell <<'EOF'
from django.db.models.signals import post_save
from payments.models import Payment
from payments import signals

# List all receivers for Payment post_save
receivers = post_save._live_receivers(Payment)
print(f"Signal receivers for Payment.post_save: {len(receivers)}")
for receiver in receivers:
    print(f"  - {receiver.__module__}.{receiver.__name__}")

# Should include: grant_badge_on_payment

EOF
```

---

## Performance Monitoring

### Response Time Tracking
```bash
# Check M-Pesa STK push response time
python manage.py shell <<'EOF'
from payments.models import Payment
from django.utils import timezone
from datetime import timedelta

# Recent STK pushes (last hour)
hour_ago = timezone.now() - timedelta(hours=1)
recent = Payment.objects.filter(stk_initiated_at__gte=hour_ago)

total_time = 0
count = 0

for payment in recent:
    if payment.payment_verified_at:
        duration = (payment.payment_verified_at - payment.stk_initiated_at).total_seconds()
        total_time += duration
        count += 1

if count > 0:
    avg_time = total_time / count
    print(f"Average payment processing time: {avg_time:.2f} seconds")
    if avg_time > 60:
        print("⚠️  WARNING: Average time > 60 seconds")
else:
    print("No completed payments in last hour")

EOF
```

### Database Query Performance
```bash
# Enable query logging in development
python manage.py shell <<'EOF'
from django.db import connection
from django.test.utils import CaptureQueriesContext

with CaptureQueriesContext(connection) as context:
    # Run some queries
    from payments.models import Payment
    payments = list(Payment.objects.all()[:10])

print(f"Queries executed: {len(context)}")
for i, query in enumerate(context, 1):
    print(f"\n{i}. {query['sql'][:80]}...")
    print(f"   Time: {query['time']}s")

EOF
```

---

## Log Analysis

### Extract Error Patterns
```bash
# Show all errors from last 24 hours
grep "ERROR\|EXCEPTION\|FAILED" /var/log/charlady/payments.log | tail -50

# Check specific error types
grep "M-Pesa.*error" /var/log/charlady/payments.log -i

# Count errors by type
grep "ERROR" /var/log/charlady/payments.log | cut -d':' -f2 | sort | uniq -c | sort -rn
```

### Analyze Callback Patterns
```bash
# Show all callbacks
grep "callback received\|callback processed" /var/log/charlady/payments.log

# Failed callbacks
grep "callback" /var/log/charlady/payments.log | grep -i "failed\|error"

# Callback response time
grep "callback processed in" /var/log/charlady/payments.log
```

---

## Alerting Setup

### Create Alert Status Dashboard
```bash
python manage.py shell <<'EOF'
from payments.models import Payment
from django.utils import timezone
from datetime import timedelta

print("=" * 60)
print("SYSTEM HEALTH CHECK - " + timezone.now().strftime("%Y-%m-%d %H:%M:%S"))
print("=" * 60)

# 1. Payment success rate (last hour)
hour_ago = timezone.now() - timedelta(hours=1)
recent = Payment.objects.filter(stk_initiated_at__gte=hour_ago)
if recent.count() > 0:
    success_rate = (recent.filter(status='completed').count() / recent.count()) * 100
    status = "✓ OK" if success_rate >= 95 else "✗ ALERT"
    print(f"\n1. Success Rate (1 hour): {success_rate:.1f}% {status}")
else:
    print(f"\n1. Success Rate (1 hour): No payments")

# 2. Stuck payments
stuck = Payment.objects.filter(
    status='pending',
    stk_initiated_at__lt=timezone.now() - timedelta(minutes=5)
).count()
status = "✓ OK" if stuck == 0 else f"✗ ALERT ({stuck} stuck)"
print(f"2. Stuck Payments (>5 min): {status}")

# 3. Failed payments (last 24 hours)
day_ago = timezone.now() - timedelta(hours=24)
failed_24h = Payment.objects.filter(
    status='failed',
    stk_initiated_at__gte=day_ago
).count()
status = "✓ OK" if failed_24h < 10 else f"✗ ALERT ({failed_24h} failed)"
print(f"3. Failed Payments (24h): {status}")

# 4. Celery health
# (requires celery inspect)
print(f"4. Celery Tasks: Check with 'celery -A housekeeper_connect inspect active'")

# 5. Database size
from django.db import connection
cursor = connection.cursor()
cursor.execute("SELECT pg_size_pretty(pg_database_size('charlady_db'));")
db_size = cursor.fetchone()[0]
print(f"5. Database Size: {db_size}")

print("\n" + "=" * 60)

EOF
```

---

## Recovery Procedures

### Recover Stuck Payment
```bash
python manage.py shell <<'EOF'
from payments.models import Payment
import json

payment = Payment.objects.get(id=123)  # Replace with stuck payment ID

# Create recovery record
print(f"Recovery action for Payment {payment.id}:")
print(f"  Current status: {payment.status}")
print(f"  History: {payment.status_history}")

# Option 1: Check last callback data
last_callback = payment.callback_response_log
if last_callback:
    data = json.loads(last_callback)
    print(f"  Last M-Pesa response: {data}")

# Option 2: Ask user to retry
print(f"\n  Recovery:")
print(f"  1. User retries payment via UI")
print(f"  2. OR contact M-Pesa to resend callback")
print(f"  3. OR manually mark as failed")

EOF
```

### Resync User Badges
```bash
python manage.py shell <<'EOF'
from payments.models import Payment
from accounts.models import CustomUser

# Find all users who should have badge
should_have_badge = CustomUser.objects.filter(
    payment__status='completed',
    payment__payment_plan__grants_badge=True
).distinct()

updated = 0
for user in should_have_badge:
    if not user.is_paid_verified:
        user.is_paid_verified = True
        user.save()
        updated += 1
        print(f"✓ Badge granted to {user.email}")

print(f"\nTotal users updated: {updated}")

EOF
```

---

## Debugging Checklist

When troubleshooting payment issues, run through this checklist:

- [ ] Check payment status in database: `python manage.py shell`
- [ ] Verify M-Pesa connection: `celery -A housekeeper_connect inspect active`
- [ ] Check logs: `tail -f /var/log/charlady/payments.log`
- [ ] Verify database size: `SELECT pg_size_pretty(pg_database_size('charlady_db'));`
- [ ] Check Redis connection: `redis-cli ping`
- [ ] Verify M-Pesa credentials: Check settings.py MPESA_* values
- [ ] Test callback manually: `curl -X POST .../mpesa-callback/ --data {...}`
- [ ] Check signal handlers: `python manage.py shell` → Check receivers
- [ ] Review recent git changes: `git log --oneline -10`
- [ ] Monitor system resources: `top` / `free` / `df`

---

**Last Updated**: April 17, 2026
**Version**: 1.0.0
**Status**: PRODUCTION MONITORING READY
