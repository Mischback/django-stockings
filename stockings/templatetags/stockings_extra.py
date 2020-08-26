"""Provides an app-specific collection of templatetags."""

# Django imports
from django import template

# external imports
from babel.numbers import format_currency

# app imports
from stockings.i18n import get_current_locale

register = template.Library()
"""Required module-level variable to build a templatetag library."""


@register.simple_tag
def format_money(money_instance):
    """Format a money value (including currency) based on the user's locale.

    Returns
    -------
    formatted money value : str
    """
    return format_currency(
        money_instance.amount, money_instance.currency, locale=get_current_locale()
    )


@register.inclusion_tag("stockings/money_instance.html")
def money(money_instance):  # noqa: D205, D400
    """Provide a uniform format to all instances of
    :class:`stockings.data.StockingsMoney` throughout the templates.

    Parameters
    ----------
    money_instance : stockings.data.StockingsMoney

    Notes
    -----
    The actual formatting is done with a (modifiable) template,
    ``stockings/money_instance.html``.
    """
    return {"money": money_instance}
