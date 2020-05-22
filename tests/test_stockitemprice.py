# Python imports
from datetime import timedelta
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.stock import StockItemPrice

# app imports
from .util.testcases import StockingsTestCase


@tag("models", "stockitemprice")
class StockItemTest(StockingsTestCase):
    """Provide tests for class `StockItemPrice`."""

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
