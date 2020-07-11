"""Provides tests for module `stockings.models.stockitemprice`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.models.stockitemprice import StockItemPrice

# app imports
from ..util.testcases import StockingsTestCase


@tag("models", "stockitemprice", "unittest")
class StockItemPriceTest(StockingsTestCase):
    """Provide tests for class `StockItemPrice`."""

    @mock.patch(
        "stockings.models.stockitemprice.StockItemPrice.price",
        new_callable=mock.PropertyMock,
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
        "stockings.models.stockitemprice.StockItemPrice.stockings_manager",
        new_callable=mock.PropertyMock,
    )
    def test_get_latest_price(self, mock_manager):
        """Return the most recent object's price as StockingsMoney instance."""
        a = StockItemPrice.get_latest_price("FOO")
        self.assertTrue(mock_manager.return_value.get_latest_price_object.called)
        mock_manager.return_value.get_latest_price_object.assert_called_with(
            stockitem="FOO"
        )
        self.assertEqual(
            a, mock_manager.return_value.get_latest_price_object.return_value.price
        )
