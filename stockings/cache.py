"""Provides app-specific interfaces to Django's cache system."""

# Python imports
import logging

# Django imports
from django.conf import settings
from django.core.cache import cache

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
