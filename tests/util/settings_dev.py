"""Contains minimum settings to run the development of the app in a tox-based
environment."""

# Python imports
import os
import sys

# Path to the test directory
TEST_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Path to the project root
PROJECT_ROOT = os.path.dirname(TEST_ROOT)

# Add PROJECT_ROOT to Python path
sys.path.append(os.path.normpath(PROJECT_ROOT))

# Allow all hosts during development
ALLOWED_HOSTS = ['*']

# Database configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(TEST_ROOT, 'test.sqlite'),
    }
}

# Enable Django's DEBUG mode
DEBUG = True

# Provide a minimal Django project as environment
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.messages',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'stockings.apps.StockingsConfig',
]

MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
]

ROOT_URLCONF = 'tests.util.urls_dev'

SECRET_KEY = 'only-for-development'

STATIC_URL = '/static/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(TEST_ROOT, 'utils', 'templates'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                # 'django.template.context_processors.i18n',
                'django.template.context_processors.static',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'dev': {
            'format': '[{levelname}] {name}:{lineno}:{funcName} - {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'dev',
        },
    },
    'loggers': {
        'stockings': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    }
}
