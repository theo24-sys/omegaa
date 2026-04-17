# .ENV QUICK REFERENCE
## Pre-Filled Values from Previous Implementation

---

## ✅ VALUES YOU ALREADY HAVE

Copy these directly into your `.env` file:

### M-Pesa Sandbox (Already Verified)
```env
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY_SANDBOX=DU68PrjYY2nEYvXA5Eq2GyoL4c7LQwN8i8X01aGyRQp6zGjD
MPESA_CONSUMER_SECRET_SANDBOX=your_sandbox_consumer_secret_here
MPESA_PASSKEY_SANDBOX=bfb279f9ba9b9d8c25f1c0e1c5f54987b51e1dd45e2c6c0e4f4f8c1f8f9b9e8c
MPESA_SHORT_CODE_SANDBOX=4564139
MPESA_BUSINESS_TYPE_SANDBOX=DefaultAccount
MPESA_API_ENDPOINT_SANDBOX=https://sandbox.safaricom.co.ke
```

### Payment Configuration (Already Validated)
```env
CURRENCY=KES
VERIFICATION_BADGE_COST=250
VERIFICATION_BADGE_VALIDITY_DAYS=365
MONTHLY_CONTRIBUTION_PERCENTAGE=3
MONTHLY_CONTRIBUTION_MINIMUM=100
```

### Celery Configuration (Already Tested)
```env
CELERY_TIMEZONE=Africa/Nairobi
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
CELERY_TASK_TIME_LIMIT=1800
CELERY_TASK_SOFT_TIME_LIMIT=1500
CELERY_RESULT_EXPIRES=3600
```

### Feature Flags (Ready for Production)
```env
ENABLE_MPESA_PAYMENTS=True
ENABLE_WORKER_VERIFICATION=True
ENABLE_MONTHLY_CONTRIBUTIONS=True
ENABLE_ADMIN_DASHBOARD=True
```

### Timezone & Localization
```env
TIME_ZONE=Africa/Nairobi
LANGUAGE_CODE=en-us
SUPPORTED_LANGUAGES=en,sw
```

---

## ⏳ VALUES YOU NEED TO FILL IN

### 1. Django Security (GENERATE NEW)
```env
# Generate with:
# python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
SECRET_KEY=<GENERATE_NEW>
ALLOWED_HOSTS=charlady.co.ke,www.charlady.co.ke
```

### 2. Database Configuration (SET UP YOUR POSTGRES)
```env
# Step 1: Install PostgreSQL
# Step 2: Create database & user
# Step 3: Add credentials here:
DATABASE_URL=postgresql://charlady:<PASSWORD>@localhost:5432/charlady_db

# Or individual settings:
DB_ENGINE=django.db.backends.postgresql
DB_NAME=charlady_db
DB_USER=charlady
DB_PASSWORD=<YOUR_PG_PASSWORD>
DB_HOST=localhost
DB_PORT=5432
```

### 3. Redis Configuration (LOCAL OR CLOUD)
```env
# Local Redis (default)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Or Cloud Redis (e.g., Redis Cloud):
REDIS_URL=redis://:<PASSWORD>@<HOST>:6379/0
CELERY_BROKER_URL=redis://:<PASSWORD>@<HOST>:6379/0
CELERY_RESULT_BACKEND=redis://:<PASSWORD>@<HOST>:6379/0
```

### 4. Email Configuration (OPTIONAL - FOR PRODUCTION)
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=<YOUR_EMAIL@gmail.com>
EMAIL_HOST_PASSWORD=<GMAIL_APP_PASSWORD>
DEFAULT_FROM_EMAIL=noreply@charlady.co.ke
```

### 5. M-Pesa Production (WHEN READY - NOT NOW)
```env
# Only fill after sandbox testing complete
# And after getting credentials from Safaricom

# Get from Safaricom
MPESA_ENVIRONMENT=production
MPESA_CONSUMER_KEY_PRODUCTION=<FROM_SAFARICOM>
MPESA_CONSUMER_SECRET_PRODUCTION=<FROM_SAFARICOM>
MPESA_PASSKEY_PRODUCTION=<FROM_SAFARICOM>
MPESA_SHORT_CODE_PRODUCTION=<FROM_SAFARICOM>

MPESA_CALLBACK_URL=https://charlady.co.ke/payments/mpesa-callback/
MPESA_ALLOWED_IPS=<ASK_SAFARICOM>
```

---

## 🚀 MINIMAL .ENV TO GET STARTED

For immediate testing, use this minimal config:

```env
# === REQUIRED FOR TESTING ===

DEBUG=False
SECRET_KEY=your_generated_secret_key_here

ALLOWED_HOSTS=127.0.0.1,localhost

# Database (PostgreSQL)
DATABASE_URL=postgresql://charlady:password@localhost:5432/charlady_db

