import os
import secrets
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
from django.core.exceptions import ImproperlyConfigured

DEPLOYMENT_ENV = os.environ.get('DJANGO_ENV', 'development').strip().lower()
DEBUG = False if DEPLOYMENT_ENV == 'production' else os.environ.get('DJANGO_DEBUG', '0') == '1'
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    if DEPLOYMENT_ENV == 'production':
        raise ImproperlyConfigured('DJANGO_SECRET_KEY must be configured outside local development.')
    SECRET_KEY = secrets.token_urlsafe(50)
ALLOWED_HOSTS = [host.strip() for host in os.environ.get('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if host.strip()]
if DEPLOYMENT_ENV == 'production' and ('DJANGO_ALLOWED_HOSTS' not in os.environ or not ALLOWED_HOSTS or '*' in ALLOWED_HOSTS):
    raise ImproperlyConfigured('Production requires explicit DJANGO_ALLOWED_HOSTS entries.')
INSTALLED_APPS = [
    'django.contrib.admin', 'django.contrib.auth', 'django.contrib.contenttypes',
    'django.contrib.sessions', 'django.contrib.messages', 'django.contrib.staticfiles',
    'django_otp', 'django_otp.plugins.otp_totp',
    'accounts', 'content', 'practice', 'calculations', 'planning', 'learning', 'discovery', 'notepad', 'billing',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware', 'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware', 'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware', 'django_otp.middleware.OTPMiddleware', 'config.middleware.StaffWithoutOTPMiddleware', 'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages', 'billing.context.strip']}}]
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'
DATABASES = {'default': {'ENGINE':'django.db.backends.postgresql','NAME':os.environ.get('MALILAB_DB_NAME','malilab'),'USER':os.environ.get('MALILAB_DB_USER','malilab_app'),'HOST':os.environ.get('MALILAB_DB_HOST','127.0.0.1'),'PORT':os.environ.get('MALILAB_DB_PORT','5432'),'CONN_MAX_AGE':60}}
AUTH_USER_MODEL = 'accounts.UserAccount'
AUTHENTICATION_BACKENDS = ['accounts.backends.NormalizedEmailBackend']
AUTH_PASSWORD_VALIDATORS = [
 {'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
 {'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator'},
 {'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},
 {'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE='en-us'; TIME_ZONE='UTC'; USE_I18N=True; USE_TZ=True
STATIC_URL='static/'
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'

STATIC_ROOT = '/var/www/malilab_app/static'

# --- 6B.11 production hardening (inert unless DJANGO_ENV=production) -----------------------------
if DEPLOYMENT_ENV == 'production':
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SSL_REDIRECT', '1') == '1'
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '3600'))   # raise to 31536000 once HTTPS is proven
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = 'same-origin'
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()]
    if os.environ.get('DJANGO_BEHIND_PROXY') == '1':   # only when nginx sets X-Forwarded-Proto and the app is NOT reachable directly
        SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# --- 6B.12 account email (Gmail SMTP). Secrets come from the environment file, never from code. ---
SITE_URL = os.environ.get('DJANGO_SITE_URL', '').rstrip('/')   # e.g. https://malilab.online
EMAIL_HOST = os.environ.get('DJANGO_EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('DJANGO_EMAIL_PORT', '587'))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('DJANGO_EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('DJANGO_EMAIL_HOST_PASSWORD', '')
EMAIL_TIMEOUT = 10
DEFAULT_FROM_EMAIL = os.environ.get('DJANGO_DEFAULT_FROM_EMAIL', 'MaliLab <malilabsetup@gmail.com>')
# Without a password the app writes emails to its log instead of sending (safe for local work).
EMAIL_BACKEND = ('django.core.mail.backends.smtp.EmailBackend' if EMAIL_HOST_PASSWORD
                 else 'django.core.mail.backends.console.EmailBackend')
PASSWORD_RESET_TIMEOUT = 60 * 60   # password reset links work for one hour

# --- patch 14: staff sign in with a password only; long-lived sessions ---------------------------------
# Set MALILAB_STAFF_OTP=1 in the environment file to ask for the authenticator code again.
STAFF_OTP_REQUIRED = os.environ.get('MALILAB_STAFF_OTP', '0') == '1'
SESSION_COOKIE_AGE = 60 * 60 * 24 * 365      # stay signed in for a year, renewed every time the site is used
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True


# --- patch 25: payments (M-Pesa) -----------------------------------------------------------------------
# MALILAB_PAYWALL=1 locks modules until bought. Leave it off while testing the sandbox.
MALILAB_PAYWALL = os.environ.get('MALILAB_PAYWALL', '0') == '1' and 'test' not in __import__('sys').argv
MALILAB_ALL_COVERS_FUTURE = os.environ.get('MALILAB_ALL_COVERS_FUTURE', '1') == '1'
MALILAB_PAY_PROVIDERS = [p.strip() for p in os.environ.get('MALILAB_PAY_PROVIDERS', 'mpesa').split(',') if p.strip()]
MPESA_ENV = os.environ.get('MPESA_ENV', 'sandbox')
MPESA_CONSUMER_KEY = os.environ.get('MPESA_CONSUMER_KEY', '')
MPESA_CONSUMER_SECRET = os.environ.get('MPESA_CONSUMER_SECRET', '')
MPESA_SHORTCODE = os.environ.get('MPESA_SHORTCODE', '174379')
MPESA_PASSKEY = os.environ.get('MPESA_PASSKEY', '')
MPESA_CALLBACK_SECRET = os.environ.get('MPESA_CALLBACK_SECRET', '')
MPESA_CALLBACK_BASE = os.environ.get('MPESA_CALLBACK_BASE', 'https://malilab.online')
MPESA_TRANSACTION_TYPE = os.environ.get('MPESA_TRANSACTION_TYPE', 'CustomerPayBillOnline')
