"""Provides signal handlers."""

# Python imports
import logging

# app imports
from stockings.cache.cache import invalidate_cache
from stockings.cache.util import find_portfolioitem_list_caches
from stockings.exceptions import StockingsInterfaceError

logger = logging.getLogger(__name__)


def price_information_changed(sender, *args, **kwargs):
    """Perform necessary operations after price information changed.

    Parameters
    ----------
    sender
        The sender of the signal, might be a given object or ``None``.
    """
    instance = kwargs.get("instance", None)
    if instance is None:
        raise StockingsInterfaceError(
            "This signal handler must be called with an instance of StockItemPrice"
        )

    raw = kwargs.get("raw", False)

    # The following code should only be executed, if this is not a `raw` operation
    if not raw:
        key_list = []

        # caches of portfolioitem_list fragments
        key_list += find_portfolioitem_list_caches(instance)

        # actually invalidate the caches
        invalidate_cache(key_list)
    else:
        logger.debug("Skipped because of `raw` operation.")
