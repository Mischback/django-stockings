# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Provide app-specific checks for application."""

# Django imports
from django.conf import settings
from django.core.checks import Error


def check_timezone_awareness(app_configs, **kwargs):  # noqa: D103
    errors = []

    if not getattr(settings, "USE_TZ", False):
        errors.append(
            Error(
                "USE_TZ is set to False or missing in the project's settings",
                hint="django-stockings requires 'USE_TZ = True' to maintain data integrity",
                id="stockings.E001",
            )
        )

    return errors
