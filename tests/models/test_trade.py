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

    @mock.patch(
        "stockings.models.trade.Trade.portfolioitem", new_callable=mock.PropertyMock,
    )
    def test_currency_get_with_annotations(self, mock_portfolioitem):
        """Property's getter uses annotated attributes."""
        # get a Trade instance
        a = Trade()
        # This attribute can't be mocked by patch, because it is no part of the
        # actual class. Provide it here to simulate Django's annotation
        a._currency = mock.MagicMock()

        # actually access the attribute
        b = a.currency

        self.assertFalse(mock_portfolioitem.called)
        self.assertEqual(b, a._currency)

    @mock.patch(
        "stockings.models.trade.Trade.portfolioitem", new_callable=mock.PropertyMock,
    )
    def test_currency_get_wihtout_annotations(self, mock_portfolioitem):
        """Property's getter retrieves missing attributes."""
        # get a Trade instance
        a = Trade()

        # actually access the attribute
        b = a.currency

        self.assertTrue(mock_portfolioitem.called)
        self.assertEqual(b, mock_portfolioitem.return_value.currency)

    def test_currency_set(self):
        """Property is read-only."""
        a = Trade()

        with self.assertRaises(AttributeError):
            a.currency = "foobar"
