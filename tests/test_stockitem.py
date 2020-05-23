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

    def test_to_string(self):
        """Return ISIN as a fallback."""

        # get a `StockItem` object
        a = StockItem()

        self.assertEqual(a.isin, a.__str__())

        a.name = "foo"

        self.assertEqual("{} ({})".format(a.name, a.isin), a.__str__())

    @mock.patch(
        "stockings.models.stock.StockItem.stockitemprice_set",
        new_callable=mock.PropertyMock,
    )
    def test_property_currency(self, mock_stockitemprice_set):
        """Returns the object's currency, setter applies new currency to all price items."""

        # get a `StockItem` object
        a = StockItem()

        # getter
        b = a.currency
        self.assertEqual(a._currency, b)

        # setter
        mock_item = mock.MagicMock()
        mock_stockitemprice_set.return_value.iterator.return_value.__iter__.return_value = iter(
            [mock_item]
        )

        a.currency = "FOO"

        mock_item._apply_new_currency.assert_called_with("FOO")
        self.assertEqual(a.currency, "FOO")

        # deleting should not be possible
        with self.assertRaises(AttributeError):
            del a.currency

    @mock.patch(
        "stockings.models.stock.StockItem.portfolioitem_set",
        new_callable=mock.PropertyMock,
    )
    def test_property_is_active(self, mock_portfolioitem_set):
        """Determine `is_active` status based on `PortfolioItem `objects`."""

        # get a `StockItem` object
        a = StockItem()

        mock_portfolioitem_set.return_value.filter.return_value.count.return_value = 0
        self.assertFalse(a.is_active)

        mock_portfolioitem_set.return_value.filter.return_value.count.return_value = 5
        self.assertTrue(a.is_active)

        with self.assertRaises(AttributeError):
            a.is_active = False

        with self.assertRaises(AttributeError):
            del a.is_active

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
