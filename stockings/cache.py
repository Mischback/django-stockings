"""Provides app-specific interfaces to Django's cache system."""

# Python imports
import logging

# Django imports
from django.conf import settings
from django.core.cache import cache
from django.core.cache.utils import make_template_fragment_key

logger = logging.getLogger(__name__)


def get_template_fragment(cache_key, use_cache, render_func, *args, **kwargs):
    """Retrieve a template fragment from the cache or create that fragment.

    Parameters
    ----------
    cache_key : str
        The key to be retrieved or set.
    use_cache : bool
        Controls, whether the function should try to retrieve from cache or not.
        If set to ``False``, the template fragment will be rendered.
    render_func :
        This is the function to actually create the template fragment. It will
        be called with ``*args`` and ``**kwargs``.

    Returns
    -------
    The template fragment : str
    """
    if use_cache is True:
        rendered = cache.get(cache_key)
        if rendered:
            return rendered

    logger.debug("Updating cache for {}".format(cache_key))
    rendered = render_func(*args, **kwargs)

    cache.set(cache_key, rendered, timeout=settings.STOCKINGS_CACHE_TIMEOUT)

    return rendered


def invalidate_cache(key):
    """Delete a given cache entry.

    The function can handle single cache entries aswell as a list of entries and
    will dynamically use the required Django function.

    Parameters
    ----------
    key : mixed
        ``key`` may either be a string, if the deletion of a single entry should
        be performed or a list of strings.

    Notes
    -----
    If the function is called with a :obj:`list`, it is not checked, whether
    the list contains strings. :func:`django.core.cache.cache.delete_many` may
    raise an exception.

    As of **Django 3.1**, :func:`django.core.cache.cache.delete` and
    :func:`django.core.cache.cache.delete_many` return ``True`` / ``False`` to
    indicate success. The app supports the latest LTS (2.2), so these return
    codes are not considered.
    """
    if isinstance(key, list):
        # TODO: write appropriate test to check the behaviour, if the list does
        #       not contain strings
        cache.delete_many(key)
    elif isinstance(key, str):
        cache.delete(key)
    else:
        logger.info("Could not delete cache, received incompatible key")


def keygen_portfolioitem_list(status_filter, portfolio_id):  # noqa: D205, D400
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
