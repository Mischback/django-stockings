"""Provides functions to determine cache keys."""

# Django imports
from django.core.cache.utils import make_template_fragment_key


def portfolioitem_list(status_filter, portfolio_id):  # noqa: D205, D400
    """Generate a cache key for :class:`~stockings.models.portfolioitem.PortfolioItem`
    list fragments.

    Parameters
    ----------
    status_filter : str
        The `status_filter` is actually included in the cache key, to
        distinguish list of ``"active"`` and ``"inactive"`` items.
    portfolio_id : int
        The ID of the (parent) :class:`~stockings.models.portfolio.Portfolio`
        instance. This will be used as ``vary_on`` parameter.

    Returns
    -------
    The cache key : str

    See Also
    --------
    django.core.cache.utils.make_template_fragment_key
    """
    return make_template_fragment_key(
        "portfolio.portfolioitem_list.{}".format(status_filter), [portfolio_id]
    )
