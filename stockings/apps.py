"""Contains the application configuration, as required by Django."""

# Django imports
from django.apps import AppConfig
from django.db.models.signals import post_save  # noqa: F401


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

        As of now, this method does not execute anything. Anyhow, it is
        considered best practice to use this method to connect signal handlers,
        which might be needed.
        """
        pass
