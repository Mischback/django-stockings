"""Provides views for the :class:`stockings.models.portfolioitem.PortfolioItem` model.

Additionally, it provides functions to render template fragments for other
views.
"""

# Python imports
import logging

# Django imports
from django.template.loader import render_to_string

# app imports
from stockings.exceptions import StockingsTemplateError

logger = logging.getLogger(__name__)


def render_portfolioitems_as_table(portfolioitems, status_filter):
    """Create a template fragment from a list of `PortfolioItem` objects.

    The function dynamically determines, which template needs to be used for the
    fragment, depending on the value of ``status_filter``.

    Parameters
    ----------
    portfolioitems : list
        The list of :class:`PortfolioItem objects <stockings.models.portfolioitem.PortfolioItem>`
        to be rendered. This is used as the context during the rendering process.
    status_filter : str
        Determines, if ``"active"`` or ``"inactive"`` items should be rendered.
        This also determines, which template will be used.

    Returns
    -------
    The rendered template fragment : str

    Raises
    ------
    StockingsTemplateError
        Raised, if ``status_filter`` has an value other than ``"active"`` or
        ``"inactive"``.

    See Also
    --------
    django.template.loader.render_to_string : This function actually performs
        the rendering.
    """
    # Determine which template needs rendering
    if status_filter == "active":
        template = "stockings/portfolioitem_table_active.html"
    elif status_filter == "inactive":
        template = "stockings/portfolioitem_table_inactive.html"
    else:
        raise StockingsTemplateError(
            "`status_filter` has to be either `active` or `inactive`."
        )

    logger.debug("Rendering fragment with template '{}'".format(template))

    # Actually render the fragment
    return render_to_string(template, {"portfolioitems": portfolioitems})
