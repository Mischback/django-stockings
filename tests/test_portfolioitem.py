# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.models.portfolio import PortfolioItem

# app imports
from .util.testcases import StockingsTestCase


@tag("models")
class PortfolioItemTest(StockingsTestCase):
    @mock.patch("stockings.data.now")
    def test_return_money(self, mock_now):

        # get a PortfolioItem object
        a = PortfolioItem()

        # Providing a `timestamp` manually
        b = a._return_money(1339, timestamp="bar")
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 1339)
        self.assertEqual(b.currency, a._currency)
        self.assertEqual(mock_now.called, False)
        self.assertEqual(b.timestamp, "bar")

        # Only provide `amount`, let `currency` and `timestamp` be provided
        # automatically.
        b = a._return_money(1337)
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 1337)
        self.assertEqual(b.currency, a._currency)
        self.assertEqual(mock_now.called, True)
        self.assertEqual(b.timestamp, mock_now.return_value)

        # Providing a `currency` manually.
        b = a._return_money(1338, currency="FOO")
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 1338)
        self.assertNotEqual(b.currency, a._currency)
        self.assertEqual(b.currency, "FOO")
        self.assertEqual(mock_now.called, True)
        self.assertEqual(b.timestamp, mock_now.return_value)
