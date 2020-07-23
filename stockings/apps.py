"""Contains the application configuration, as required by Django."""

# Django imports
from django.apps import AppConfig
from django.core.checks import register as register_check
from django.db.models.signals import post_save  # noqa: F401

# app imports
from stockings.checks import (
    check_use_django_auth_permissions,
    check_use_django_auth_permissions_requires_django_contrib_auth,
)


class StockingsConfig(AppConfig):
    """Application-specific configuration class, which is required by Django.

    This sub-class of Django's `AppConfig` provides application-specific
    information to be used in Django's application registry (see
    :djangoapi:`applications/#configuring-applications`).
    """

    name = "stockings"
    verbose_name = "Stockings"

    def ready(self):
        """Apply app-specific stuff.

        Notes
        -----
        This method is executed, when the application is (completely) loaded.

        It registers the app-specific contribution to Django's check framework
        (see :djangoapi:`checks/` and :mod:`stockings.checks`).
        """
        # register check functions
        register_check(check_use_django_auth_permissions)
        register_check(check_use_django_auth_permissions_requires_django_contrib_auth)
