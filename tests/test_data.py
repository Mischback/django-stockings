# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney

# app imports
from .util.testcases import StockingsTestCase


class StockingsMoneyTest(StockingsTestCase):
    """Provides tests for the ``StockingsMoney`` class."""

    def test_constructor_requires_amount_currency(self):
        """Does the constructor enforce required values?

        Yeah, this is kind of redundant, because it should be a given fact,
        that Python works. But for the sake of completeness and to be prepared
        for further extensions of the constructor, here we go."""

        with self.assertRaises(TypeError):
            a = StockingsMoney()

        with self.assertRaises(TypeError):
            a = StockingsMoney(1337)

        with self.assertRaises(TypeError):
            a = StockingsMoney(amount=1337)

        with self.assertRaises(TypeError):
            a = StockingsMoney(currency='EUR')

        a = StockingsMoney(1337, 'EUR')
        self.assertEqual(a.amount, 1337)
        self.assertEqual(a.currency, 'EUR')

    @mock.patch('stockings.data.now')
    def test_constructor_accepts_timestamp(self, mock_now):
        """Does the constructor accepts the provided timestamp?

        Please note the patch: Actually, no timestamp is provided!"""

        a = StockingsMoney(1337, 'EUR', timestamp='foobar')

        # The mocked `now()` isn't called.
        self.assertEqual(mock_now.called, False)
        self.assertEqual(a.timestamp, 'foobar')

    @mock.patch('stockings.data.now')
    def test_constructor_provide_timestamp(self, mock_now):
        """Does the constructor automatically provide a timestamp?

        Please note the patch: Actually, no timestamp is provided!"""

        a = StockingsMoney(1337, 'EUR')

        self.assertEqual(mock_now.called, True)
        self.assertEqual(a.timestamp, mock_now.return_value)

    def test_currency_conversion(self):
        """Currency conversion is currently not implemented, an error should be raised."""
        a = StockingsMoney(1337, 'EUR')
        with self.assertRaises(NotImplementedError):
            a.convert('USD')
