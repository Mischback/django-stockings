"""Provides tests for module `stockings.models.stockitem`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.models.stockitem import StockItem

# app imports
from ..util.testcases import StockingsTestCase


@tag("models", "stockitem", "unittest")
class StockItemTest(StockingsTestCase):
    """Provide tests for class `StockItem`."""

    def test_to_string(self):
        """Return ISIN as a fallback."""
        # get a StockItem object
        a = StockItem()

        self.assertEqual(a.isin, a.__str__())

        a.name = "foo"

        self.assertEqual("{} ({})".format(a.name, a.isin), a.__str__())

    def test_currency_get(self):
        """Property's getter simply returns the stored attribute."""
        # get a StockItem object
        a = StockItem()

        self.assertEqual(a.currency, a._currency)

    @mock.patch("stockings.models.stockitem.StockItem.save")
    @mock.patch("stockings.models.stockitem.StockItem.prices")
    def test_currency_set(self, mock_prices, mock_save):
        """Property's setter updates associated `StockItemPrice` objects."""
        # set up the mock
        mock_item = mock.MagicMock()
        mock_prices.iterator.return_value.__iter__.return_value = iter([mock_item])

        # get a StockItem object
        a = StockItem()

        a.currency = "FOO"

        mock_item._apply_new_currency.assert_called_with("FOO")
        self.assertTrue(mock_item.save.called)

        self.assertEqual(a._currency, "FOO")
        self.assertTrue(mock_save.called)

    def test_currency_del(self):
        """Property can not be deleted."""
        # get a StockItem object
        a = StockItem()

        with self.assertRaises(AttributeError):
            del a.currency
