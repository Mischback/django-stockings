# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Application configuration as required by Django."""

# Django imports
from django.apps import AppConfig
from django.core.exceptions import ImproperlyConfigured


class StockingsYFinanceSimpleConfig(AppConfig):
    """Application-specific configuration class, as required by Django."""

    name = "stockings.contrib.provider.yfinance_simple"
    verbose_name = "(Stockings) YFinance Simple"

    def ready(self):
        """Apply app-specific stuff."""
        # Django imports
        from django.apps import apps

        if not apps.is_installed("stockings"):
            raise ImproperlyConfigured(
                "Requires the base application 'stockings' to be installed"
            )
