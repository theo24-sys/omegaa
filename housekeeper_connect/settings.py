import os
import sys
from pathlib import Path
import dj_database_url
from dotenv import load_dotenv

# ─── Paths & Env ────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent.parent

# Load .env file (only once!)
load_dotenv(BASE_DIR / '.env')

# ─── Core Settings ──────────────────────────────────────────────────────────────
SECRET_KEY = os.getenv('SECRET_KEY')

DEBUG = os.getenv('DEBUG', 'True') == 'True'  # Default True for local, set False in Railway vars

ALLOWED_HOSTS = [
    'charlady.co.ke',
    'www.charlady.co.ke',
    'charlady.online',
    'www.charlady.online',
    'omega-production-734f.up.railway.app',
    'localhost',
    '127.0.0.1',
]

# Add Railway dynamic preview/deploy domain if present
railway_domain = os.getenv('RAILWAY_PUBLIC_DOMAIN')
if railway_domain:
    ALLOWED_HOSTS.append(railway_domain)

# Add Render dynamic domain if present
render_domain = os.getenv('RENDER_EXTERNAL_HOSTNAME')
if render_domain:
    ALLOWED_HOSTS.append(render_domain)

CSRF_TRUSTED_ORIGINS = [
    'https://charlady.co.ke',
    'https://www.charlady.co.ke',
    'https://charlady.online',
    'https://www.charlady.online',
    'https://omega-production-734f.up.railway.app',
]
if railway_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{railway_domain}')
if render_domain:
    CSRF_TRUSTED_ORIGINS.append(f'https://{render_domain}')

APPEND_SLASH = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT     = False   # Important — Railway handles SSL

# ─── Email Configuration ────────────────────────────────────────────────────────
if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

    EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'  # usually False with port 587

    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
    EMAIL_TIMEOUT = int(os.getenv('EMAIL_TIMEOUT', '10'))

    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

    # Gmail-specific reminder (must use App Password, not normal password!)
    # 1. Enable 2FA on Google account
    # 2. Go to https://myaccount.google.com/apppasswords
    # 3. Generate → use the 16-char code as EMAIL_HOST_PASSWORD

# ─── Database ───────────────────────────────────────────────────────────────────
DATABASES = {
    'default': dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",  # local fallback
        conn_max_age=600,
        conn_health_checks=True,
    )
}

# Override for tests
if 'test' in sys.argv:
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'test_db.sqlite3',
    }

# ─── Applications & Middleware ──────────────────────────────────────────────────
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_tailwind',
    'accounts',
    'jobs',
    'dashboard',
    'notifications',
    'reviews',
    'payments',
    'blog',
    'courses',
    'chat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'housekeeper_connect.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'housekeeper_connect.wsgi.application'

# ─── Auth & Passwords ───────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

AUTH_USER_MODEL = 'accounts.CustomUser'
AUTHENTICATION_BACKENDS = [
    'accounts.backends.PhoneNumberBackend',
    'django.contrib.auth.backends.ModelBackend',
]

LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'home'

# ─── Internationalization ───────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Nairobi'
USE_I18N = True
USE_TZ = True

# ─── Static & Media ─────────────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

# AWS S3 Settings (provided by user)
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.getenv('AWS_S3_ENDPOINT_URL')
AWS_S3_CUSTOM_DOMAIN = os.getenv('AWS_S3_CUSTOM_DOMAIN')
AWS_S3_REGION_NAME = os.getenv('AWS_S3_REGION_NAME', 'eu-central-1')

# Storage Configuration (Django 4.2+ pattern)
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "region_name": AWS_S3_REGION_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "custom_domain": AWS_S3_CUSTOM_DOMAIN,
            "location": os.getenv('AWS_S3_LOCATION', 'media'),
            "file_overwrite": False,
        },
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

AWS_S3_LOCATION = os.getenv('AWS_S3_LOCATION', 'media')
if not AWS_ACCESS_KEY_ID:
    STORAGES["default"]["BACKEND"] = "django.core.files.storage.FileSystemStorage"
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
else:
    # Use the custom domain if available, otherwise fallback to endpoint/bucket pattern
    if AWS_S3_CUSTOM_DOMAIN:
        MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/{AWS_S3_LOCATION}/'
    else:
        # Construct path-style URL for R2 or S3
        MEDIA_URL = f'{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/{AWS_S3_LOCATION}/'

