# .ENV SETUP GUIDE
## Step-by-Step Configuration for Charlady M-Pesa Integration

---

## 📋 QUICK START

```bash
# 1. Copy the example file
cp .env.example .env

# 2. Fill in your credentials (see sections below)
nano .env

# 3. Verify configuration
python manage.py check

# 4. Load environment variables
source .env  # On Linux/Mac
# Or on Windows PowerShell: Get-Content .env | foreach { $name, $value = $_.split('='); [Environment]::SetEnvironmentVariable($name, $value) }
```

---

## 🔧 SECTION-BY-SECTION CONFIGURATION

### 1. DJANGO CONFIGURATION

**What to do:**

```env
DEBUG=False  # Production: ALWAYS False
SECRET_KEY=<generate_new_key>  # Generate with: python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
ALLOWED_HOSTS=charlady.co.ke,www.charlady.co.ke,127.0.0.1
ENVIRONMENT=production
```

**How to generate SECRET_KEY:**
```bash
python manage.py shell
>>> from django.core.management.utils import get_random_secret_key
>>> print(get_random_secret_key())
# Copy the output to SECRET_KEY in .env
```

---

### 2. DATABASE CONFIGURATION

**Option A: Using DATABASE_URL (Recommended)**
```env
DATABASE_URL=postgresql://charlady:your_password@localhost:5432/charlady_db
```

**Option B: Individual settings**
```env
DB_ENGINE=django.db.backends.postgresql
DB_NAME=charlady_db
DB_USER=charlady
DB_PASSWORD=your_postgres_password
DB_HOST=localhost
DB_PORT=5432
```

**How to setup PostgreSQL:**
```bash
# 1. Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# 2. Create database
sudo -u postgres psql
CREATE DATABASE charlady_db;
CREATE USER charlady WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE charlady_db TO charlady;
\q

# 3. Test connection
psql postgresql://charlady:your_password@localhost:5432/charlady_db -c "SELECT 1;"
```

---

### 3. M-PESA SANDBOX CONFIGURATION (For Testing)

**Get credentials from:** https://developer.safaricom.co.ke/

**Steps:**

1. Create Safaricom developer account
2. Create an app
3. Copy credentials:

```env
MPESA_ENVIRONMENT=sandbox  # Change to 'production' when ready

# Get these from Daraja dashboard
MPESA_CONSUMER_KEY_SANDBOX=DU68PrjYY2nEYvXA5Eq2GyoL4c7LQwN8i8X01aGyRQp6zGjD
MPESA_CONSUMER_SECRET_SANDBOX=your_sandbox_consumer_secret_here
MPESA_PASSKEY_SANDBOX=bfb279f9ba9b9d8c25f1c0e1c5f54987b51e1dd45e2c6c0e4f4f8c1f8f9b9e8c
MPESA_SHORT_CODE_SANDBOX=4564139

MPESA_CALLBACK_URL=https://your-domain.com/payments/mpesa-callback/
```

**Verify with test script:**
```bash
python manage.py shell
>>> from payments.mpesa_service import get_mpesa_client
>>> client = get_mpesa_client()
>>> token = client.authenticate()
>>> print(f"✓ Connected! Token: {token[:30]}...")
```

---

### 4. M-PESA PRODUCTION CONFIGURATION

**⚠️ ONLY after sandbox testing passes**

```env
MPESA_ENVIRONMENT=production  # Switch from sandbox

# Request production credentials from Safaricom
MPESA_CONSUMER_KEY_PRODUCTION=your_production_key
MPESA_CONSUMER_SECRET_PRODUCTION=your_production_secret
MPESA_PASSKEY_PRODUCTION=your_production_passkey
MPESA_SHORT_CODE_PRODUCTION=your_production_shortcode

# Update callback URL to production domain
MPESA_CALLBACK_URL=https://charlady.co.ke/payments/mpesa-callback/
```

**Required before going live:**
- [ ] Consumer Key & Secret obtained from Safaricom
- [ ] Callback URL registered in M-Pesa portal
- [ ] M-Pesa server IPs whitelisted in firewall
- [ ] SSL certificate installed (HTTPS required)
- [ ] Test payment with 1 KES completed successfully

---

### 5. REDIS CONFIGURATION (For Celery)

**Installation:**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows (Docker recommended)
docker run -d -p 6379:6379 redis:latest
```

**Configuration:**
```env
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

**Verify:**
```bash
redis-cli ping
# Should return: PONG
```

---

### 6. CELERY CONFIGURATION

```env
CELERY_TIMEZONE=Africa/Nairobi
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP=True
CELERY_TASK_TIME_LIMIT=1800         # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT=1500    # 25 minutes
CELERY_RESULT_EXPIRES=3600          # 1 hour
```

**Start Celery services:**
```bash
# Terminal 1: Celery Worker
celery -A housekeeper_connect worker --loglevel=info

# Terminal 2: Celery Beat (scheduler)
celery -A housekeeper_connect beat --loglevel=info
```

---

### 7. EMAIL CONFIGURATION

**Using Gmail:**

```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_app_specific_password  # NOT your main password!
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@charlady.co.ke
```

