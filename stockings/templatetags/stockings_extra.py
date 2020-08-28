"""Provides an app-specific collection of templatetags."""

# Python imports
import logging

# Django imports
from django import template

logger = logging.getLogger(__name__)

register = template.Library()
"""Required module-level variable to build a templatetag library."""


def _internal_fallback_format_currency(amount, currency):
    """Format a money value (including currency).

    This is an internal fallback function, that is utilised if the
    :func:`~stockings.templatetags.stockings_extra.money_locale` templatetag is
    used without having `Babel` installed.

    Parameters
    ----------
    amount : decimal.Decimal
    currency : str

    Returns
    -------
    formatted money value : str

    Notes
    -----
    The function uses a simple string format. The used format string is
    ``"{currency} {amount:.2f}"``, meaning that the ``amount`` is rounded to
    two decimal places.

    Instances of :class:`~stockings.data.StockingsMoney` provide its `currency`
    in :wiki:`ISO 4217 format<ISO_4217>`, so the currency is not displayed as
    symbol (`stockings` does not include its own logic to resolv currency codes
    to their according symbols).
    """
    return "{currency} {amount:.2f}".format(amount=amount, currency=currency)


@register.simple_tag
def money_locale(money_instance):
    """Format a money value (including currency) based on the user's locale.

    Parameters
    ----------
    money_instance : stockings.data.StockingsMoney

    Returns
    -------
    formatted money value : str

    Notes
    -----
    The function will try to use `Babel` to provide a locale-aware formatting
    of the money's value including its currency.

    However, if `Babel` is not available, it will fall back to an internal
    formatting function
    :func:`stockings.templatetags.stockings_extra._internal_fallback_format_currency`.

    If locale-aware formatting is not required or desired,
    :func:`stockings.templatetags.stockings_extra.money` may be used to control
    the format of :class:`stockings.data.StockingsMoney` instances.
    """
    try:
        # Actually, only the babel import may fail, but `get_current_locale` is
        # only required, if `format_currency` is available.
        from babel.numbers import format_currency
        from stockings.i18n import get_current_locale
    except ImportError:
        logger.info(
            "`Babel` could not be loaded. Falling back to an internal formatting function."
        )
        return _internal_fallback_format_currency(
            money_instance.amount, money_instance.currency
        )

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

    If the formatting is required to be locale-aware,
    :func:`stockings.templatetags.stockings_extra.money_locale` may be used (of
    course, that `templatetag` may aswell be used in the template, used by this
    tag, for even more flexibility).
    """
    return {"money": money_instance}
