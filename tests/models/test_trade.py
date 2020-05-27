"""Provide tests for `stockings.models.trade.Trade``."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.core.exceptions import ValidationError
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.portfolio import PortfolioItem
from stockings.models.trade import Trade

# app imports
from ..util.testcases import StockingsTestCase


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

    @mock.patch(
        "stockings.models.trade.Trade.portfolio", new_callable=mock.PropertyMock
    )
    def test_property_costs(self, mock_portfolio):
        """Returns correctly populated `StockingsMoney` object."""
        # get a `Trade` object
        a = Trade()

        b = a.costs

        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 0)
        self.assertEqual(b.amount, a._costs_amount)
        self.assertEqual(b.currency, mock_portfolio.return_value.currency)
        self.assertEqual(b.timestamp, a.timestamp)

    @mock.patch(
        "stockings.models.trade.Trade.portfolio", new_callable=mock.PropertyMock
    )
    def test_property_currency(self, mock_portfolio):
        """Returns the currency of `Portfolio`."""
        # get a `Trade` object
        a = Trade()

        b = a.currency

        self.assertEqual(b, mock_portfolio.return_value.currency)

        # setter
        with self.assertRaises(StockingsInterfaceError):
            a.currency = "FOO"

        # deleter
        with self.assertRaises(AttributeError):
            del a.currency

    @mock.patch(
        "stockings.models.trade.Trade.portfolio", new_callable=mock.PropertyMock
    )
    def test_property_price(self, mock_portfolio):
        """Returns correctly populated `StockingsMoney` object."""
        # get a `Trade` object
        a = Trade()

        b = a.price

        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 0)
        self.assertEqual(b.amount, a._price_amount)
        self.assertEqual(b.currency, mock_portfolio.return_value.currency)
        self.assertEqual(b.timestamp, a.timestamp)
