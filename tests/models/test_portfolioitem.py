# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.portfolio import PortfolioItem

# app imports
from ..util.testcases import StockingsTestCase


@tag("models", "portfolioitem")
class PortfolioItemTest(StockingsTestCase):
    """Provide tests for PortfolioItem class."""

    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.cash_in",
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.cash_out",
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.costs", new_callable=mock.PropertyMock
    )
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.stock_value",
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.portfolio",
        new_callable=mock.PropertyMock,
    )
    def test_apply_new_currency(
        self, mock_portfolio, mock_stock_value, mock_costs, mock_cash_out, mock_cash_in,
    ):
        """Setting a new currency recalculates all money-related amounts."""

        # get PortfolioItem object
        a = PortfolioItem()

        a._apply_new_currency("FOO")

        # Assess, if the conversion method is called and the `amount` updated.
        mock_cash_in.return_value.convert.assert_called_with("FOO")
        self.assertEqual(
            a._cash_in_amount, mock_cash_in.return_value.convert.return_value.amount
        )
        mock_cash_out.return_value.convert.assert_called_with("FOO")
        self.assertEqual(
            a._cash_out_amount, mock_cash_out.return_value.convert.return_value.amount
        )
        mock_costs.return_value.convert.assert_called_with("FOO")
        self.assertEqual(
            a._costs_amount, mock_costs.return_value.convert.return_value.amount
        )
        mock_stock_value.return_value.convert.assert_called_with("FOO")
        self.assertEqual(
            a._stock_value_amount,
            mock_stock_value.return_value.convert.return_value.amount,
        )

    @mock.patch("stockings.models.trade.Trade", autospec=True)
    @mock.patch("stockings.models.portfolio.PortfolioItem.update_stock_value")
    @mock.patch("stockings.models.portfolio.PortfolioItem.update_cash_out")
    @mock.patch("stockings.models.portfolio.PortfolioItem.update_cash_in")
    @mock.patch("stockings.models.portfolio.PortfolioItem.update_costs")
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.portfolio",
        new_callable=mock.PropertyMock,
    )
    def test_apply_trade(
        self,
        mock_portfolio,
        mock_update_costs,
        mock_update_cash_in,
        mock_update_cash_out,
        mock_update_stock_value,
        mock_trade,
    ):
        """Method calls the methods to update money-related fields."""

        # get PortfolioItem object
        a = PortfolioItem()

        mock_trade.trade_type = "BUY"
        mock_trade.item_count = 1

        a.apply_trade(mock_trade, skip_integrity_check=True)

        mock_update_costs.assert_called_with(mock_trade.costs)
        mock_update_cash_in.assert_called_with(mock_trade.price.multiply.return_value)
        mock_update_stock_value.assert_called_with(
            item_count=a._stock_count + mock_trade.item_count,
            item_price=mock_trade.price,
        )

        mock_trade.reset_mock()
        mock_trade.trade_type = "SELL"
        mock_trade.item_count = 1
        a._stock_count = 4

        a.apply_trade(mock_trade, skip_integrity_check=True)

        mock_update_costs.assert_called_with(mock_trade.costs)
        mock_update_cash_out.assert_called_with(mock_trade.price.multiply.return_value)
        mock_update_stock_value.assert_called_with(
            item_count=a._stock_count - mock_trade.item_count,
            item_price=mock_trade.price,
        )

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

        self.assertTrue(mock_item.apply_trade.called)
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

        self.assertTrue(mock_item.apply_trade.called)
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

        with self.assertRaises(AttributeError):
            del a.cash_in

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

        with self.assertRaises(AttributeError):
            del a.cash_out

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

        with self.assertRaises(AttributeError):
            del a.costs

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

        with self.assertRaises(AttributeError):
            del a.currency

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

        with self.assertRaises(AttributeError):
            del a.stock_count

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

        with self.assertRaises(AttributeError):
            del a.stock_value

    @mock.patch("django.apps.apps.get_model")
    @mock.patch("stockings.models.portfolio.PortfolioItem.apply_trade")
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.portfolio",
        new_callable=mock.PropertyMock,
    )
    @mock.patch(
        "stockings.models.portfolio.PortfolioItem.stock_item",
        new_callable=mock.PropertyMock,
    )
    def test_reapply_trades(
        self, mock_stock_item, mock_portfolio, mock_apply_trade, mock_objects
    ):
        """Reapplies all associated `Trade` objects using `apply_trade()`."""

        mock_trade = mock.MagicMock()

        # `mock_objects` is the actual mock, that patches `PortfolioItem`'s `objects`
        # and basically intercepts all Django database ORM stuff.
        # The following code provides the `queryset`'s `iterator()` and returns
        # one single MagicMock (`mock_item`) on iteration.
        mock_objects.return_value.objects.filter.return_value.order_by.return_value.iterator.return_value.__iter__.return_value = iter(  # noqa: E501
            [mock_trade]
        )

        # get a PortfolioItem object
        a = PortfolioItem()

        # actually call the method
        a.reapply_trades()

        self.assertTrue(mock_apply_trade.called)
        mock_apply_trade.assert_called_with(mock_trade, skip_integrity_check=True)

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
