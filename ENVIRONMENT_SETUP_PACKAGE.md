# ENVIRONMENT SETUP - COMPLETE PACKAGE
## All Environment Configuration Files & How to Use Them

---

## 📦 WHAT YOU HAVE

I've created a complete environment configuration package with 4 components:

### 1. `.env.example` (900+ lines)
**Purpose**: Complete template with all possible configurations  
**When to use**: Reference when you need to understand what each variable does  
**Status**: ✅ Committed to git (safe to share)

### 2. `ENV_SETUP_GUIDE.md` (300+ lines)
**Purpose**: Step-by-step guide for filling in each section  
**When to use**: Detailed instructions with examples for each configuration  
**Status**: ✅ Reference documentation

### 3. `ENV_QUICK_REFERENCE.md` (250+ lines)
**Purpose**: Quick reference with values you already have + minimal config  
**When to use**: Fast lookup for pre-configured values  
**Status**: ✅ Quick reference

### 4. `generate_env.py` (executable script)
**Purpose**: Interactive Python script that generates .env file  
**When to use**: Fastest way to create .env file with proper values  
**Status**: ✅ Ready to run

### 5. `.env` (YOUR ACTUAL CONFIG - NOT COMMITTED)
**Purpose**: Your actual production/development secrets  
**When to use**: Django reads this automatically at startup  
**Status**: 🔒 NEVER COMMIT - Add to .gitignore (already done)

---

## 🚀 QUICK START (5 MINUTES)

### Option A: Interactive Generation (Recommended)
```bash
# Run the interactive script
python generate_env.py

# It will:
# 1. Ask questions about your setup
# 2. Generate a secure Secret Key
# 3. Configure M-Pesa sandbox (already have these keys)
# 4. Set up Redis, PostgreSQL, Email
# 5. Create .env file automatically
```

### Option B: Manual Configuration
```bash
# Copy the template
cp .env.example .env

# Edit with your values (use ENV_SETUP_GUIDE.md as reference)
nano .env  # or: code .env  # or: vim .env
```

### Option C: Quick Minimal Setup
```bash
# Copy pre-configured values from ENV_QUICK_REFERENCE.md
# Into a .env file
```

---

## 🔄 FILE RELATIONSHIPS

```
.env.example (template)
    ↓
    ├─→ generate_env.py (creates .env interactively)
    ├─→ ENV_SETUP_GUIDE.md (how to fill each section)
    └─→ ENV_QUICK_REFERENCE.md (quick lookup)
    
    Final Result: .env (YOUR PRODUCTION SECRETS)
    │
    └─→ Django loads automatically
        (Never commit to git)
```

---

## 📋 CONFIGURATION CHECKLIST

### Before Running `generate_env.py`

- [ ] **PostgreSQL** installed and running
- [ ] **Redis** installed and running (or know cloud Redis URL)
- [ ] **M-Pesa credentials** ready (have consumer secret)
- [ ] **Email credentials** ready (optional, can skip)
- [ ] **Domain** decided (for production)

### After Running `generate_env.py`

- [ ] `.env` file created locally
- [ ] `.env` NOT committed to git (check .gitignore)
- [ ] All required values filled in (marked as required)
- [ ] Email configured (optional, can use console mode)
- [ ] Database connection working (`python manage.py dbshell`)
- [ ] M-Pesa connection verified (`python manage.py check`)

---

## 🎯 THREE PATHS TO SETUP

### PATH 1: Fastest (Recommended) ⚡
```bash
# ~2 minutes, interactive prompts
python generate_env.py

# Answer questions and done!
# .env file is ready to use
```

**Best for**: First-time setup, development environment

---

### PATH 2: Detailed Reference 📖
```bash
# ~10 minutes, manual editing with reference

# 1. Copy template
cp .env.example .env

# 2. Read the setup guide
cat ENV_SETUP_GUIDE.md  # or open in editor

# 3. Edit .env with your values
nano .env

# 4. Save and verify
python manage.py check
```

**Best for**: Production setup, understanding each setting

---

### PATH 3: Quick Reference 🏃
```bash
# ~5 minutes, copy pre-configured values
cat ENV_QUICK_REFERENCE.md

# Copy the "MINIMAL .ENV TO GET STARTED" section
# Create .env with those values
# Fill in your custom settings (PostgreSQL password, etc.)
```

