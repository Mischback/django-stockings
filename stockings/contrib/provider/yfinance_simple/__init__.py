# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Provides financial data using ``yfinance`` for the main application."""

__author__ = "Mischback"
"""The current project owner."""

__app_name__ = "django-stockings"
"""The name of the application."""

__version__ = "1.0.0"
"""The current version."""

default_app_config = (
    "stockings.contrib.provider.yfinance_simple.apps.StockingsYFinanceSimpleConfig"
)
"""The path to the app's default configuration class.

Consider this *legacy code*. See
:djangoapi:`Django's documentation<applications/#configuring-applications>` for
details.
"""
