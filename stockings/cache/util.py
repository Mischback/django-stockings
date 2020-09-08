"""Provides cache-related utility functions."""

# Python imports
import logging

# app imports
from stockings.cache.keygen import portfolioitem_list as keygen_portfolioitem_list
from stockings.models.portfolio import Portfolio
from stockings.models.stockitemprice import StockItemPrice

logger = logging.getLogger(__name__)


def find_portfolioitem_list_caches(instance):
    """Return a list of cache fragment keys of ``portfolioitem_lists``.

    The list will contain several keys, which will be determined based on the
    class of ``instance``.

    Parameters
    ----------
    instance : a `stockings` model class instance

    Returns
    -------
    key_list
        A list of :obj:`str`, which identify cache keys.

    Notes
    -----
    If ``instance`` is a :class:`~stockings.models.stockitemprice.StockItemPrice`
    instance, ``key_list`` will contain all keys of ``portfolioitem_lists``,
    which will vary on the condition, that the associated
    :class:`~stockings.models.stockitem.StockItem` is tracked by an
    :class:`~stockings.models.portfolioitem.PortfolioItem` instance in the
    :class:`~stockings.models.portfolio.Portfolio`. However, changes of
    :class:`~stockings.models.stockitemprice.StockItemPrice` only require to
    invalidate the ``"active"`` fragment.
    """
    # `key_list` will contain a list of keys
    key_list = []

    if isinstance(instance, StockItemPrice):
        logger.debug("[dev] Found instance of StockItemPrice!")

        # Find a list of Portfolio Ids, that contain the `StockItem`
        portfolio_list = (
            Portfolio.objects.filter(portfolioitems__stockitem=instance.stockitem)
            .values_list("id", flat=True)
            .distinct()
        )

        for portfolio_id in portfolio_list:
            key_list.append(keygen_portfolioitem_list("active", portfolio_id))

    return key_list
