"""Provides app-specific contributions to Django's check framework.

These checks verify the values of app-specific settings and may also perform
logical checks in combination with other project settings.

Notes
-----
The checks are applied / registered in
:meth:`StockingsConfig.ready() <stockings.apps.StockingsConfig.ready>` and
automatically executed by Django (see :djangoapi:`checks/`).
"""

# Python imports
import logging

# Django imports
from django.conf import settings
from django.core.checks import Error
from django.utils.translation import ugettext_lazy as _

# get a module-level logger
logger = logging.getLogger(__name__)


def check_use_django_auth_permissions(app_configs, **kwargs):
    """Verify that STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS is of type bool.

    Parameters
    ----------
    app_configs : list
        A list of applications that should be in inspected (see
        :djangodoc:`topics/checks/#writing-your-own-checks`).

    Returns
    -------
    list
        A list of :djangodoc:`Messages <topics/checks/#messages>`.

    Warnings
    --------
    Please note that, in Python, any non-zero value is considered ``True``,
    while values like ``None``, ``[]``, ``{}`` or ``0`` are considered
    ``False``. The unittests are considering some of these possibilities, but
    not all of them. Actually, no unittest is available, that verifies that the
    error is correctly appended.
    """
    errors = []

    logger.debug("Is STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS of type bool?")
    if not isinstance(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS, bool):
        errors.append(
            Error(
                _("STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS has to be a boolean value!"),
                hint=_(
                    "STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS has to be either True or "
                    "False."
                ),
                id="stockings.e001",
            )
        )

    return errors


def check_use_django_auth_permissions_requires_django_contrib_auth(
    app_configs, **kwargs
):
    """Confirm that the required app is installed.

    If `STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS` is set to ``True``, it is
    obviously required to have ``"django.contrib.auth"`` in
    :setting:`INSTALLED_APPS`.

    Parameters
    ----------
    app_configs : list
        A list of applications that should be in inspected (see
        :djangodoc:`topics/checks/#writing-your-own-checks`).

    Returns
    -------
    list
        A list of :djangodoc:`Messages <topics/checks/#messages>`.

    Warnings
    --------
    Please note that, in Python, any non-zero value is considered ``True``,
    while values like ``None``, ``[]``, ``{}`` or ``0`` are considered
    ``False``. The unittests are considering some of these possibilities, but
    not all of them.
    """
    errors = []

    if settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS:
        logger.debug("Is 'django.contrib.auth' present in INSTALLED_APPS?")
        if "django.contrib.auth" not in settings.INSTALLED_APPS:
            errors.append(
                Error(
                    _("'django.contrib.auth' must be installed!"),
                    hint=_(
                        "STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS is True and thus "
                        "requires 'django.contrib.auth' to be present in "
                        "INSTALLED_APPS."
                    ),
                    id="stockings.e002",
                )
            )

    return errors


def check_to_percent_precision_is_int(app_configs, **kwargs):
    """Verify that STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS is of type int.

    Parameters
    ----------
    app_configs : list
        A list of applications that should be in inspected (see
        :djangodoc:`topics/checks/#writing-your-own-checks`).

    Returns
    -------
    list
        A list of :djangodoc:`Messages <topics/checks/#messages>`.
    """
    errors = []

    logger.debug("Is STOCKINGS_TO_PERCENT_PRECISION of type int and >= 0?")
    if (
        (not isinstance(settings.STOCKINGS_TO_PERCENT_PRECISION, int))
        or (settings.STOCKINGS_TO_PERCENT_PRECISION < 0)
        or (isinstance(settings.STOCKINGS_TO_PERCENT_PRECISION, bool))
    ):
        errors.append(
            Error(
                _("STOCKINGS_TO_PERCENT_PRECISION has to be a positive integer value!"),
                hint=_(
                    "STOCKINGS_TO_PERCENT_PRECISION has to be a positive integer "
                    "value (actually, zero is ok aswell)."
                ),
                id="stockings.e003",
            )
        )

    return errors
