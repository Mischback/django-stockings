"""Provides the app-specific settings.

This module contains the app-specific settings with their respective default
values.

The settings may be provided in the project's settings module.
"""

# Django imports
from django.conf import settings

STOCKINGS_CACHE_TIMEOUT = None
"""Determines the timeout for app-specific cache operations (:obj:`int`).

**Default value:** ``None``

Notes
-----
The app will set any timeouts explicitly when accessing the cache, so the
specified timeout in :setting:`CACHE` will not be used. Instead, this setting
controls the timeout.

The app will handle cache invalidation, whenever necessary, so this setting
may be left as ``None``. If your project makes heavy use of Django's cache
system and you are forced to keep the cache small, you may place any positive
integer value here.
"""


STOCKINGS_DEFAULT_CURRENCY = "EUR"
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

STOCKINGS_TO_PERCENT_PRECISION = 2
"""The number of decimal places used by the templatetag
:func:`~stockings.templatetags.stockings_extra.to_percent` (:obj:`int`).

**Default value:** ``2``
"""


STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS = True
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


def _read_default_currency():
    """Return the app-specific setting :attr:`stockings.settings.STOCKINGS_DEFAULT_CURRENCY`.

    This utility function is required, to make the app-specific setting actually
    usable by the app's models :class:`stockings.models.portfolio.Portfolio` and
    :class:`stockings.models.stockitem.StockItem`.

    Returns
    -------
    str
        The value of :attr:`stockings.settings.STOCKINGS_DEFAULT_CURRENCY`.
    """
    return settings.STOCKINGS_DEFAULT_CURRENCY
