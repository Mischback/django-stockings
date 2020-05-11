# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.core.exceptions import ValidationError
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.models.portfolio import PortfolioItem
from stockings.models.trade import Trade

# app imports
from .util.testcases import StockingsTestCase


class TradeTest(StockingsTestCase):
    """Provide tests for `Trade` class."""

    @mock.patch("stockings.models.trade.Trade.stock_item")
    @mock.patch("stockings.models.trade.Trade.portfolio")
    def test_clean_sell_ok(self, mock_portfolio, mock_stock_item):
        """All cleaning is successfully done, `item_count` is not adjusted."""

        # set up the mocks
        mock_portfolio_item = mock.MagicMock()
        type(mock_portfolio_item).stock_count = mock.PropertyMock(return_value=5)

        mock_portfolio.portfolioitem_set.get.return_value = mock_portfolio_item

        # set up the `Trade` object
        a = Trade(item_count=3, trade_type="SELL")

        # actually call the method
        a.clean()

        self.assertEqual(a.item_count, 3)

    @mock.patch("stockings.models.trade.Trade.stock_item")
    @mock.patch("stockings.models.trade.Trade.portfolio")
    def test_clean_sell_item_count_too_high(self, mock_portfolio, mock_stock_item):
        """`item_count` is adjusted to maximum `stock_count` of `PortfolioItem`."""

        # set up the mocks
        mock_portfolio_item = mock.MagicMock()
        type(mock_portfolio_item).stock_count = mock.PropertyMock(return_value=5)

        mock_portfolio.portfolioitem_set.get.return_value = mock_portfolio_item

        # set up the `Trade` object
        a = Trade(item_count=10, trade_type="SELL")

        # actually call the method
        a.clean()

        self.assertEqual(a.item_count, 5)

    @mock.patch("stockings.models.trade.Trade.stock_item")
    @mock.patch("stockings.models.trade.Trade.portfolio")
    def test_clean_sell_invalid_portfolio_item(self, mock_portfolio, mock_stock_item):
        """Selling stock that is not in the portfolio is prohibited."""

        # set up the mocks
        mock_portfolio_item = mock.MagicMock()
        type(mock_portfolio_item).stock_count = mock.PropertyMock(return_value=5)

        # TODO: this must raise `PortfolioItem.DoesNotExist`
        # mock_portfolio.portfolioitem_set.get.return_value = mock_portfolio_item
        mock_portfolio.portfolioitem_set.get.side_effect = PortfolioItem.DoesNotExist

        # set up the `Trade` object
        a = Trade(item_count=3, trade_type="SELL")

        # actually call the method
        with self.assertRaises(ValidationError):
            a.clean()

    @mock.patch("stockings.models.trade.Trade.portfolio")
    def test_clean_buy_noop(self, mock_portfolio):
        """`trade_type` `BUY` does effectively nothing."""

        # set up the `Trade` object
        a = Trade(item_count=10, trade_type="BUY")

        # actually call the method
        a.clean()

        self.assertFalse(mock_portfolio.portfolioitem_set.get.called)

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
