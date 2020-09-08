"""Contains minimum settings to run the development of the app in a tox-based environment."""

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
ALLOWED_HOSTS = ["*"]

# Database configuration
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(TEST_ROOT, "test.sqlite"),
    }
}

# Enable Django's DEBUG mode
DEBUG = True

# Provide a minimal Django project as environment
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "django.contrib.staticfiles",
    "stockings.apps.StockingsConfig",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]

ROOT_URLCONF = "tests.util.urls_dev"

SILENCED_SYSTEM_CHECKS = [
    # As of Django 3.1 this warning informs about an optional configuration
    # requirement for `django.contrib.admin`. This is currently not relevant
    # for development of `django-stockings`.
    "admin.W411"
]

SECRET_KEY = "only-for-development"  # nosec: this is on purpose, just for development

STATIC_URL = "/static/"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(TEST_ROOT, "util", "templates"),],  # noqa: E231
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.contrib.auth.context_processors.auth",
                # 'django.template.context_processors.i18n',
                "django.template.context_processors.static",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]