"""Provides tests for module `stockings.models.portfolio`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.models.portfolio import Portfolio

# app imports
from ..util.testcases import StockingsTestCase


@tag("models", "portfolio")
class PortfolioTest(StockingsTestCase):
    """Provide tests for `Portfolio` class."""

    def test_property_currency_get(self):
        """Property's getter simply returns the stored attribute."""
        # get a Portfolio object
        a = Portfolio()

        self.assertEqual(a._currency, a.currency)
