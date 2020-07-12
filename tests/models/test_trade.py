"""Provide tests for `stockings.models.trade.Trade``."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.models.trade import Trade

# app imports
from ..util.testcases import StockingsTestCase


@tag("current")
class TradeTest(StockingsTestCase):
    """Provide tests for `Trade` class."""

    @mock.patch("stockings.models.trade.Trade.currency", new_callable=mock.PropertyMock)
    @mock.patch(
        "stockings.models.trade.Trade.timestamp", new_callable=mock.PropertyMock
    )
    def test_costs_get(self, mock_timestamp, mock_currency):
        """Return the instances attributes as StockingsMoney instance."""
        # get a Trade instance
        a = Trade()

        # actually access the attribute
        b = a.costs

        self.assertEqual(a._costs_amount, b.amount)
        self.assertEqual(mock_currency.return_value, b.currency)
        self.assertEqual(mock_timestamp.return_value, b.timestamp)

    def test_costs_set(self):
        """Property is read-only."""
        # get a Trade instance
        a = Trade()

        with self.assertRaises(AttributeError):
            a.costs = "foobar"
