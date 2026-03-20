from pathlib import Path
from django.contrib import messages

from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

APPEND_SLASH = True

# ======================
# BASIC SETTINGS
# ======================
SECRET_KEY = 'django-insecure-r$rt2)kr3j2(ecpu%^+x_(&2@jfv*a0=lsy(iu3^(jwq$zc&wt'
DEBUG = True
ALLOWED_HOSTS = ['*']

# ======================
# APPLICATIONS
# ======================
INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'buyzoneapp',
    'authcart',
    'delivery',
]

# ======================
# MIDDLEWARE
# ======================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    'delivery.middleware.DeliveryBoyRedirectMiddleware',
    'authcart.middleware.AuthUserRedirectMiddleware',
]

ROOT_URLCONF = 'BuyZone.urls'
WSGI_APPLICATION = 'BuyZone.wsgi.application'
ASGI_APPLICATION = 'BuyZone.asgi.application'
# ======================
# TEMPLATES
# ======================
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

# ======================
# DATABASE
# ======================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ======================
# PASSWORD VALIDATION
# ======================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ======================
# INTERNATIONALIZATION
# ======================
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

# ======================
# EMAIL
# ======================
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'

EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = 'apikey'

EMAIL_HOST_PASSWORD = os.getenv('SENDGRID_API_KEY')

DEFAULT_FROM_EMAIL = 'tauseef.buyzone@outlook.com'

# ======================
# STATIC & MEDIA
# ======================
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# ======================
# MESSAGES
# ======================
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ======================
# PAYMENTS
# ======================
RAZORPAY_KEY_ID = 'rzp_test_RxQBw94fljOG8Y'
RAZORPAY_KEY_SECRET = 'qL14RIxEXO5zC7yAtWo5hqXI'

LOGIN_URL = '/auth/login/'

# ======================
# JAZZMIN – AMAZON STYLE ADMIN UI
# ======================
JAZZMIN_SETTINGS = {

    # Branding
    "site_title": "BuyZone Admin",
    "site_header": "BuyZone",
    "site_brand": "BuyZone",
    "site_logo": "images/logo.png",
    "login_logo": "images/logo.png",
    "site_icon": "images/logo.png",

    "welcome_sign": "Welcome to BuyZone Admin Panel",
    "copyright": "BuyZone",

    # AMAZON LOOK
    "theme": "flatly",
    "dark_mode_theme": "darkly",

    "navbar": "navbar-dark bg-dark",
    "sidebar": "sidebar-dark-primary",
    "brand_colour": "navbar-dark",

    # Yellow accent like Amazon
    "accent": "accent-warning",

    "button_classes": {
        "primary": "btn-warning",
        "secondary": "btn-secondary",
        "success": "btn-success",
        "danger": "btn-danger",
        "info": "btn-info",
        "warning": "btn-warning",
    },

    # Layout
    "sidebar_fixed": True,
    "navbar_fixed": True,
    "footer_fixed": False,
    "sidebar_mini": False,

    # Icons
    "icons": {
        "auth.user": "fas fa-user",
        "auth.Group": "fas fa-users",
        "buyzoneapp.Product": "fas fa-box",
        "buyzoneapp.Orders": "fas fa-shopping-cart",
        "buyzoneapp.OrderUpdate": "fas fa-truck",
        "buyzoneapp.Contact": "fas fa-envelope",
        "buyzoneapp.Size": "fas fa-ruler",
        "buyzoneapp.ProductVariant": "fas fa-tags",
        "buyzoneapp.CancelledPaidOrder": "fas fa-ban",
        "delivery.DeliveryBoy": "fas fa-motorcycle",
        "delivery.DeliveryOTP": "fas fa-key",
        
    },

    # UX
    "related_modal_active": True,
    "changeform_format": "horizontal_tabs",
    "show_ui_builder": False,

    # Custom files (loader here)
    "custom_css": "assets/css/admin_custom.css",
    "custom_js": "assets/js/admin_custom.js",
}