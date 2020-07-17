"""Provides utilities for testing and running the development server."""

# Django imports
from django.conf import settings


def callback_show_debug_toolbar(request):
    """Return ``settings.DEBUG`` to control debug_toolbar."""
    return settings.DEBUG
