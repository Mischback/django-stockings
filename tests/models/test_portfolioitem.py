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

    @mock.patch("stockings.models.portfolioitem.PortfolioItem.currency")
    @mock.patch("stockings.models.portfolioitem.PortfolioItem.trades")
    def test_cash_out_get_with_annotations(self, mock_trades, mock_currency):
        """Property's getter uses annotated attributes."""
        # get a PortfolioItem
        a = PortfolioItem()
        # These attributes can't be mocked by patch, because they are not part
        # of the actual class. Provide them here to simulate Django's annotation
        a._cash_out_amount = mock.MagicMock()
        a._cash_out_timestamp = mock.MagicMock()

        # actually access the attribute
        b = a.cash_out

        self.assertFalse(mock_trades.return_value.trade_summary.called)
        self.assertEqual(
            b, StockingsMoney(a._cash_out_amount, mock_currency, a._cash_out_timestamp)
        )

    @mock.patch("stockings.models.portfolioitem.PortfolioItem.currency")
    @mock.patch("stockings.models.portfolioitem.PortfolioItem.trades")
    def test_cash_out_get_without_annotations(self, mock_trades, mock_currency):
        """Property's getter retrieves missing attributes."""
        # set up the mock
        mock_amount = mock.MagicMock()
        mock_timestamp = mock.MagicMock()
        mock_trades.return_value.trade_summary.return_value = [
            {"sale_amount": mock_amount, "sale_latest_timestamp": mock_timestamp},
        ]

        # get a PortfolioItem
        a = PortfolioItem()

        # actually access the attribute
        b = a.cash_out

        self.assertTrue(mock_trades.return_value.trade_summary.called)
        self.assertEqual(b, StockingsMoney(mock_amount, mock_currency, mock_timestamp))

    def test_cash_out_set(self):
        """Property is read-only."""
        a = PortfolioItem()

        with self.assertRaises(AttributeError):
            a.cash_out = "foobar"

    @mock.patch("stockings.models.portfolioitem.PortfolioItem.currency")
    @mock.patch("stockings.models.portfolioitem.PortfolioItem.trades")
    def test_costs_get_with_annotations(self, mock_trades, mock_currency):
        """Property's getter uses annotated attributes."""
        # get a PortfolioItem
        a = PortfolioItem()
        # These attributes can't be mocked by patch, because they are not part
        # of the actual class. Provide them here to simulate Django's annotation
        a._costs_amount = mock.MagicMock()
        a._costs_timestamp = mock.MagicMock()

        # actually access the attribute
        b = a.costs

        self.assertFalse(mock_trades.return_value.trade_summary.called)
        self.assertEqual(
            b, StockingsMoney(a._costs_amount, mock_currency, a._costs_timestamp)
        )

    @mock.patch("stockings.models.portfolioitem.PortfolioItem.currency")
    @mock.patch("stockings.models.portfolioitem.PortfolioItem.trades")
    def test_costs_get_without_annotations(self, mock_trades, mock_currency):
        """Property's getter retrieves missing attributes."""
        # set up the mock
        mock_amount = mock.MagicMock()
        mock_timestamp = mock.MagicMock()
        mock_trades.return_value.trade_summary.return_value = [
            {"costs_amount": mock_amount, "costs_latest_timestamp": mock_timestamp},
        ]

        # get a PortfolioItem
        a = PortfolioItem()

        # actually access the attribute
        b = a.costs

        self.assertTrue(mock_trades.return_value.trade_summary.called)
        self.assertEqual(b, StockingsMoney(mock_amount, mock_currency, mock_timestamp))

    def test_costs_set(self):
        """Property is read-only."""
        a = PortfolioItem()

        with self.assertRaises(AttributeError):
            a.costs = "foobar"


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

    @skip("to be done")
    def test_cash_out_get_with_annotations(self):
        """Property's getter uses annotated attributes."""
        raise NotImplementedError

    def test_cash_out_get_without_annotations(self):
        """Property's getter retrieves missing attributes."""
        # get the PortfolioItem (just one "SELL" trade)
        a = PortfolioItem.objects.get(
            portfolio__name="PortfolioA", stockitem__isin="XX0000000001"
        )

        # get the relevant Trade items and calculate the trade_amount
        trade_amount = 0
        for item in Trade.objects.filter(
            portfolioitem=a, trade_type=Trade.TRADE_TYPE_SELL
        ).iterator():
            trade_amount += item._price_amount * item.item_count

        self.assertAlmostEqual(trade_amount, a.cash_out.amount)

        # get the PortfolioItem (two "SELL" trades)
        b = PortfolioItem.objects.get(
            portfolio__name="PortfolioB1", stockitem__isin="XX0000000004"
        )

        # get the relevant Trade items and calculate the trade_amount
        trade_amount = 0
        for item in Trade.objects.filter(
            portfolioitem=b, trade_type=Trade.TRADE_TYPE_SELL
        ).iterator():
            trade_amount += item._price_amount * item.item_count

        self.assertAlmostEqual(trade_amount, b.cash_out.amount)

    @skip("to be done")
    def test_costs_get_with_annotations(self):
        """Property's getter uses annotated attributes."""
        raise NotImplementedError

    def test_costs_get_without_annotations(self):
        """Property's getter retrieves missing attributes."""
        # get the PortfolioItem (just one "BUY" trade)
        a = PortfolioItem.objects.get(
            portfolio__name="PortfolioA", stockitem__isin="XX0000000001"
        )

        # get the relevant Trade items and calculate the trade_amount
        trade_costs = 0
        for item in Trade.objects.filter(portfolioitem=a).iterator():
            trade_costs += item._costs_amount

        self.assertAlmostEqual(trade_costs, a.costs.amount)

        # get the PortfolioItem (two "BUY" trades)
        b = PortfolioItem.objects.get(
            portfolio__name="PortfolioB1", stockitem__isin="XX0000000004"
        )

        # get the relevant Trade items and calculate the trade_amount
        trade_costs = 0
        for item in Trade.objects.filter(portfolioitem=b).iterator():
            trade_costs += item._costs_amount

        self.assertAlmostEqual(trade_costs, b.costs.amount)