# Redis (Local)
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# M-Pesa Sandbox (Already have these)
MPESA_ENVIRONMENT=sandbox
MPESA_CONSUMER_KEY_SANDBOX=DU68PrjYY2nEYvXA5Eq2GyoL4c7LQwN8i8X01aGyRQp6zGjD
MPESA_CONSUMER_SECRET_SANDBOX=your_sandbox_secret
MPESA_PASSKEY_SANDBOX=bfb279f9ba9b9d8c25f1c0e1c5f54987b51e1dd45e2c6c0e4f4f8c1f8f9b9e8c
MPESA_SHORT_CODE_SANDBOX=4564139
MPESA_CALLBACK_URL=http://localhost:8000/payments/mpesa-callback/

# Timezone
CELERY_TIMEZONE=Africa/Nairobi

# === OPTIONAL ===

# Email (for production only)
# EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Logging
LOG_LEVEL=INFO

# Django
ENVIRONMENT=production
PAYMENT_TIMEOUT_MINUTES=5
```

---

## 🔧 SETUP COMMANDS

### Step 1: Generate and Copy Configuration

```bash
# Navigate to project
cd /c/Users/user/Downloads/omegaa-main/omegaa-main

# Copy template
cp .env.example .env

# Generate secret key
python -c "from django.core.management.utils import get_random_secret_key; print('SECRET_KEY=' + get_random_secret_key())"
# Copy output and paste into .env
```

### Step 2: Set Up PostgreSQL

```bash
# Install PostgreSQL (if not already installed)
# Windows: Download from https://www.postgresql.org/download/windows/
# Mac: brew install postgresql
# Linux: sudo apt-get install postgresql

# Create database
psql -U postgres
postgres=# CREATE DATABASE charlady_db;
postgres=# CREATE USER charlady WITH PASSWORD 'your_password';
postgres=# GRANT ALL PRIVILEGES ON DATABASE charlady_db TO charlady;
postgres=# \q

# Test connection
psql postgresql://charlady:your_password@localhost:5432/charlady_db -c "SELECT 1;"
```

### Step 3: Set Up Redis

```bash
# Install Redis
# Windows: Docker recommended
# Mac: brew install redis
# Linux: sudo apt-get install redis-server

# Start Redis
redis-server

# Test connection
redis-cli ping
# Should return: PONG
```

### Step 4: Verify Configuration

```bash
# Check Django
python manage.py check

# Test database
python manage.py dbshell

# Test M-Pesa
python manage.py shell
>>> from payments.mpesa_service import get_mpesa_client
>>> client = get_mpesa_client()
>>> token = client.authenticate()
>>> print("✓ M-Pesa OK")

# Test Redis
python -c "import redis; redis.Redis(host='localhost').ping(); print('✓ Redis OK')"
```

### Step 5: Run Migrations

```bash
python manage.py migrate
```

### Step 6: Start Services

```bash
# Terminal 1: Django
python manage.py runserver

# Terminal 2: Celery Worker
celery -A housekeeper_connect worker --loglevel=info

# Terminal 3: Celery Beat
celery -A housekeeper_connect beat --loglevel=info
```

---

## 📊 CONFIGURATION STATUS

| Component | Status | What to Do |
|-----------|--------|-----------|
| M-Pesa Sandbox Keys | ✅ Have | Copy to .env |
| Payment Config | ✅ Have | Copy to .env |
| Celery Config | ✅ Have | Copy to .env |
| Django Secret Key | ❌ Generate | Generate with Python command |
| PostgreSQL | ❌ Setup | Create DB and user |
| Redis | ❌ Setup | Install and start service |
| Email | ⏳ Optional | Setup for production later |
| M-Pesa Production | ❌ Future | Get from Safaricom after testing |

---

## 🧪 TEST CHECKLIST AFTER SETUP

Run these to verify everything works:

```bash
# 1. Django check
✓ python manage.py check

# 2. Database connection
✓ python manage.py dbshell (then \q to exit)

# 3. M-Pesa connection
✓ python manage.py shell
  >>> from payments.mpesa_service import get_mpesa_client
  >>> client.authenticate()

# 4. Redis connection
✓ redis-cli ping

# 5. Migrations
✓ python manage.py showmigrations

# 6. Integration tests
✓ python test_integration.py

# 7. Celery workers
✓ celery -A housekeeper_connect inspect active
```

---

## 📝 NEXT STEPS

1. **Generate SECRET_KEY** → Copy to .env
2. **Setup PostgreSQL** → Create database
3. **Setup Redis** → Start Redis service
4. **Copy known values** → See "✅ VALUES YOU ALREADY HAVE" section
5. **Fill in placeholders** → See "ENV_SETUP_GUIDE.md" for details
6. **Run verification tests** → See "TEST CHECKLIST" above
7. **Deploy to production** → See "PRODUCTION_DEPLOYMENT_GUIDE.md"

---

**Document Version**: 1.0.0  
**Last Updated**: April 17, 2026  
**Status**: ✅ READY FOR USE
