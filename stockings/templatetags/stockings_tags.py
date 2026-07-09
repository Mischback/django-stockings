# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""App-specific templatetags."""

# Python imports
import logging

# Django imports
from django import template
from django.utils.translation import get_language

# external imports
from babel.numbers import format_currency

# app imports
from stockings.services.data import StockingsMoney

logger = logging.getLogger(__name__)

register = template.Library()


@register.filter(name="format_money")
def format_money(value):
    """Format :class:`~stockings.data.StockingsMoney` instances."""
    # ONLY apply to StockingsMoney
    if not isinstance(value, StockingsMoney):
        return value

    current_locale = get_language() or "en_US"
    babel_locale = current_locale.replace("-", "_")

    try:
        return format_currency(
            value.amount,
            value.currency,
            locale=babel_locale,
        )
    except Exception:
        logger.warn("'format_currency()' failed!")
        return "{} {}".format(value.amount, value.currency)
