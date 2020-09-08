"""Tests for module `stockings.cache`."""

# Python imports
from unittest import (  # noqa
    mock,
    skip,
)

# Django imports
from django.test import (  # noqa
    override_settings,
    tag,
)

# app imports
from stockings.cache import (
    get_template_fragment,
    invalidate_cache,
    keygen_portfolioitem_list,
)

# app imports
from .util.testcases import StockingsTestCase


@tag("cache")
class StockingsCacheTest(StockingsTestCase):
    """Provides tests for module `stockings.cache`."""

    @mock.patch("stockings.cache.cache")
    def test_get_template_fragment_use_cache(self, mock_cache):
        """Fragment is fetched from the cache."""
        # setup the mock
        mock_func = mock.MagicMock()

        self.assertEqual(
            mock_cache.get.return_value,
            get_template_fragment("foobar", True, mock_func),
        )

        self.assertTrue(mock_cache.get.called)
        self.assertFalse(mock_func.called)
        self.assertFalse(mock_cache.set.called)

    @override_settings(STOCKINGS_CACHE_TIMEOUT=1337)
    @mock.patch("stockings.cache.cache")
    def test_get_template_fragment_use_cache_miss(self, mock_cache):
        """Fragment is not available in cache and rendered again."""
        # setup the mock
        mock_func = mock.MagicMock()
        mock_cache.get.return_value = None

        self.assertEqual(
            mock_func.return_value,
            get_template_fragment("foobar", True, mock_func, *("foo", "bar")),
        )

        self.assertTrue(mock_cache.get.called)
        self.assertTrue(mock_func.called)
        self.assertTrue(mock_cache.set.called)

        # are the parameters passed on?
        mock_func.assert_called_with("foo", "bar")

        # is the cache correctly updated?
        mock_cache.set.assert_called_with(
            "foobar", mock_func.return_value, timeout=1337
        )

    @override_settings(STOCKINGS_CACHE_TIMEOUT=1337)
    @mock.patch("stockings.cache.cache")
    def test_get_template_fragment_do_not_use_cache(self, mock_cache):
        """Bypass the cache."""
        # setup the mock
        mock_func = mock.MagicMock()

        self.assertEqual(
            mock_func.return_value,
            get_template_fragment("foobar", False, mock_func, *("foo", "bar")),
        )

        self.assertFalse(mock_cache.get.called)
        self.assertTrue(mock_func.called)
        self.assertTrue(mock_cache.set.called)

        # are the parameters passed on?
        mock_func.assert_called_with("foo", "bar")

        # is the cache correctly updated?
        mock_cache.set.assert_called_with(
            "foobar", mock_func.return_value, timeout=1337
        )

    @mock.patch("stockings.cache.cache")
    def test_invalidate_cache_string(self, mock_cache):
        """Invalidate a single cache entry."""
        test_key = "foobar"

        invalidate_cache(test_key)

        mock_cache.delete.assert_called_with(test_key)

    @mock.patch("stockings.cache.cache")
    def test_invalidate_cache_list(self, mock_cache):
        """Invalidate a list of cache entries."""
        test_key_list = ["foo", "bar"]

        invalidate_cache(test_key_list)

        mock_cache.delete_many.assert_called_with(test_key_list)

    @mock.patch("stockings.cache.logger")
    def test_invalidate_cache_incompatible(self, mock_logger):
        """Log a message, if called with incompatible key."""
        invalidate_cache(5)

        self.assertTrue(mock_logger.info.called)

    @mock.patch("stockings.cache.make_template_fragment_key")
    def test_keygen_portfolioitem_list(self, mock_make_fragment_key):
        """Key generation relies on Django's built-in function."""
        self.assertEqual(
            mock_make_fragment_key.return_value, keygen_portfolioitem_list("active", 1)
        )
        mock_make_fragment_key.assert_called_with(
            "portfolio.portfolioitem_list.active", [1]
        )

        mock_make_fragment_key.mock_reset()

        self.assertEqual(
            mock_make_fragment_key.return_value,
            keygen_portfolioitem_list("inactive", 1),
        )
        mock_make_fragment_key.assert_called_with(
            "portfolio.portfolioitem_list.inactive", [1]
        )
