# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.models.stock import StockItem

# app imports
from .util.testcases import StockingsTestCase


@tag("models", "stockitem")
class StockItemTest(StockingsTestCase):
    """Provide tests for class `StockItem`."""

    def test_property_currency(self):
        """Returns the object's currency, setter applies new currency to all price items."""

        # get a `StockItem` object
        a = StockItem()

        # getter
        b = a.currency
        self.assertEqual(a._currency, b)

        # setter
        # TODO: after implementation

        # deleting should not be possible
        with self.assertRaises(AttributeError):
            del a.currency

    @mock.patch("stockings.models.stock.StockItemPrice")
    def test_property_latest_price(self, mock_price_object):

        # get a `StockItem` object
        a = StockItem()

        # getter
        b = a.latest_price
        self.assertTrue(mock_price_object.get_latest_price.called)
        self.assertEqual(b, mock_price_object.get_latest_price.return_value)

        # setter
        a.latest_price = 1337
        self.assertTrue(mock_price_object.set_latest_price.called)

        # deleting should not be possible
        with self.assertRaises(AttributeError):
            del a.latest_price
