# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.models.portfolio import Portfolio

# app imports
from ..util.testcases import StockingsTestCase


@tag("models", "portfolio")
class PortfolioTest(StockingsTestCase):
    """Provide tests for `Portfolio` class."""

    @mock.patch("stockings.models.portfolio.PortfolioItem.objects")
    def test_property_currency(self, mock_objects):
        """Property's getter works, setter applies currency to all associated `PortfolioItem`s."""

        # get a Portfolio object
        a = Portfolio()

        self.assertEqual(a._currency, a.currency)

        mock_item = mock.MagicMock()
        mock_objects.filter.return_value.iterator.return_value.__iter__.return_value = iter(
            [mock_item]
        )

        a.currency = "FOO"

        mock_item._apply_new_currency.assert_called_with("FOO")
        self.assertTrue(mock_item.save.called)

        with self.assertRaises(AttributeError):
            del a.currency