**Best for**: Experienced developers, quick testing

---

## 📊 WHAT EACH FILE CONTAINS

### `.env.example` - Full Template
```
✅ DJANGO CONFIGURATION
   - SECRET_KEY (placeholder)
   - DEBUG (True/False)
   - ALLOWED_HOSTS
   - etc.

✅ DATABASE CONFIGURATION
   - DATABASE_URL (placeholder)
   - Individual DB settings
   - Connection pooling
   - etc.

✅ M-PESA SANDBOX
   - MPESA_CONSUMER_KEY_SANDBOX ✓ (have this)
   - MPESA_CONSUMER_SECRET_SANDBOX (need this)
   - MPESA_PASSKEY_SANDBOX ✓ (have this)
   - MPESA_SHORT_CODE_SANDBOX ✓ (have this)
   - etc.

✅ M-PESA PRODUCTION
   - (fill after getting from Safaricom)

✅ REDIS & CELERY
   - REDIS_URL
   - CELERY_BROKER_URL
   - CELERY_TIMEZONE = Africa/Nairobi
   - etc.

✅ EMAIL CONFIGURATION
   - EMAIL_HOST
   - EMAIL_PORT
   - EMAIL_HOST_USER
   - etc.

✅ AWS S3 & STORAGE
   - (optional, local storage default)

✅ SECURITY SETTINGS
   - HTTPS enforcement
   - CSRF protection
   - etc.

✅ PAYMENT CONFIGURATION
   - VERIFICATION_BADGE_COST = 250 KES
   - MONTHLY_CONTRIBUTION_PERCENTAGE = 3%
   - etc.

✅ FEATURE FLAGS
   - ENABLE_MPESA_PAYMENTS = True
   - etc.
```

Total: ~80 variables, all documented with comments

---

### `ENV_SETUP_GUIDE.md` - Implementation Guide

For each major section:
- ✅ Step-by-step instructions
- ✅ Where to get credentials
- ✅ How to verify configuration
- ✅ Common issues & solutions
- ✅ Testing commands

---

### `ENV_QUICK_REFERENCE.md` - Values You Have

**Pre-filled (Copy directly to .env)**:
```
✅ M-Pesa Sandbox Keys
✅ Payment Configuration
✅ Celery Configuration
✅ Feature Flags
✅ Timezone & Localization
```

**You need to fill**:
```
❌ Django Secret Key (generate)
❌ PostgreSQL credentials
❌ Redis URL
❌ Email credentials
❌ M-Pesa Consumer Secret
```

---

### `generate_env.py` - Interactive Script

**What it does**:
1. Generates Django SECRET_KEY automatically
2. Asks about PostgreSQL setup
3. Asks about Redis setup
4. Asks about M-Pesa configuration
5. Asks about Email configuration
6. Creates .env with all values

**What it handles**:
- ✅ Automatic secret key generation
- ✅ Database URL construction
- ✅ Redis URL construction
- ✅ Multi-choice options (Gmail, custom SMTP, etc.)
- ✅ Pre-fills known values (M-Pesa sandbox keys)
- ✅ Validation of required fields

---

## 🛠️ USAGE SCENARIOS

### Scenario 1: First-Time Development Setup
```bash
# You have:
# - MacBook/Windows
# - Python installed
# - NO databases set up yet

# Do this:
python generate_env.py
# Follow prompts - it will ask you to install PostgreSQL/Redis
# Once done: .env is ready
```

---

### Scenario 2: Production Deployment
```bash
# You have:
# - Production server running
# - PostgreSQL & Redis already configured
# - M-Pesa production credentials from Safaricom

# Do this:
# 1. Read ENV_SETUP_GUIDE.md Production section
cat ENV_SETUP_GUIDE.md | grep -A 50 "Production"

# 2. Either run generate_env.py or manually create .env
cp .env.example .env
nano .env  # Fill in production values

# 3. Verify
python manage.py check --deploy

# 4. Deploy
./deploy_production.sh deploy
```

---

### Scenario 3: Team Collaboration
```bash
# Team member joins project

# What's in git:
# ✅ .env.example (template)
# ✅ ENV_SETUP_GUIDE.md (how to set up)
# ✅ ENV_QUICK_REFERENCE.md (quick lookup)
# ✅ generate_env.py (automation)
# ❌ .env (never in git) - in .gitignore

# New team member:
git clone <repo>
python generate_env.py  # Create their own .env
# Or read ENV_SETUP_GUIDE.md and manually create
```

