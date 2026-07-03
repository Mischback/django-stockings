# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Provide the default values for app-specific settings."""

# Django imports
from django.conf import settings

STOCKINGS_DEFAULT_CURRENCY = "EUR"
"""Determines the default value for all currency fields (:obj:`str`).

**Default value:** ``"EUR"``

The currency is stored as its
:wiki:`currency code as described by ISO 4217 <ISO_4217>`.

Warnings
--------
Handling of different currencies is not (yet) implemented, so this setting
currently has no effect.
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
