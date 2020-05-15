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

    @mock.patch("stockings.models.portfolio.StockingsMoney.multiply")
    @mock.patch("stockings.models.portfolio.PortfolioItem.stock_item")
    def test_update_stock_value(self, mock_stock_item, mock_multiply):
        """Updates `stock_value` while automatically retrieving required parameters."""

        # get a PortfolioItem object
        a = PortfolioItem()
        a._stock_count = 1

        # Set up the mock object.
        mock_latest_price = mock.PropertyMock(return_value=StockingsMoney(5, "EUR"))
        type(mock_stock_item).latest_price = mock_latest_price

        # call `update_stock_value()` without any parameter
        a.update_stock_value()

        # `latest_price` is determined internally
        self.assertTrue(mock_latest_price.called)
        # `multiply()` is called with the current `_stock_count` (=1)
        self.assertTrue(mock_multiply.called)
        mock_multiply.assert_called_with(1)
        # the object's attributes are actually updated
        self.assertEqual(a._stock_value_amount, mock_multiply.return_value.amount)
        self.assertEqual(a._stock_value_timestamp, mock_multiply.return_value.timestamp)
        # `_stock_count` did not change (still =1)
        self.assertEqual(a._stock_count, 1)
        mock_latest_price.reset_mock()
        mock_multiply.reset_mock()

        # call `update_stock_value()` with parameter `item_price`
        a.update_stock_value(item_price=StockingsMoney(5, "EUR"))

        # `latest_price` is provided as parameter
        self.assertFalse(mock_latest_price.called)
        # `multiply()` is called with the current `_stock_count` (=1)
        self.assertTrue(mock_multiply.called)
        mock_multiply.assert_called_with(1)
        # the object's attributes are actually updated
        self.assertEqual(a._stock_value_amount, mock_multiply.return_value.amount)
        self.assertEqual(a._stock_value_timestamp, mock_multiply.return_value.timestamp)
        # `_stock_count` did not change (still =1)
        self.assertEqual(a._stock_count, 1)
        mock_latest_price.reset_mock()
        mock_multiply.reset_mock()

        # call `update_stock_value()` with parameter `item_count`
        a.update_stock_value(item_count=5)

        # `latest_price` is determined internally
        self.assertTrue(mock_latest_price.called)
        # `multiply()` is called with the provided `item_count` (=5)
        self.assertTrue(mock_multiply.called)
        mock_multiply.assert_called_with(5)
        # the object's attributes are actually updated
        self.assertEqual(a._stock_value_amount, mock_multiply.return_value.amount)
        self.assertEqual(a._stock_value_timestamp, mock_multiply.return_value.timestamp)
        self.assertEqual(a._stock_count, 5)
        mock_latest_price.reset_mock()
        mock_multiply.reset_mock()

        # call `update_stock_value()` with parameters `item_price` and `item_count`
        a.update_stock_value(item_price=StockingsMoney(5, "EUR"), item_count=3)

        # `latest_price` is provided as parameter
        self.assertFalse(mock_latest_price.called)
        # `multiply()` is called with the provided `item_count` (=3)
        self.assertTrue(mock_multiply.called)
        mock_multiply.assert_called_with(3)
        # the object's attributes are actually updated
        self.assertEqual(a._stock_value_amount, mock_multiply.return_value.amount)
        self.assertEqual(a._stock_value_timestamp, mock_multiply.return_value.timestamp)
        self.assertEqual(a._stock_count, 3)

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_cash_in(self, mock_return_money):
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
    def test_cash_out(self, mock_return_money):
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
    def test_costs(self, mock_return_money):
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
    def test_currency(self, mock_portfolio):
        """Returns the object's `currency`."""

        # get a PortfolioItem object
        a = PortfolioItem()

        self.assertEqual(a.currency, mock_portfolio.return_value.currency)

        # setting the property is not possible
        with self.assertRaises(StockingsInterfaceError):
            a.currency = "FOO"

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_get_stock_value(self, mock_return_money):
        """Calls `_return_money()` with correct arguments."""

        # get a PortfolioItem object
        a = PortfolioItem()

        b = a._get_stock_value()
        self.assertTrue(mock_return_money.called)
        mock_return_money.assert_called_with(
            a._stock_value_amount, timestamp=a._stock_value_timestamp
        )
        self.assertEqual(b, mock_return_money.return_value)

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

    @skip
    @mock.patch("stockings.models.portfolio.StockingsMoney.convert")
    def test_set_currency_old(self, mock_convert):
        """Setting the object's currency converts all money-related attributes."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # Set up the mock object.
        mock_convert.return_value = StockingsMoney(1337, "FOO", timestamp="bar")

        a._set_currency("FOO")

        self.assertTrue(mock_convert.called)
        # `call_count` should be 4: cash_in, cash_out, costs, stock_value
        self.assertEqual(mock_convert.call_count, 4)
        # the object's attributes are actually updated
        self.assertEqual(a._cash_in_amount, mock_convert.return_value.amount)
        self.assertEqual(a._cash_in_amount, 1337)
        self.assertEqual(a._cash_in_timestamp, mock_convert.return_value.timestamp)
        self.assertEqual(a._cash_in_timestamp, "bar")
        self.assertEqual(a._cash_out_amount, mock_convert.return_value.amount)
        self.assertEqual(a._cash_out_amount, 1337)
        self.assertEqual(a._cash_out_timestamp, mock_convert.return_value.timestamp)
        self.assertEqual(a._cash_out_timestamp, "bar")
        self.assertEqual(a._costs_amount, mock_convert.return_value.amount)
        self.assertEqual(a._costs_amount, 1337)
        self.assertEqual(a._costs_timestamp, mock_convert.return_value.timestamp)
        self.assertEqual(a._costs_timestamp, "bar")
        self.assertEqual(a._stock_value_amount, mock_convert.return_value.amount)
        self.assertEqual(a._stock_value_amount, 1337)
        self.assertEqual(a._stock_value_timestamp, mock_convert.return_value.timestamp)
        self.assertEqual(a._stock_value_timestamp, "bar")
        self.assertEqual(a._currency, mock_convert.return_value.currency)
        self.assertEqual(a._currency, "FOO")

    @mock.patch("stockings.models.portfolio.PortfolioItem.update_stock_value")
    def test_stock_count(self, mock_update):
        """Setting the `stock_count` updates the `stock_value`."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # set the stock count
        a.stock_count = 5

        self.assertTrue(mock_update.called)
        mock_update.assert_called_with(item_count=5)

        # get the stock count
        self.assertEqual(a.stock_count, a._stock_count)

    @tag("signal-handler")
    def test_callback_stockitem_update_stock_value_raw(self):
        """Callback does not execute when called with `raw` = `True`."""

        # fourth parameter is `raw`
        self.assertIsNone(
            PortfolioItem.callback_stockitem_update_stock_value(
                None, None, None, True,  # sender, instance, created, raw
            )
        )

    @tag("signal-handler")
    @mock.patch("stockings.models.portfolio.PortfolioItem.objects")
    def test_callback_stockitem_update_stock_value_regular(self, mock_objects):
        """Callback determines `PortfolioItems` to update and calls `update_stock_value()`.

        While this unittest does hit all code lines of the method, actually
        nothing is done, because really everything is mocked.

        The test method checks, if all functions are called as required, but
        because all of Django's ORM database stuff is mocked aswell, it can
        not be determined, if the correct objects are retrieved from database
        and updated consequently.

        A functional / integration test should be used with an appropriate
        fixture to actually test the signal handler."""

        # Set up the mocks:
        # `mock_cls_stock_item` (is not actually used for assertions)
        mock_cls_stock_item = mock.MagicMock()

        # `mock_instance` has a property `latest_price`; assertion is done for
        # that property.
        mock_instance = mock.MagicMock()
        mock_instance_latest_price = mock.PropertyMock()
        type(mock_instance).latest_price = mock_instance_latest_price

        # This item will be returned from all Django database layer related functions.
        # See `mock_objects` for details.
        mock_item = mock.MagicMock()

        # `mock_objects` is the actual mock, that patches `PortfolioItem`'s `objects`
        # and basically intercepts all Django database ORM stuff.
        # The following code provides the `queryset`'s `iterator()` and returns
        # one single MagicMock (`mock_item`) on iteration.
        mock_objects.filter.return_value.iterator.return_value.__iter__.return_value = iter(
            [mock_item]
        )

        # actually call the method...
        PortfolioItem.callback_stockitem_update_stock_value(
            mock_cls_stock_item,  # sender
            mock_instance,  # instance
            False,  # created
            False,  # raw
        )

        self.assertTrue(mock_instance_latest_price.called)
        self.assertTrue(mock_item.update_stock_value.called)
        self.assertTrue(mock_item.save.called)

    @tag("signal-handler")
    def test_callback_trade_apply_trade_noop(self):
        """Callback does not execute when called with `raw` = `True` or `created` = `False`."""

        # Fourth parameter is `raw`... Always returns `None`
        self.assertIsNone(
            PortfolioItem.callback_trade_apply_trade(
                None, None, None, True,  # sender, instance, created, raw
            )
        )
        self.assertIsNone(
            PortfolioItem.callback_trade_apply_trade(
                None, None, False, True,  # sender, instance, created, raw
            )
        )
        self.assertIsNone(
            PortfolioItem.callback_trade_apply_trade(
                None, None, True, True,  # sender, instance, created, raw
            )
        )

        # Third parameter is `created`... Returns `None` if `created` = `False`
        self.assertIsNone(
            PortfolioItem.callback_trade_apply_trade(
                None, None, False, True,  # sender, instance, created, raw
            )
        )
        self.assertIsNone(
            PortfolioItem.callback_trade_apply_trade(
                None, None, False, False,  # sender, instance, created, raw
            )
        )

    @tag("signal-handler")
    @mock.patch("stockings.models.portfolio.PortfolioItem.objects")
    def test_callback_trade_apply_trade_buy(self, mock_objects):
        """Callback updates attributes of `PortfolioItem` for buy operations.

        While this unittest does hit all code lines of the method, actually
        nothing is done, because really everything is mocked.

        The test method checks, if all functions are called as required, but
        because all of Django's ORM database stuff is mocked aswell, it can
        not be determined, if the correct objects are retrieved from database
        and updated consequently.

        A functional / integration test should be used with an appropriate
        fixture to actually test the signal handler."""

        # Set up the mocks:
        # `mock_cls_stock_item` (is not actually used for assertions)
        mock_cls_stock_item = mock.MagicMock()

        # `mock_instance` needs a property `trade_type`
        mock_instance = mock.MagicMock()
        type(mock_instance).trade_type = mock.PropertyMock(return_value="BUY")

        # This item will be returned from all Django database layer related functions.
        # See `mock_objects` for details.
        mock_item = mock.MagicMock()

        # `mock_objects` is the actual mock, that patches `PortfolioItem`'s `objects`
        # and basically intercepts all Django database ORM stuff.
        mock_objects.get_or_create.return_value = (mock_item, True)

        PortfolioItem.callback_trade_apply_trade(
            mock_cls_stock_item, mock_instance, True, False,
        )

        self.assertTrue(mock_item.update_costs.called)
        self.assertTrue(mock_item.update_cash_in.called)
        self.assertFalse(mock_item.update_cash_out.called)
        self.assertTrue(mock_item.update_stock_value.called)
        self.assertTrue(mock_item.save.called)

    @tag("signal-handler")
    @mock.patch("stockings.models.portfolio.PortfolioItem.objects")
    def test_callback_trade_apply_trade_sell_valid(self, mock_objects):
        """Callback updates attributes of `PortfolioItem` for sell operations.

        While this unittest does hit all code lines of the method, actually
        nothing is done, because really everything is mocked.

        The test method checks, if all functions are called as required, but
        because all of Django's ORM database stuff is mocked aswell, it can
        not be determined, if the correct objects are retrieved from database
        and updated consequently.

        A functional / integration test should be used with an appropriate
        fixture to actually test the signal handler."""

        # Set up the mocks:
        # `mock_cls_stock_item` (is not actually used for assertions)
        mock_cls_stock_item = mock.MagicMock()

        # `mock_instance` needs a property `trade_type`
        mock_instance = mock.MagicMock()
        type(mock_instance).trade_type = mock.PropertyMock(return_value="SELL")

        # This item will be returned from all Django database layer related functions.
        # See `mock_objects` for details.
        mock_item = mock.MagicMock()

        # `mock_objects` is the actual mock, that patches `PortfolioItem`'s `objects`
        # and basically intercepts all Django database ORM stuff.
        mock_objects.get_or_create.return_value = (mock_item, False)

        PortfolioItem.callback_trade_apply_trade(
            mock_cls_stock_item, mock_instance, True, False,
        )

        self.assertTrue(mock_item.update_costs.called)
        self.assertFalse(mock_item.update_cash_in.called)
        self.assertTrue(mock_item.update_cash_out.called)
        self.assertTrue(mock_item.update_stock_value.called)
        self.assertTrue(mock_item.save.called)

    @tag("signal-handler")
    @mock.patch("stockings.models.portfolio.PortfolioItem.objects")
    def test_callback_trade_apply_trade_sell_invalid(self, mock_objects):
        """Callback raises error, if not available stock is sold.

        While this unittest does hit all code lines of the method, actually
        nothing is done, because really everything is mocked.

        The test method checks, if all functions are called as required, but
        because all of Django's ORM database stuff is mocked aswell, it can
        not be determined, if the correct objects are retrieved from database
        and updated consequently.

        A functional / integration test should be used with an appropriate
        fixture to actually test the signal handler."""

        # Set up the mocks:
        # `mock_cls_stock_item` (is not actually used for assertions)
        mock_cls_stock_item = mock.MagicMock()

        # `mock_instance` needs a property `trade_type`
        mock_instance = mock.MagicMock()
        type(mock_instance).trade_type = mock.PropertyMock(return_value="SELL")

        # This item will be returned from all Django database layer related functions.
        # See `mock_objects` for details.
        mock_item = mock.MagicMock()

        # `mock_objects` is the actual mock, that patches `PortfolioItem`'s `objects`
        # and basically intercepts all Django database ORM stuff.
        mock_objects.get_or_create.return_value = (mock_item, True)

        with self.assertRaises(RuntimeError):
            PortfolioItem.callback_trade_apply_trade(
                mock_cls_stock_item, mock_instance, True, False,
            )
