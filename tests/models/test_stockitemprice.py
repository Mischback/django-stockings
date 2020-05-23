# Python imports
from datetime import datetime, timedelta
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.stock import StockItemPrice

# app imports
from ..util.testcases import StockingsTestCase


@tag("models", "stockitemprice")
class StockItemPriceTest(StockingsTestCase):
    """Provide tests for class `StockItemPrice`."""

    @mock.patch(
        "stockings.models.stock.StockItemPrice.price", new_callable=mock.PropertyMock
    )
    def test_apply_new_currency(self, mock_price):
        """Call convert and apply new amount."""

        # get a `StockItemPrice` object
        a = StockItemPrice()

        a._apply_new_currency("FOO")

        mock_price.return_value.convert.assert_called_with("FOO")
        self.assertEqual(
            a._price_amount, mock_price.return_value.convert.return_value.amount
        )

    @mock.patch(
        "stockings.models.stock.StockItemPrice.objects", new_callable=mock.PropertyMock
    )
    def test_get_latest_price(self, mock_objects):
        """Return the most recent object's price as StockingsMoney instance."""

        a = StockItemPrice.get_latest_price("FOO")
        self.assertTrue(mock_objects.return_value.get_latest_price_object.called)
        mock_objects.return_value.get_latest_price_object.assert_called_with(
            stock_item="FOO"
        )
        self.assertEqual(
            a, mock_objects.return_value.get_latest_price_object.return_value.price
        )

    @mock.patch(
        "stockings.models.stock.StockItemPrice.stock_item",
        new_callable=mock.PropertyMock,
    )
    def test_property_currency(self, mock_stock_item):

        # get a StockItemPrice object
        a = StockItemPrice()

        # getter
        b = a.currency
        self.assertEqual(b, mock_stock_item.return_value.currency)

        # setter
        with self.assertRaises(StockingsInterfaceError):
            a.currency = "FOO"

        # deleter
        with self.assertRaises(AttributeError):
            del a.currency

    @mock.patch("stockings.models.stock.StockingsMoney", autospec=True)
    @mock.patch(
        "stockings.models.stock.StockItemPrice.stock_item",
        new_callable=mock.PropertyMock,
    )
    def test_property_price(self, mock_stock_item, mock_stockingsmoney):

        # get a StockItemPrice object
        a = StockItemPrice()

        # getter
        b = a.price
        mock_stockingsmoney.assert_called_with(
            a._price_amount, a.currency, a._price_timestamp
        )
        self.assertIsInstance(b, StockingsMoney)

        # setter
        # `_timestamp` == `value.timestamp`, no action!
        mock_stockingsmoney.timestamp = a._price_timestamp
        a.price = mock_stockingsmoney
        self.assertNotEqual(a._price_amount, mock_stockingsmoney.amount)

        mock_stockingsmoney.timestamp = a._price_timestamp + timedelta(days=1)
        a.price = mock_stockingsmoney
        self.assertEqual(a._price_amount, mock_stockingsmoney.amount)
        mock_stockingsmoney.convert.assert_called_with(a.currency)

        mock_stockingsmoney.reset_mock()
        mock_stockingsmoney.currency = a.currency
        mock_stockingsmoney.timestamp = a._price_timestamp + timedelta(days=1)
        a.price = mock_stockingsmoney
        self.assertEqual(a._price_amount, mock_stockingsmoney.amount)
        self.assertFalse(mock_stockingsmoney.convert.called)

        # deleter
        with self.assertRaises(AttributeError):
            del a.price

    @mock.patch("stockings.models.stock.StockingsMoney", autospec=True)
    @mock.patch(
        "stockings.models.stock.StockItemPrice.objects", new_callable=mock.PropertyMock
    )
    def test_set_latest_price(self, mock_objects, mock_stockingsmoney):
        """Retrieve required `StockItemPrice` object and set new price information."""

        mock_latest_obj = mock.MagicMock()
        mock_latest_obj._price_timestamp = datetime(2020, 5, 23, hour=21, minute=0)
        mock_objects.return_value.get_latest_price_object.return_value = mock_latest_obj
        mock_stockingsmoney.timestamp = datetime(2020, 5, 23, hour=20, minute=0)

        # `_timestamp` of the latest object is more recent than the `timestamp`
        # of `value`, no action is performed!
        StockItemPrice.set_latest_price("FOO", mock_stockingsmoney)
        mock_objects.return_value.get_latest_price_object.assert_called_with(
            stock_item="FOO"
        )
        self.assertFalse(mock_latest_obj.save.called)

        mock_latest_obj.reset_mock()
        mock_objects.reset_mock()
        mock_stockingsmoney.timestamp = datetime(2020, 5, 23, hour=22, minute=0)

        # `timestamp` of `value` is more recent, but still on the same day
        StockItemPrice.set_latest_price("FOO", mock_stockingsmoney)
        self.assertFalse(mock_objects.create.called)
        mock_latest_obj._set_price.assert_called_with(mock_stockingsmoney)
        self.assertTrue(mock_latest_obj.save.called)

        mock_latest_obj.reset_mock()
        mock_objects.reset_mock()
        mock_stockingsmoney.timestamp = datetime(2020, 5, 24, hour=7, minute=0)

        # `timestamp` of `value` is on the next day
        StockItemPrice.set_latest_price("FOO", mock_stockingsmoney)
        mock_objects.return_value.create.assert_called_with(
            stock_item="FOO", _price_timestamp=mock_stockingsmoney.timestamp
        )
        mock_objects.return_value.create.return_value._set_price.assert_called_with(
            mock_stockingsmoney
        )
        self.assertTrue(mock_objects.return_value.create.return_value.save.called)
