"""Tests for module `stockings.signals.handlers`."""

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
from stockings.exceptions import StockingsInterfaceError
from stockings.signals.handlers import price_information_changed

# app imports
from .util.testcases import StockingsTestCase


@tag("signals", "signal handlers", "unittest")
class StockingsSignalHandlerTest(StockingsTestCase):
    """Provides tests for moduls `stockings.signals.handlers`."""

    def test_price_information_changed_missing_instance(self):
        """Missing instance parameter raises error."""
        with self.assertRaises(StockingsInterfaceError):
            price_information_changed(None)

    @mock.patch("stockings.signals.handlers.logger")
    def test_price_information_changed_raw_mode(self, mock_logger):
        """Only use logging if ``raw == True``."""
        price_information_changed(None, instance="foobar", raw=True)
        mock_logger.debug.assert_called_with("Skipped because of `raw` operation.")

    @mock.patch("stockings.signals.handlers.invalidate_cache")
    @mock.patch("stockings.signals.handlers.find_portfolioitem_list_caches")
    def test_price_information_changed_invalidate_caches(
        self, mock_find_caches, mock_invalidate_cache
    ):
        """Caches are invalidated based on find_portfolioitem_list_caches."""
        price_information_changed(None, instance="foobar")

        mock_find_caches.assert_called_with("foobar")
        mock_invalidate_cache.assert_called_with(
            mock_find_caches.return_value.__radd__.return_value
        )
