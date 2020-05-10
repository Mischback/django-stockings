# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.models.trade import Trade

# app imports
from .util.testcases import StockingsTestCase


class TradeTest(StockingsTestCase):
    """Provide tests for `Trade` class."""

    def test_get_costs(self):
        """Returns correctly populated `StockingsMoney` object."""

        a = Trade()

        b = a.costs

        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 0)
        self.assertEqual(b.amount, a._costs_amount)
        self.assertEqual(b.currency, "EUR")
        self.assertEqual(b.currency, a._costs_currency)
        self.assertEqual(b.timestamp, a.timestamp)

    def test_get_price(self):
        """Returns correctly populated `StockingsMoney` object."""

        a = Trade()

        b = a.price

        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 0)
        self.assertEqual(b.amount, a._price_amount)
        self.assertEqual(b.currency, "EUR")
        self.assertEqual(b.currency, a._price_currency)
        self.assertEqual(b.timestamp, a.timestamp)
