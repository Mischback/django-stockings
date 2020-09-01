"""Provides an app-specific collection of templatetags."""

# Python imports
import logging

# Django imports
from django import template
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key
from django.template.loader import render_to_string

# app imports
from stockings.exceptions import StockingsTemplateError

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


def _internal_fallback_format_percent(value):
    """Format a percent value.

    This is an internal fallback function, that is utilised if the
    :func:`~stockings.templatetags.stockings_extra.to_percent` templatetag /
    filter is used without having `Babel` installed.

    Parameters
    ----------
    value : decimal.Decimal

    Returns
    -------
    formatted percent value : str

    Notes
    -----
    The function uses a simple string format. The used format string is
    ``"{value:.{precision}f}"``, meaning, the percent value is rounded to the
    given precision.
    """
    # TODO: Make the precision configurable
    return "{value:.2f}".format(value=value * 100, precision=2)


@register.simple_tag(takes_context=True)
def list_portfolioitems_as_table(
    context, portfolioitems, status_filter="active", use_cache=True
):  # noqa: D205, D400
    """Format a list of :class:`stockings.models.portfolioitem.PortfolioItem`
    instances and provide them as HTML table rows.

    The templatetag will try to get the rendered result from Django's cache or
    will render on-the-fly.

    Parameters
    ----------
    context : django.template.Context
        The currently active context object. This parameter is automatically
        provided by Django and *must not* be provided while using the
        templatetag.
    portfolioitems : list
        The list of :class:`~stockings.models.portfolioitem.PortfolioItem`
        instances to be rendered.
    status_filter : str, optional
        Determines, if ``"active"`` or ``"inactive"`` items should be rendered.
        This also determines, which template will be used. Default value is
        ``"active"``.
    use_cache : bool, optional
        Determines, if the cache lookup should be performed. Default value is
        ``True``.

    Returns
    -------
    The rendered template fragment : str

    Raises
    ------
    stockings.exceptions.StockingsTemplateError
        The error is raised, if ``status_filter`` is set to an illegal value.

    Notes
    -----
    The templatetag will try to fetch the rendered fragment from Django's cache.
    The corresponding ``cache_key`` is determined using Django's
    :func:`~django.core.cache.utils.make_template_fragment_key` and will vary on
    the :model:`corresponding Portfolio's id <stockings.models.portfolio.Portfolio>`,
    thus, the `Portfolio` has to be provided to the function.
    The function will fetch the `Portfolio` from the ``context``.

    The function dynamically determines, which template needs to be rendered,
    depending on ``status_filter``: if ``status_filter == "active"``, the
    template ``stockings/portfolioitem_table_active.html`` will be used or
    if ``status_filter == "inactive"``
    ``stockings/portfolioitem_table_inactive.html`` is used. If ``status_filter``
    has any other value, :class:`stockings.exceptions.StockingsTemplateError` is
    raised.
    """
    # Get the portfolio from the context
    portfolio = context["portfolio"]

    # Get the cache_key, and vary on `portfolio.id`
    cache_key = make_template_fragment_key(
        "portfolio.portfolioitem_list.{}".format(status_filter), [portfolio.id]
    )

    # Try to fetch the fragment from cache
    if use_cache is True:
        rendered = cache.get(cache_key)
        if rendered:
            return rendered

    # Determine which template needs rendering
    if status_filter == "active":
        template = "stockings/portfolioitem_table_active.html"
    elif status_filter == "inactive":
        template = "stockings/portfolioitem_table_inactive.html"
    else:
        raise StockingsTemplateError(
            "`status_filter` has to be either `active` or `inactive`."
        )

    # Actually render the fragment
    rendered = render_to_string(template, {"portfolioitems": portfolioitems})

    # Update the cache
    cache.set(cache_key, rendered, timeout=None)

    return rendered


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


@register.filter
def to_percent(value):
    """Format a value as percents based on the user's locale.

    Parameters
    ----------
    value : decimal.Decimal

    Returns
    -------
    formatted percent value : str

    Notes
    -----
    The function will try to use `Babel` to provide a locale-aware formatting
    of the provided value, limited to two decimal places

    However, if `Babel` is not available, it will fall back to an internal
    formatting function
    :func:`stockings.templatetags.stockings_extra._internal_fallback_format_percent`.
    """
    try:
        from babel.numbers import format_percent
        from stockings.i18n import get_current_locale
    except ImportError:
        logger.info(
            "`Babel` could not be loaded. Falling back to an internal formatting function."
        )
        return _internal_fallback_format_percent(value)

    # TODO: Make the precision configurable
    # TODO: Second param of `round` is then `config_value + 2`
    return format_percent(
        round(value, 4), locale=get_current_locale(), decimal_quantization=False
    )
