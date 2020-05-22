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

    def test_property_latest_price(self):
        pass
