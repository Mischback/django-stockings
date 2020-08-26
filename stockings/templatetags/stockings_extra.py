"""Provides an app-specific collection of templatetags."""

# Django imports
from django import template

register = template.Library()
"""Required module-level variable to build a templatetag library."""


@register.inclusion_tag("stockings/money_instance.html")
def money(money_instance):
    """Provide a uniform format to all instances of :class:`stockings.data.StockingsMoney` throughout the templates.

    Parameters
    ----------
    money_instance : stockings.data.StockingsMoney

    Notes
    -----
    The actual formatting is done with a (modifiable) template,
    ``stockings/money_instance.html``.
    """
    return {"money": money_instance}