**Get Gmail App Password:**
1. Enable 2FA on your Google account
2. Visit: https://myaccount.google.com/apppasswords
3. Select "Mail" and "Windows Computer"
4. Copy the 16-character password
5. Paste as `EMAIL_HOST_PASSWORD`

**Test:**
```bash
python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'This works!', 'noreply@charlady.co.ke', ['admin@charlady.co.ke'])
```

---

### 8. AWS S3 CONFIGURATION (For file uploads)

**Get credentials from AWS IAM:**

```env
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_STORAGE_BUCKET_NAME=charlady-media-bucket
AWS_S3_REGION_NAME=eu-west-1
```

**Or use local storage (development):**
```env
# Comment out AWS settings and Django will use local filesystem
# Media files stored in: media/
```

---

### 9. SECURITY SETTINGS (Production)

```env
# HTTPS enforcement
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Security headers
SECURE_HSTS_SECONDS=31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS=True
SECURE_HSTS_PRELOAD=True

# Clickjacking protection
X_FRAME_OPTIONS=DENY
```

---

### 10. LOGGING & MONITORING

**For Sentry error tracking:**

1. Create account at: https://sentry.io/
2. Create project for Django
3. Copy DSN:

```env
SENTRY_DSN=https://your_key@sentry.io/project_id
SENTRY_ENVIRONMENT=production
```

**For local logging:**
```env
LOG_LEVEL=INFO  # Use DEBUG in development, WARNING in production
```

---

## 🧪 VERIFICATION CHECKLIST

Run these commands to verify your configuration:

```bash
# 1. Check Django settings
python manage.py check

# 2. Test database connection
python manage.py dbshell
# Should connect without errors, then type: \q

# 3. Test M-Pesa connection
python manage.py shell <<'EOF'
from payments.mpesa_service import get_mpesa_client
client = get_mpesa_client()
token = client.authenticate()
print(f"✓ M-Pesa OK: {token[:20]}...")
EOF

# 4. Test Redis connection
python -c "import redis; redis.Redis(host='localhost', port=6379).ping(); print('✓ Redis OK')"

# 5. Test email
python manage.py shell <<'EOF'
from django.core.mail import send_mail
send_mail('Test', 'OK', 'noreply@charlady.co.ke', ['admin@charlady.co.ke'])
print("✓ Email sent")
EOF

# 6. Test migrations
python manage.py migrate --plan

# 7. Run all tests
python test_integration.py
```

---

## 📋 PRODUCTION DEPLOYMENT CHECKLIST

Before deploying to production:

- [ ] SECRET_KEY changed
- [ ] DEBUG=False
- [ ] ALLOWED_HOSTS configured
- [ ] HTTPS/SSL enabled
- [ ] M-Pesa production credentials added
- [ ] Database backed up
- [ ] Redis available
- [ ] Email configured
- [ ] Sentry DSN added
- [ ] AWS S3 configured (or local storage if testing)
- [ ] All verification tests passing
- [ ] `.env` file permissions secured (`chmod 600 .env`)
- [ ] `.env` added to `.gitignore`

---

## 🔐 SECURITY BEST PRACTICES

### Before Committing Code:

```bash
# Add .env to .gitignore (CRITICAL!)
echo ".env" >> .gitignore

# Ensure .env is not tracked
git rm --cached .env
git add .gitignore
git commit -m "Remove .env from tracking"
```

### File Permissions:

```bash
# Restrict access to .env (Unix/Linux/Mac)
chmod 600 .env

# Verify
ls -la .env
# Should show: -rw------- (read/write for owner only)
```

### Secret Rotation:

- Rotate Django SECRET_KEY every 3 months
- Rotate database passwords every quarter
- Rotate M-Pesa credentials if compromised
- Use AWS Secrets Manager for additional security

---

## 🆘 TROUBLESHOOTING

### Error: "M-Pesa authentication failed"
```
Solution: Check MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET
          Verify you're using sandbox keys for sandbox environment
          Ensure MPESA_ENVIRONMENT is set correctly
```

### Error: "Database connection refused"
```
Solution: Check DB_HOST, DB_PORT, DB_NAME in .env
          Verify PostgreSQL is running: psql -U charlady -d charlady_db
          Check credentials in DATABASE_URL
```

### Error: "Redis connection refused"
```
Solution: Start Redis: redis-server
          Check REDIS_URL points to running Redis instance
          Verify port 6379 is accessible
```

### Error: "Email not sending"
```
Solution: Generate new Gmail App Password (not your main password!)
          Check EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
          If using different provider, verify SMTP credentials
          Check firewall allows SMTP port (587 or 465)
```

### Error: ".env file not loaded"
```
Solution: Django doesn't auto-load .env
          Use: pip install python-dotenv
          At top of settings.py, add:
          
          import os
          from dotenv import load_dotenv
          load_dotenv()
```

---

## 📞 SUPPORT

- **Framework Issues**: Django documentation
- **M-Pesa Issues**: Safaricom support
- **PostgreSQL Issues**: PostgreSQL documentation
- **Redis Issues**: Redis documentation
- **Platform-specific issues**: See MONITORING_AND_DEBUGGING_GUIDE.md

---

**Version**: 1.0.0  
**Last Updated**: April 17, 2026  
**Status**: ✅ PRODUCTION READY
