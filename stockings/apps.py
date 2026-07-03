# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Application configuration as required by Django."""

# Python imports
import logging

# Django imports
from django.apps import AppConfig
from django.conf import settings
from django.core.checks import Tags, register

logger = logging.getLogger(__name__)


class StockingsConfig(AppConfig):
    """Application-specific configuration class, as required by Django.

    As of now, this doesn't really do anything and just provides meta
    information.
    """

    name = "stockings"
    verbose_name = "Stockings"

    def ready(self):
        """Apply app-specific stuff."""
        # delay app imports until now, to make sure everything else is ready
        # app imports
        from stockings import settings as app_default_settings
        from stockings.checks import check_timezone_awareness

        # inject app-specific settings
        # see https://stackoverflow.com/a/47154840
        for name in dir(app_default_settings):
            if name.isupper() and not hasattr(settings, name):
                value = getattr(app_default_settings, name)
                logger.info("Injecting setting {} with value {}".format(name, value))
                setattr(settings, name, value)

        register(Tags.compatibility)(check_timezone_awareness)
