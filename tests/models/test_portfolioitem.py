"""Provides tests for module `stockings.models.portfolioitem`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.models.portfolioitem import PortfolioItem
from stockings.models.trade import Trade

# app imports
from ..util.testcases import StockingsORMTestCase, StockingsTestCase


@tag("models", "portfolioitem", "unittest")
class PortfolioItemTest(StockingsTestCase):
    """Provide tests for PortfolioItem class."""

    @mock.patch("stockings.models.portfolioitem.PortfolioItem.currency")
    @mock.patch("stockings.models.portfolioitem.PortfolioItem.trades")
    def test_cash_in_get_with_annotations(self, mock_trades, mock_currency):
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
    def test_cash_in_get_without_annotations(self, mock_trades, mock_currency):
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


@tag("integrationtest", "models", "portfolioitem")
class PortfolioItemORMTest(StockingsORMTestCase):
    """Provide tests with fixture data."""

    @skip("to be done")
    def test_cash_in_get_with_annotations(self):
        """Property's getter uses annotated attributes."""
        raise NotImplementedError

    def test_cash_in_get_without_annotations(self):
        """Property's getter retrieves missing attributes."""
        # get the PortfolioItem (just one "BUY" trade)
        a = PortfolioItem.objects.get(
            portfolio__name="PortfolioA", stockitem__isin="XX0000000001"
        )

        # get the relevant Trade items and calculate the trade_amount
        trade_amount = 0
        for item in Trade.objects.filter(
            portfolioitem=a, trade_type=Trade.TRADE_TYPE_BUY
        ).iterator():
            trade_amount += item._price_amount * item.item_count

        self.assertAlmostEqual(trade_amount, a.cash_in.amount)

        # get the PortfolioItem (two "BUY" trades)
        b = PortfolioItem.objects.get(
            portfolio__name="PortfolioB1", stockitem__isin="XX0000000004"
        )

        # get the relevant Trade items and calculate the trade_amount
        trade_amount = 0
        for item in Trade.objects.filter(
            portfolioitem=b, trade_type=Trade.TRADE_TYPE_BUY
        ).iterator():
            trade_amount += item._price_amount * item.item_count

        self.assertAlmostEqual(trade_amount, b.cash_in.amount)
