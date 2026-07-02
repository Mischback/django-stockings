# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Application configuration as required by Django."""

# Django imports
from django.apps import AppConfig
from django.core.checks import Tags, register


class StockingsConfig(AppConfig):
    """Application-specific configuration class, as required by Django.

    As of now, this doesn't really do anything and just provides meta
    information.
    """

    name = "stockings"
    verbose_name = "Stockings"

    def ready(self):
        """Apply app-specific stuff."""
        # app imports
        from stockings.checks import check_timezone_awareness

        register(Tags.compatibility)(check_timezone_awareness)
