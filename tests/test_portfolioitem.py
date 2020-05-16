# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.portfolio import PortfolioItem

# app imports
from .util.testcases import StockingsTestCase


@tag("models", "portfolioitem")
class PortfolioItemTest(StockingsTestCase):
    """Provide tests for PortfolioItem class."""

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_property_cash_in(self, mock_return_money):
        """Property's getter uses `_return_money()`, setter raises exception."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # getting the property
        b = a.cash_in

        self.assertTrue(mock_return_money.called)
        mock_return_money.assert_called_with(
            a._cash_in_amount, timestamp=a._cash_in_timestamp
        )
        self.assertEqual(b, mock_return_money.return_value)

        # setting the property is not possible
        with self.assertRaises(StockingsInterfaceError):
            a.cash_in = 1337

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_property_cash_out(self, mock_return_money):
        """Property's getter uses `_return_money()`, setter raises exception."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # getting the property
        b = a.cash_out

        self.assertTrue(mock_return_money.called)
        mock_return_money.assert_called_with(
            a._cash_out_amount, timestamp=a._cash_out_timestamp
        )
        self.assertEqual(b, mock_return_money.return_value)

        # setting the property is not possible
        with self.assertRaises(StockingsInterfaceError):
            a.cash_out = 1337

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_property_costs(self, mock_return_money):
        """Property's getter uses `_return_money()`, setter raises exception."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # getting the property
        b = a.costs

        self.assertTrue(mock_return_money.called)
        mock_return_money.assert_called_with(
            a._costs_amount, timestamp=a._costs_timestamp
        )
        self.assertEqual(b, mock_return_money.return_value)

        # setting the property is not possible
        with self.assertRaises(StockingsInterfaceError):
            a.costs = 1337

    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.portfolio",
        new_callable=mock.PropertyMock,
    )
    def test_property_currency(self, mock_portfolio):
        """Returns the object's `currency`."""

        # get a PortfolioItem object
        a = PortfolioItem()

        self.assertEqual(a.currency, mock_portfolio.return_value.currency)

        # setting the property is not possible
        with self.assertRaises(StockingsInterfaceError):
            a.currency = "FOO"

    @mock.patch("stockings.models.portfolio.PortfolioItem.update_stock_value")
    def test_property_stock_count(self, mock_update):
        """Setting the `stock_count` updates the `stock_value`."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # set the stock count
        a.stock_count = 5

        self.assertTrue(mock_update.called)
        mock_update.assert_called_with(item_count=5)

        # get the stock count
        self.assertEqual(a.stock_count, a._stock_count)

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_property_stock_value(self, mock_return_money):
        """Property's getter uses `_return_money()`, setter raises exception."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # getting the property
        b = a.stock_value

        self.assertTrue(mock_return_money.called)
        mock_return_money.assert_called_with(
            a._stock_value_amount, timestamp=a._stock_value_timestamp
        )
        self.assertEqual(b, mock_return_money.return_value)

        # setting the property is not possible
        with self.assertRaises(StockingsInterfaceError):
            a.stock_value = 1337

    @mock.patch("stockings.models.portfolio.StockingsMoney", autospec=True)
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.portfolio",
        new_callable=mock.PropertyMock,
    )
    def test_return_money(self, mock_portfolio, mock_stockingsmoney):
        """Returns correctly populated `StockingsMoney` object."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # Only provide `amount`, let `currency` and `timestamp` be provided
        # automatically.
        b = a._return_money(1337)

        # `1337` is the provided value
        mock_stockingsmoney.assert_called_with(
            1337, mock_portfolio.return_value.currency, None
        )
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, mock_stockingsmoney.return_value.amount)
        self.assertEqual(b.currency, mock_stockingsmoney.return_value.currency)
        self.assertEqual(b.timestamp, mock_stockingsmoney.return_value.timestamp)

        # Providing a `currency` manually.
        b = a._return_money(1337, currency="BAR")

        # `1337` is the provided value, `"BAR"` is the provided value of `currency`
        mock_stockingsmoney.assert_called_with(1337, "BAR", None)
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, mock_stockingsmoney.return_value.amount)
        self.assertEqual(b.currency, mock_stockingsmoney.return_value.currency)
        self.assertEqual(b.timestamp, mock_stockingsmoney.return_value.timestamp)

        # Providing a `timestamp` manually
        b = a._return_money(1337, timestamp="now")

        # `1337` is the provided value, `"now"` is the provided timestamp
        mock_stockingsmoney.assert_called_with(
            1337, mock_portfolio.return_value.currency, "now"
        )
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, mock_stockingsmoney.return_value.amount)
        self.assertEqual(b.currency, mock_stockingsmoney.return_value.currency)
        self.assertEqual(b.timestamp, mock_stockingsmoney.return_value.timestamp)

    @mock.patch("stockings.models.portfolio.StockingsMoney", autospec=True)
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.portfolio",
        new_callable=mock.PropertyMock,
    )
    def test_update_cash_in(self, mock_portfolio, mock_stockingsmoney):
        """Adds provided `StockingsMoney` to `cash_in`."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # Actually it is assumed, that the method is called with a `StockingsMoney`
        # instance, but for this test, that part is mocked out anyway...
        a.update_cash_in("StockingsMoney")

        self.assertTrue(mock_stockingsmoney.return_value.add.called)
        self.assertEqual(
            a._cash_in_amount, mock_stockingsmoney.return_value.add.return_value.amount
        )
        self.assertEqual(
            a._cash_in_timestamp,
            mock_stockingsmoney.return_value.add.return_value.timestamp,
        )

    @mock.patch("stockings.models.portfolio.StockingsMoney", autospec=True)
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.portfolio",
        new_callable=mock.PropertyMock,
    )
    def test_update_cash_out(self, mock_portfolio, mock_stockingsmoney):
        """Adds provided `StockingsMoney` to `cash_out`."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # Actually it is assumed, that the method is called with a `StockingsMoney`
        # instance, but for this test, that part is mocked out anyway...
        a.update_cash_out("StockingsMoney")

        self.assertTrue(mock_stockingsmoney.return_value.add.called)
        self.assertEqual(
            a._cash_out_amount, mock_stockingsmoney.return_value.add.return_value.amount
        )
        self.assertEqual(
            a._cash_out_timestamp,
            mock_stockingsmoney.return_value.add.return_value.timestamp,
        )

    @mock.patch("stockings.models.portfolio.StockingsMoney", autospec=True)
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.portfolio",
        new_callable=mock.PropertyMock,
    )
    def test_update_costs(self, mock_portfolio, mock_stockingsmoney):
        """Adds provided `StockingsMoney` to `costs`."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # Actually it is assumed, that the method is called with a `StockingsMoney`
        # instance, but for this test, that part is mocked out anyway...
        a.update_costs("StockingsMoney")

        self.assertTrue(mock_stockingsmoney.return_value.add.called)
        self.assertEqual(
            a._costs_amount, mock_stockingsmoney.return_value.add.return_value.amount
        )
        self.assertEqual(
            a._costs_timestamp,
            mock_stockingsmoney.return_value.add.return_value.timestamp,
        )

    @tag("current")
    @mock.patch("stockings.models.portfolio.StockingsMoney", autospec=True)
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.portfolio",
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.stock_item",
        new_callable=mock.PropertyMock,
    )
    def test_update_stock_value(
        self, mock_stock_item, mock_portfolio, mock_stockingsmoney
    ):
        """Updates `stock_value` while automatically retrieving required parameters."""

        # get a PortfolioItem object
        a = PortfolioItem()
        a._stock_count = 1

        # Set up the mock object.
        # mock_latest_price = mock.PropertyMock(return_value=StockingsMoney(5, "EUR"))
        # type(mock_stock_item).latest_price = mock_latest_price

        # call `update_stock_value()` without any parameter
        a.update_stock_value()

        # `multiply()` is called with the current `_stock_count` (=1)
        mock_stock_item.return_value.latest_price.multiply.assert_called_with(
            a._stock_count
        )

        # the object's attributes are actually updated
        self.assertEqual(
            a._stock_value_amount,
            mock_stock_item.return_value.latest_price.multiply.return_value.amount,
        )
        self.assertEqual(
            a._stock_value_timestamp,
            mock_stock_item.return_value.latest_price.multiply.return_value.timestamp,
        )

        # provide price information

        # call `update_stock_value()` with parameter `item_price`
        a.update_stock_value(item_price=mock_stockingsmoney)

        # `multiply()` is called with the current `_stock_count` (=1)
        mock_stockingsmoney.multiply.assert_called_with(a._stock_count)

        # the object's attributes are actually updated
        self.assertEqual(
            a._stock_value_amount, mock_stockingsmoney.multiply.return_value.amount
        )
        self.assertEqual(
            a._stock_value_timestamp,
            mock_stockingsmoney.multiply.return_value.timestamp,
        )

        # provide item count

        # call `update_stock_value()` with parameter `item_count`
        a.update_stock_value(item_count=5)

        # `_stock_count` is actually updated
        self.assertEqual(a._stock_count, 5)

        # `multiply()` is called with the current `_stock_count` (=5)
        mock_stock_item.return_value.latest_price.multiply.assert_called_with(
            a._stock_count
        )

        # the object's attributes are actually updated
        self.assertEqual(
            a._stock_value_amount,
            mock_stock_item.return_value.latest_price.multiply.return_value.amount,
        )
        self.assertEqual(
            a._stock_value_timestamp,
            mock_stock_item.return_value.latest_price.multiply.return_value.timestamp,
        )

        # call `update_stock_value()` with parameters `item_price` and `item_count`
        a.update_stock_value(item_price=mock_stockingsmoney, item_count=3)

        # `_stock_count` is actually updated
        self.assertEqual(a._stock_count, 3)

        # `multiply()` is called with the current `_stock_count` (=3)
        mock_stockingsmoney.multiply.assert_called_with(a._stock_count)

        # the object's attributes are actually updated
        self.assertEqual(
            a._stock_value_amount, mock_stockingsmoney.multiply.return_value.amount
        )
        self.assertEqual(
            a._stock_value_timestamp,
            mock_stockingsmoney.multiply.return_value.timestamp,
        )