---

## ✅ VERIFICATION

After creating `.env`, verify it works:

```bash
# 1. Django check
python manage.py check
# Should pass with no errors

# 2. Database connection
python manage.py dbshell
# Should connect, then type: \q

# 3. M-Pesa connection
python manage.py shell
>>> from payments.mpesa_service import get_mpesa_client
>>> client = get_mpesa_client()
>>> token = client.authenticate()
>>> print("✓ M-Pesa working")

# 4. Redis connection
python -c "import redis; redis.Redis(host='localhost').ping(); print('✓ Redis OK')"

# 5. Run migrations
python manage.py migrate

# 6. Integration tests
python test_integration.py
# Should pass 100% (6/6 test suites)
```

---

## 🔐 SECURITY REMINDERS

### .env File Security

```bash
# 1. Ensure .env is in .gitignore
grep ".env" .gitignore  # Should show: .env

# 2. Restrict file permissions (Unix/Mac/Linux)
chmod 600 .env  # Only owner can read/write

# 3. NEVER commit .env to git
git status  # Should NOT show .env

# 4. Keep secrets secret
# Don't share .env with anyone
# Don't paste .env in Slack/email
# Don't commit to public repos
```

### Secret Rotation

- [ ] Django SECRET_KEY: Every 3 months
- [ ] Database password: Every 3 months
- [ ] Email credentials: Every 3 months
- [ ] M-Pesa credentials: If compromised
- [ ] Redis password: Every 3 months

---

## 📞 FILE LOCATIONS

All files are in project root:

```
/project-root/
├── .env.example                    ← Template (in git)
├── .env                           ← YOUR CONFIG (NOT in git)
├── ENV_SETUP_GUIDE.md             ← Step-by-step guide
├── ENV_QUICK_REFERENCE.md         ← Quick lookup
├── generate_env.py                ← Interactive script
├── .gitignore                     ← Blocks .env from git
└── manage.py
```

---

## 🎓 LEARNING RESOURCES

### If you're new to environment variables:
- Django docs: https://docs.djangoproject.com/en/stable/howto/deployment/checklist/
- 12factor.net: https://12factor.net/config

### If you're new to M-Pesa:
- Daraja API docs: https://developer.safaricom.co.ke/
- Integration guide: See `PRODUCTION_DEPLOYMENT_GUIDE.md`

### If you're new to Celery:
- Celery docs: https://docs.celeryproject.io/
- Our config: `housekeeper_connect/celery_config.py`

---

## 🚀 NEXT STEPS

### Immediate (Today)
1. [ ] Choose setup path (generate_env.py recommended)
2. [ ] Run setup process
3. [ ] Verify with test commands
4. [ ] Run `python manage.py migrate`

### Short-term (This week)
1. [ ] Execute QA tests from QA_TEST_SCENARIOS.py
2. [ ] Test payment flow end-to-end
3. [ ] Verify badge granting

### Medium-term (This month)
1. [ ] Get M-Pesa production credentials
2. [ ] Update .env with production values
3. [ ] Run `./deploy_production.sh deploy`

---

## 📊 SUMMARY TABLE

| File | Purpose | Readwrite | How to Use |
|------|---------|-----------|-----------|
| `.env.example` | Template | Read | Reference when confused |
| `.env` | Your config | Read/Write | Django reads at startup |
| `ENV_SETUP_GUIDE.md` | Instructions | Read | Step-by-step guide |
| `ENV_QUICK_REFERENCE.md` | Quick lookup | Read | Find value quickly |
| `generate_env.py` | Auto-generator | Execute | Run to create .env |

---

## ✨ YOU'RE ALL SET!

Everything is ready to use. Pick your preferred method:

**🔥 Fastest**: `python generate_env.py` (2 min)  
**📖 Detailed**: Read `ENV_SETUP_GUIDE.md` + manual edit (10 min)  
**⚡ Quick**: Copy from `ENV_QUICK_REFERENCE.md` (5 min)

All three methods result in a working `.env` file! 🎉

---

**Document Version**: 1.0.0  
**Last Updated**: April 17, 2026  
**Status**: ✅ PRODUCTION READY
