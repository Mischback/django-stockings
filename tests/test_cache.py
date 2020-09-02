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
from stockings.cache import get_template_fragment

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
