# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""A pluggable Django application to manage a financial portfolio."""

__author__ = "Mischback"
"""The current project owner."""

__app_name__ = "django-stockings"
"""The name of the application."""

__version__ = "1.0.0"
"""The current version."""

default_app_config = "stockings.apps.StockingsConfig"
"""The path to the app's default configuration class.

Consider this *legacy code*. See
:djangoapi:`Django's documentation<applications/#configuring-applications>` for
details.
"""
