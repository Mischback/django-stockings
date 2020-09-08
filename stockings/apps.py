"""Contains the application configuration, as required by Django."""

# Python imports
import logging

# Django imports
from django.apps import AppConfig
from django.conf import settings
from django.core.checks import register as register_check
from django.db.models.signals import post_save  # noqa: F401

# get a module-level logger
logger = logging.getLogger(__name__)


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

        It performs the following actions:

        - ensures, that app-specific settings are available in the project's
          settings
        - registers the app-specific contribution to Django's check framework
          (see :djangoapi:`checks/` and :mod:`stockings.checks`).
        """
        # delay app imports until now, to make sure everything else is ready
        from stockings import settings as app_default_settings
        from stockings.checks import (
            check_to_percent_precision_is_int,
            check_use_django_auth_permissions,
            check_use_django_auth_permissions_requires_django_contrib_auth,
        )
        from stockings.models.stockitemprice import StockItemPrice
        from stockings.signals.handlers import price_information_changed

        # inject app-specific settings
        # see https://stackoverflow.com/a/47154840
        for name in dir(app_default_settings):
            if name.isupper() and not hasattr(settings, name):
                value = getattr(app_default_settings, name)
                logger.info("Injecting setting {} with value {}".format(name, value))
                setattr(settings, name, value)

        # register check functions
        register_check(check_use_django_auth_permissions)
        register_check(check_use_django_auth_permissions_requires_django_contrib_auth)
        register_check(check_to_percent_precision_is_int)

        # connect signal handlers
        post_save.connect(
            price_information_changed,
            sender=StockItemPrice,
            dispatch_uid="stockitemprice.post_save",
        )
