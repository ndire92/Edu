"""
Django settings for Gestion_EducMNIE project.
"""

from pathlib import Path
import os
from decouple import config


# ==============================
# BASE DIR
# ==============================
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================
# SECURITY
# ==============================
SECRET_KEY = 'django-insecure-6u3=j@exr%yub^wxq=^1qsqdw3=_b+fv@xax^gh-5#3360bw)h'

DEBUG = True

ALLOWED_HOSTS = []  # En production : ['127.0.0.1', 'tondomaine.com']


# ==============================
# APPLICATIONS
# ==============================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Apps locales
   'dashboard.apps.DashboardConfig',
 


    # Apps tierces
    'tinymce',
]

SITE_URL = "http://127.0.0.1:8000"
# ==============================
# MIDDLEWARE
# ==============================
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


# ==============================
# URLS / WSGI
# ==============================
ROOT_URLCONF = 'Gestion_EducMNIE.urls'

WSGI_APPLICATION = 'Gestion_EducMNIE.wsgi.application'


# ==============================
# TEMPLATES
# ==============================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',  # <-- IMPORTANT
        ],
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


# ==============================
# DATABASE
# ==============================
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# ==============================
# AUTH USER
# ==============================
AUTH_USER_MODEL = "dashboard.CustomUser"


# ==============================
# PASSWORD VALIDATION
# ==============================
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ==============================
# INTERNATIONALIZATION
# ==============================
LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'UTC'

USE_I18N = True
USE_TZ = True


# ==============================
# STATIC FILES
# ==============================
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',  # fichiers CSS/JS en dev
]

STATIC_ROOT = BASE_DIR / 'staticfiles'  # collectstatic (prod)


# ==============================
# MEDIA FILES
# ==============================
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


# ==============================
# TINYMCE CONFIG
# ==============================
TINYMCE_DEFAULT_CONFIG = {
    'height': 400,
    'width': '100%',
    'menubar': False,
    'statusbar': False,
    'branding': False,
    'resize': True,
    'language': 'fr',
    'plugins': [
        'link image media lists code table preview'
    ],
    'toolbar': (
        'undo redo | bold italic underline | '
        'forecolor backcolor | alignleft aligncenter alignright | '
        'bullist numlist | link image media | code preview'
    ),
    'content_style': """
        body {
            font-family: 'Inter', sans-serif;
            font-size: 16px;
            line-height: 1.6;
        }
    """,
}

# ==============================
# DEFAULT PRIMARY KEY
# ==============================
# EMAIL CONFIG (GMAIL)
# ==============================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

EMAIL_HOST_USER = config('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

