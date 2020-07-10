"""Provides tests for module `stockings.models.portfolioitem`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.models.portfolioitem import PortfolioItem

# app imports
from ..util.testcases import StockingsTestCase


@tag("models", "portfolioitem", "unittest")
class PortfolioItemTest(StockingsTestCase):
    """Provide tests for PortfolioItem class."""

    @mock.patch("stockings.models.portfolioitem.PortfolioItem.currency")
    @mock.patch("stockings.models.portfolioitem.PortfolioItem.trades")
    def test_property_cash_in_with_annotations(self, mock_trades, mock_currency):
        """Property's getter uses annotated attributes."""
        # get a PortfolioItem
        a = PortfolioItem()
        # These attributes can't be mocked by patch, because they are not part
        # of the actual class. Provide them here to simulate Django's annotation
        a._cash_in_amount = mock.MagicMock()
        a._cash_in_timestamp = mock.MagicMock()

        # actually access the attribute
        b = a.cash_in

        self.assertFalse(mock_trades.return_value.trade_summary.called)
        self.assertEqual(
            b, StockingsMoney(a._cash_in_amount, mock_currency, a._cash_in_timestamp)
        )

    @mock.patch("stockings.models.portfolioitem.PortfolioItem.currency")
    @mock.patch("stockings.models.portfolioitem.PortfolioItem.trades")
    def test_cash_in_without_annotations(self, mock_trades, mock_currency):
        """Property's getter retrieves missing attributes."""
        # set up the mock
        mock_amount = mock.MagicMock()
        mock_timestamp = mock.MagicMock()
        mock_trades.return_value.trade_summary.return_value = [
            {
                "purchase_amount": mock_amount,
                "purchase_latest_timestamp": mock_timestamp,
            },
        ]

        # get a PortfolioItem
        a = PortfolioItem()

        # actually access the attribute
        b = a.cash_in

        self.assertTrue(mock_trades.return_value.trade_summary.called)
        self.assertEqual(b, StockingsMoney(mock_amount, mock_currency, mock_timestamp))

    def test_cash_in_set(self):
        """Property is read-only."""
        a = PortfolioItem()

        with self.assertRaises(AttributeError):
            a.cash_in = "foobar"
