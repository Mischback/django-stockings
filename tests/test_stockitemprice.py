# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
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
