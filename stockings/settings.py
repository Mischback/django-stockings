"""Provides the app-specific settings.

This module contains the app-specific settings with their respective default
values.

The settings may be provided in the project's settings module.
"""

# Django imports
from django.conf import settings

STOCKINGS_DEFAULT_CURRENCY = getattr(settings, "STOCKINGS_DEFAULT_CURRENCY", "EUR")
"""Determines the default value for all currency fields (:obj:`str`).

**Default value:** ``"EUR"``

Warnings
--------
Handling of different currencies is not (yet) implemented, so this setting
currently has no effect.

Notes
-----
The currency is actually stored by
:class:`~stockings.models.portfolio.Portfolio` and
:class:`~stockings.models.stockitem.StockItem` objects. Please refer to
:attr:`Portfolio.currency <stockings.models.portfolio.Portfolio.currency>` /
:attr:`StockItem.currency <stockings.models.stockitem.StockItem.currency>` for
more implementation details.

The currency is stored as its
:wiki:`currency code as described by ISO 4217 <ISO_4217>`.
"""

STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS = getattr(
    settings, "STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS", True
)
"""Make the app rely on Django's `django.contrib.auth` permission system (:obj:`bool`).

**Default value:** ``True``

Warnings
--------
Please note that, in Python, any non-zero value is considered ``True``, while
values like ``None``, ``[]``, ``{}`` or ``0`` are considered ``False``. The
unittests are considering some of these possibilities, but not all of them.

Notes
-----
If activated, all app-specific views check the requesting user's permissions,
that may be assigned in Django's admin backend, using `django.contrib.auth`'s
permission system.

By default, `django.contrib.auth` will (automatically) create ``add``,
``change``, ``delete`` and ``view`` permissions for every model of the app (see
:djangodoc:`topics/auth/default/#default-permissions`). These permissions are
checked while accessing any view.

Obviously, activating this setting requires `django.contrib.auth` to be present
in :setting:`INSTALLED_APPS`. This is ensured (or at least checked) by the app's
:mod:`stockings.checks` module.

If this setting is deactivated (set to ``False``), the views will not check the
user's permissions. But of course, the user still needs to be authenticated.
"""
