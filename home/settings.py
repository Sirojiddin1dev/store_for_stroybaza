import os
from pathlib import Path
from datetime import timedelta
from dotenv import load_dotenv

# .env faylini yuklash
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv("SECRET_KEY")

DEBUG = os.getenv("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "*").split(",")

# Application definition
INSTALLED_APPS = [
    'jazzmin',
    "unfold",
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'main.apps.MainConfig',
    'rest_framework',
    'rest_framework_simplejwt',
    'drf_yasg',
    'payment.apps.PaymentsConfig',
    'payme',
    'click_up',
    'corsheaders',
    'whitenoise'
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS Middleware'ni qo'shamiz
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True


ROOT_URLCONF = 'home.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'home.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")
STATIC_ROOT = BASE_DIR / 'static'


# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'main.User'

# REST Framework settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',  # Barcha foydalanuvchilarga ruxsat
    ],
}

# Simple JWT settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=600),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
}

# Swagger settings
SWAGGER_SETTINGS = {
   'SECURITY_DEFINITIONS': {
      'Basic': {
            'type': 'basic'
      },
      'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header'
      }
   }
}

# Authentication backends
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'main.authentication.PhoneNumberBackend',
]

# Eskiz SMS settings
ESKIZ_EMAIL = os.getenv("ESKIZ_EMAIL")
ESKIZ_PASSWORD = os.getenv("ESKIZ_PASSWORD")

# Logging configuration


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'debug.log',
        },
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}


# Payme sozlamalari
PAYME_ID_1 = os.getenv("PAYME_ID_1")
PAYME_ID_2 = os.getenv("PAYME_ID_2")
PAYME_KEYS = {
    "kassa_1": os.getenv("PAYME_KASSA_1"),
    "kassa_2": os.getenv("PAYME_KASSA_2"),
}
PAYME_ONE_TIME_PAYMENT = os.getenv("PAYME_ONE_TIME_PAYMENT", "True") == "True"
PAYME_ACCOUNT_FIELD = "order_id"  # Order modelidagi ID maydoni
PAYME_AMOUNT_FIELD = "total_amount"  # Order modelidagi summa maydoni
PAYME_ACCOUNT_MODEL = "main.models.Order"  # Order modelining to'liq yo'li
PAYME_DISABLE_ADMIN = True


# Click sozlamalari
CLICK_SERVICE_ID = os.getenv("CLICK_SERVICE_ID")
CLICK_MERCHANT_ID = os.getenv("CLICK_MERCHANT_ID")
CLICK_SECRET_KEY = os.getenv("CLICK_SECRET_KEY")
CLICK_DISABLE_ADMIN = True
CLICK_ACCOUNT_MODEL = "main.models.Order"
CLICK_AMOUNT_FIELD = "total_amount"

# AMOCRM sozlamalari
# AMOCRM_CLIENT_ID = os.getenv("AMOCRM_CLIENT_ID")
# AMOCRM_CLIENT_SECRET = os.getenv("AMOCRM_CLIENT_SECRET")
# AMOCRM_REDIRECT_URI = os.getenv("AMOCRM_REDIRECT_URI")

# Frontend URL
FRONTEND_URL = os.getenv("FRONTEND_URL")