# ─── Crispy Forms ───────────────────────────────────────────────────────────────
CRISPY_ALLOWED_TEMPLATE_PACKS = "tailwind"
CRISPY_TEMPLATE_PACK = "tailwind"

# ─── Security (Railway-specific – good setup!) ──────────────────────────────────
SECURE_SSL_REDIRECT = False  # Railway handles SSL → do NOT enable
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_USE_SESSIONS = True  # Helps with proxy issues

SECURE_HSTS_SECONDS = 31536000 if not DEBUG else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS = not DEBUG
SECURE_HSTS_PRELOAD = not DEBUG

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# ─── M-Pesa ─────────────────────────────────────────────────────────────────────
MPESA_TILL_NUMBER = os.getenv('MPESA_TILL_NUMBER', '4567052')

# API Credentials (Must be set in Render environment variables)
# SECURITY: Do NOT use hardcoded defaults for production credentials
if not DEBUG:
    if not os.getenv('MPESA_CONSUMER_KEY'):
        raise ValueError("MPESA_CONSUMER_KEY must be set in production environment")
    if not os.getenv('MPESA_CONSUMER_SECRET'):
        raise ValueError("MPESA_CONSUMER_SECRET must be set in production environment")
    if not os.getenv('MPESA_PASSKEY'):
        raise ValueError("MPESA_PASSKEY must be set in production environment")

MPESA_CONSUMER_KEY = os.getenv('MPESA_CONSUMER_KEY', '')
MPESA_CONSUMER_SECRET = os.getenv('MPESA_CONSUMER_SECRET', '')
MPESA_PASSKEY = os.getenv('MPESA_PASSKEY', '')
MPESA_SHORT_CODE = os.getenv('MPESA_SHORT_CODE', '')
MPESA_ENVIRONMENT = os.getenv('MPESA_ENVIRONMENT', 'sandbox' if DEBUG else 'production')
JOB_POSTING_FEE = 250
MPESA_TRANSACTION_TYPE = os.getenv('MPESA_TRANSACTION_TYPE', 'CustomerBuyGoodsOnline')

# Callback URL for Safaricom to send payment results
MPESA_CALLBACK_URL = os.getenv('MPESA_CALLBACK_URL', 'https://charlady.co.ke/payments/mpesa/callback/')
DIDIT_WEBHOOK_SECRET = os.getenv('DIDIT_WEBHOOK_SECRET', '')

# ─── Africa's Talking (SMS) ──────────────────────────────────────────────────
AFRICASTALKING_USERNAME = os.getenv('AFRICASTALKING_USERNAME', 'sandbox')
AFRICASTALKING_API_KEY = os.getenv('AFRICASTALKING_API_KEY', '')

# ─── Jazzmin Admin Theme ────────────────────────────────────────────────────────
JAZZMIN_SETTINGS = {
    "site_title": "Charlady Admin",
    "site_header": "Charlady",
    "site_brand": "Charlady Admin",
    "site_logo": "img/logo.png",
    "login_logo": "img/logo.png",
    "site_logo_classes": "img-circle",
    "welcome_sign": "Welcome to Charlady Admin",
    "copyright": "Charlady – Trusted • Verified • Connected",
    "search_model": ["accounts.CustomUser", "jobs.Job", "reviews.Review"],
    "topmenu_links": [
        {"name": "Dashboard", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "View site", "url": "/", "new_window": True},
    ],
    "usermenu_links": [
        {"name": "View site", "url": "/", "new_window": True},
    ],
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.Group": "fas fa-users",
        "accounts": "fas fa-user-friends",
        "accounts.CustomUser": "fas fa-user",
        "jobs": "fas fa-briefcase",
        "jobs.Job": "fas fa-briefcase",
        "jobs.Application": "fas fa-file-alt",
        "reviews": "fas fa-star",
        "reviews.Review": "fas fa-star",
        "notifications": "fas fa-bell",
        "notifications.Notification": "fas fa-bell",
        "payments": "fas fa-credit-card",
        "blog": "fas fa-newspaper",
    },
    "show_sidebar": True,
    "navigation_expanded": True,
    "changeform_format": "horizontal_tabs",
    "show_ui_builder": False,
    "custom_css": "css/jazzmin_theme.css",
    "custom_js": None,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "sidebar_nav_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-dark",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": True,
    "sidebar_fixed": True,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_accordion": True,
    "theme": "flatly",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'