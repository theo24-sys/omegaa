#!/usr/bin/env python
"""
ENV Generator - Interactive .env Configuration Helper
Generates a properly configured .env file from the template
"""

import os
import sys
import re
from pathlib import Path

def generate_secret_key():
    """Generate a Django secret key"""
    try:
        from django.core.management.utils import get_random_secret_key
        return get_random_secret_key()
    except ImportError:
        # Fallback if Django not installed
        import secrets
        import string
        chars = string.ascii_letters + string.digits + string.punctuation
        return ''.join(secrets.choice(chars) for _ in range(50))

def prompt_section(title):
    """Print section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def prompt_input(question, default=None, required=False):
    """Prompt user for input"""
    if default:
        prompt_text = f"{question} [{default}]: "
    else:
        prompt_text = f"{question}: "
    
    while True:
        answer = input(prompt_text).strip()
        
        if not answer:
            if default:
                return default
            elif required:
                print("  ⚠️  This field is required")
                continue
            else:
                return ""
        return answer

def confirm(question):
    """Prompt user for yes/no confirmation"""
    while True:
        answer = input(f"{question} (yes/no): ").strip().lower()
        if answer in ['yes', 'y']:
            return True
        elif answer in ['no', 'n']:
            return False
        else:
            print("  Please enter 'yes' or 'no'")

def main():
    print("\n" + "="*70)
    print("   ENV CONFIGURATION GENERATOR")
    print("   M-Pesa Payment Integration - Charlady Platform")
    print("="*70)
    
    env_dict = {}
    
    # ========================================================================
    # DJANGO CONFIGURATION
    # ========================================================================
    prompt_section("1. DJANGO CONFIGURATION")
    
    print("\nGenerating Django secret key...")
    secret_key = generate_secret_key()
    print(f"✓ Secret key generated")
    env_dict['SECRET_KEY'] = secret_key
    
    use_production = confirm("\nAre you setting up for production?")
    env_dict['DEBUG'] = 'False' if use_production else 'True'
    
    if use_production:
        print("\nEnter your domain (e.g., charlady.co.ke):")
        domain = prompt_input("Domain", default="charlady.co.ke", required=True)
        env_dict['ALLOWED_HOSTS'] = f"{domain},www.{domain}"
        env_dict['ENVIRONMENT'] = 'production'
    else:
        env_dict['ALLOWED_HOSTS'] = '127.0.0.1,localhost'
        env_dict['ENVIRONMENT'] = 'development'
    
    # ========================================================================
    # DATABASE CONFIGURATION
    # ========================================================================
    prompt_section("2. DATABASE CONFIGURATION (PostgreSQL)")
    
    print("\nDatabase connection options:")
    print("1. Local PostgreSQL (recommended for development)")
    print("2. Remote PostgreSQL (production)")
    print("3. Use DATABASE_URL (if you have it)")
    
    db_option = prompt_input("Select option", default="1")
    
    if db_option == "1":
        print("\nLocal PostgreSQL Setup:")
        print("  Host: localhost")
        print("  Port: 5432 (default)")
        db_user = prompt_input("Database user", default="charlady", required=True)
        db_password = prompt_input("Database password", required=True)
        db_name = prompt_input("Database name", default="charlady_db", required=True)
        db_host = "localhost"
        db_port = "5432"
    elif db_option == "2":
        print("\nRemote PostgreSQL Setup:")
        db_host = prompt_input("Database host", required=True)
        db_port = prompt_input("Database port", default="5432")
        db_user = prompt_input("Database user", required=True)
        db_password = prompt_input("Database password", required=True)
        db_name = prompt_input("Database name", required=True)
    else:
        db_url = prompt_input("DATABASE_URL", required=True)
        env_dict['DATABASE_URL'] = db_url
        db_user = db_password = db_name = db_host = db_port = None
    
    if db_user:
        env_dict['DATABASE_URL'] = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    # ========================================================================
    # REDIS CONFIGURATION
    # ========================================================================
    prompt_section("3. REDIS CONFIGURATION (for Celery)")
    
    print("\nRedis options:")
    print("1. Local Redis (localhost:6379)")
    print("2. Remote Redis (e.g., Redis Cloud)")
    
    redis_option = prompt_input("Select option", default="1")
    
    if redis_option == "1":
        redis_url = "redis://localhost:6379/0"
    else:
        redis_host = prompt_input("Redis host", required=True)
        redis_password = prompt_input("Redis password (if any)")
        redis_port = prompt_input("Redis port", default="6379")
        redis_db = prompt_input("Redis database", default="0")
        
        if redis_password:
            redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        else:
            redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
    
    env_dict['REDIS_URL'] = redis_url
    env_dict['CELERY_BROKER_URL'] = redis_url
    env_dict['CELERY_RESULT_BACKEND'] = redis_url
    
    # ========================================================================
    # M-PESA SANDBOX CONFIGURATION
    # ========================================================================
    prompt_section("4. M-PESA SANDBOX CONFIGURATION")
    
    print("\nM-Pesa sandbox credentials (from https://developer.safaricom.co.ke/)")
    print("\nPre-filled values from previous implementation:")
    print(f"  Short Code: 4564139")
    print(f"  Environment: sandbox (for testing)")
    
    env_dict['MPESA_ENVIRONMENT'] = 'sandbox'
    env_dict['MPESA_SHORT_CODE_SANDBOX'] = '4564139'
    env_dict['MPESA_CONSUMER_KEY_SANDBOX'] = 'DU68PrjYY2nEYvXA5Eq2GyoL4c7LQwN8i8X01aGyRQp6zGjD'
    
    consumer_secret = prompt_input("\nM-Pesa Consumer Secret (sandbox)", required=True)
    env_dict['MPESA_CONSUMER_SECRET_SANDBOX'] = consumer_secret
    
    passkey = prompt_input("M-Pesa Passkey (sandbox)", 
                          default="bfb279f9ba9b9d8c25f1c0e1c5f54987b51e1dd45e2c6c0e4f4f8c1f8f9b9e8c")
    env_dict['MPESA_PASSKEY_SANDBOX'] = passkey
    
    env_dict['MPESA_BUSINESS_TYPE_SANDBOX'] = 'DefaultAccount'
    env_dict['MPESA_API_ENDPOINT_SANDBOX'] = 'https://sandbox.safaricom.co.ke'
    
    # ========================================================================
    # M-PESA CALLBACK URL
    # ========================================================================
    prompt_section("5. M-PESA CALLBACK CONFIGURATION")
    
    if use_production:
        callback_url = prompt_input("Callback URL (production)", 
                                   default="https://charlady.co.ke/payments/mpesa-callback/",
                                   required=True)
    else:
        print("\nFor local testing, callback can be set up with ngrok:")
        print("  1. Run: ngrok http 8000")
        print("  2. Use generated URL: https://xxxx.ngrok.io/payments/mpesa-callback/")
        callback_url = prompt_input("Callback URL", 
                                   default="http://localhost:8000/payments/mpesa-callback/")
    
    env_dict['MPESA_CALLBACK_URL'] = callback_url
    env_dict['PAYMENT_TIMEOUT_MINUTES'] = '5'
    
    # ========================================================================
    # CELERY CONFIGURATION
    # ========================================================================
    prompt_section("6. CELERY CONFIGURATION")
    
    print("\nCelery settings (production-ready defaults):")
    env_dict['CELERY_TIMEZONE'] = 'Africa/Nairobi'
    env_dict['CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP'] = 'True'
    env_dict['CELERY_TASK_TIME_LIMIT'] = '1800'
    env_dict['CELERY_TASK_SOFT_TIME_LIMIT'] = '1500'
    env_dict['CELERY_RESULT_EXPIRES'] = '3600'
    
    print("✓ Celery configured for Africa/Nairobi timezone")
    
    # ========================================================================
    # EMAIL CONFIGURATION
    # ========================================================================
    prompt_section("7. EMAIL CONFIGURATION (Optional)")
    
    setup_email = confirm("\nDo you want to configure email now?")
    
    if setup_email:
        print("\nEmail provider options:")
        print("1. Gmail (recommended)")
        print("2. Custom SMTP")
        print("3. Django console backend (development)")
        
        email_option = prompt_input("Select option", default="3")
        
        if email_option == "1":
            env_dict['EMAIL_BACKEND'] = 'django.core.mail.backends.smtp.EmailBackend'
            env_dict['EMAIL_HOST'] = 'smtp.gmail.com'
            env_dict['EMAIL_PORT'] = '587'
            email_user = prompt_input("Gmail address", required=True)
            email_password = prompt_input("Gmail App Password (NOT your main password!)", required=True)
            env_dict['EMAIL_HOST_USER'] = email_user
            env_dict['EMAIL_HOST_PASSWORD'] = email_password
            env_dict['EMAIL_USE_TLS'] = 'True'
        elif email_option == "2":
            env_dict['EMAIL_BACKEND'] = 'django.core.mail.backends.smtp.EmailBackend'
            env_dict['EMAIL_HOST'] = prompt_input("SMTP Host", required=True)
            env_dict['EMAIL_PORT'] = prompt_input("SMTP Port", default="587")
            env_dict['EMAIL_HOST_USER'] = prompt_input("SMTP Username", required=True)
            env_dict['EMAIL_HOST_PASSWORD'] = prompt_input("SMTP Password", required=True)
            env_dict['EMAIL_USE_TLS'] = confirm("Use TLS?") and 'True' or 'False'
        else:
            env_dict['EMAIL_BACKEND'] = 'django.core.mail.backends.console.EmailBackend'
        
        env_dict['DEFAULT_FROM_EMAIL'] = prompt_input("From email", default="noreply@charlady.co.ke")
    else:
        print("\n⚠️  Email notifications disabled (development mode)")
        env_dict['EMAIL_BACKEND'] = 'django.core.mail.backends.console.EmailBackend'
    
    # ========================================================================
    # PAYMENT CONFIGURATION
    # ========================================================================
    prompt_section("8. PAYMENT CONFIGURATION")
    
    print("\nPayment plan settings (pre-configured):")
    env_dict['CURRENCY'] = 'KES'
    env_dict['VERIFICATION_BADGE_COST'] = '250'
    env_dict['VERIFICATION_BADGE_VALIDITY_DAYS'] = '365'
    env_dict['MONTHLY_CONTRIBUTION_PERCENTAGE'] = '3'
    env_dict['MONTHLY_CONTRIBUTION_MINIMUM'] = '100'
    
    print("✓ Verification badge: 250 KES (valid 365 days)")
    print("✓ Monthly contribution: 3% of salary (minimum 100 KES)")
    
    # ========================================================================
    # FEATURE FLAGS
    # ========================================================================
    prompt_section("9. FEATURE FLAGS")
    
    print("\nEnable these features:")
    env_dict['ENABLE_MPESA_PAYMENTS'] = 'True'
    env_dict['ENABLE_WORKER_VERIFICATION'] = 'True'
    env_dict['ENABLE_MONTHLY_CONTRIBUTIONS'] = 'True'
    env_dict['ENABLE_ADMIN_DASHBOARD'] = 'True'
    
    print("✓ All payment features enabled")
    
    # ========================================================================
    # SECURITY SETTINGS
    # ========================================================================
    if use_production:
        prompt_section("10. SECURITY SETTINGS (Production)")
        
        env_dict['SECURE_SSL_REDIRECT'] = 'True'
        env_dict['SESSION_COOKIE_SECURE'] = 'True'
        env_dict['CSRF_COOKIE_SECURE'] = 'True'
        env_dict['SECURE_HSTS_SECONDS'] = '31536000'
        env_dict['SECURE_HSTS_INCLUDE_SUBDOMAINS'] = 'True'
        env_dict['SECURE_HSTS_PRELOAD'] = 'True'
        
        print("✓ HTTPS enforcement enabled")
        print("✓ Security headers configured")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    prompt_section("CONFIGURATION SUMMARY")
    
    print("\n✓ Django Configuration:")
    print(f"  - Environment: {env_dict['ENVIRONMENT']}")
    print(f"  - Debug: {env_dict['DEBUG']}")
    print(f"  - Hosts: {env_dict['ALLOWED_HOSTS'][:40]}...")
    
    print("\n✓ Database:")
    print(f"  - URL: {env_dict.get('DATABASE_URL', '').split('@')[1] if '@' in env_dict.get('DATABASE_URL', '') else 'configured'}...")
    
    print("\n✓ Redis/Celery:")
    print(f"  - URL: {env_dict.get('REDIS_URL', '').split('@')[1] if '@' in env_dict.get('REDIS_URL', '') else 'configured'}")
    
    print("\n✓ M-Pesa:")
    print(f"  - Environment: {env_dict['MPESA_ENVIRONMENT']}")
    print(f"  - Callback URL: {env_dict['MPESA_CALLBACK_URL'][:40]}...")
    
    # ========================================================================
    # WRITE .ENV FILE
    # ========================================================================
    prompt_section("WRITING CONFIGURATION")
    
    env_path = Path('.env')
    
    if env_path.exists():
        overwrite = confirm(f"\n.env file already exists. Overwrite?")
        if not overwrite:
            print("\n⚠️  .env file not modified")
            return
    
    # Write .env file
    with open(env_path, 'w') as f:
        f.write("# ============================================================================\n")
        f.write("# ENVIRONMENT CONFIGURATION - AUTO-GENERATED\n")
        f.write(f"# Generated: {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("# ============================================================================\n\n")
        
        current_section = None
        section_map = {
            'DEBUG': 'DJANGO CONFIGURATION',
            'DATABASE_URL': 'DATABASE CONFIGURATION',
            'REDIS_URL': 'REDIS & CELERY',
            'MPESA_ENVIRONMENT': 'M-PESA CONFIGURATION',
            'EMAIL_BACKEND': 'EMAIL CONFIGURATION',
            'CURRENCY': 'PAYMENT CONFIGURATION',
            'ENABLE_MPESA_PAYMENTS': 'FEATURE FLAGS',
            'SECURE_SSL_REDIRECT': 'SECURITY SETTINGS',
        }
        
        for key, value in sorted(env_dict.items()):
            section = section_map.get(key)
            if section and section != current_section:
                f.write(f"\n# {section}\n")
                f.write("# " + "="*70 + "\n")
                current_section = section
            
            f.write(f"{key}={value}\n")
    
    print(f"\n✓ .env file created: {env_path.absolute()}")
    
    # ========================================================================
    # NEXT STEPS
    # ========================================================================
    prompt_section("NEXT STEPS")
    
    print("\n1. Verify configuration:")
    print("   python manage.py check")
    
    print("\n2. Test database connection:")
    print("   python manage.py dbshell")
    
    print("\n3. Test M-Pesa connection:")
    print("   python manage.py shell")
    print("   >>> from payments.mpesa_service import get_mpesa_client")
    print("   >>> client.authenticate()")
    
    print("\n4. Run migrations:")
    print("   python manage.py migrate")
    
    print("\n5. Start services:")
    print("   python manage.py runserver")
    print("   celery -A housekeeper_connect worker --loglevel=info")
    print("   celery -A housekeeper_connect beat --loglevel=info")
    
    print("\n✅ Configuration complete!\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Configuration cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
