# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError

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
            a = StockingsMoney(currency="EUR")

        a = StockingsMoney(1337, "EUR")
        self.assertEqual(a.amount, 1337)
        self.assertEqual(a.currency, "EUR")

    @mock.patch("stockings.data.now")
    def test_constructor_handles_timestamp(self, mock_now):
        """Does the constructor correctly handle timestamps?"""

        a = StockingsMoney(1337, "EUR", timestamp="foobar")

        # Note: the mocked `now()` isn't actually called.
        self.assertEqual(mock_now.called, False)
        self.assertEqual(a.timestamp, "foobar")

        a = StockingsMoney(1337, "EUR")

        # Note: the mocked `now()` is used to provide the timestamp.
        self.assertEqual(mock_now.called, True)
        self.assertEqual(a.timestamp, mock_now.return_value)

    def test_add_validates_summand(self):
        """Does `add()` correctly fail for unsupported input?

        This test case checks various object types as input for `summand` and
        then checks, if strings are rejected for `summand.amount`.

        It is **not** tested, if unexpected object types for `summand.currency`
        are handled correctly, because this is out of scope for `add()`.
        Instead, this will have to be done in `convert()`."""

        # create a (valid) `StockingsMoney` object
        a = StockingsMoney(1337, "EUR")

        # will not work with INT
        with self.assertRaises(StockingsInterfaceError):
            a.add(5)

        # will not work with STRING
        with self.assertRaises(StockingsInterfaceError):
            a.add("5")

        # will not work with TUPLE
        with self.assertRaises(StockingsInterfaceError):
            a.add((5, "foo"))

        # will not work with DICT
        with self.assertRaises(StockingsInterfaceError):
            a.add({"foo": "bar", "bar": "foo"})

        # will not work with DICT, even if the keys are right
        with self.assertRaises(StockingsInterfaceError):
            a.add({"amount": 5, "currency": "EUR"})

        # `amount` has to be a number
        with self.assertRaises(StockingsInterfaceError):
            a.add(StockingsMoney("foo", "EUR"))

        # `amount` has to be a number
        with self.assertRaises(StockingsInterfaceError):
            a.add(StockingsMoney("5", "EUR"))

        # `amount` is INT
        b = a.add(StockingsMoney(5, "EUR"))
        self.assertEqual(b.amount, 1337 + 5)

        # `amount` is FLOAT
        b = a.add(StockingsMoney(1.337, "EUR"))
        self.assertEqual(b.amount, 1337 + 1.337)

    @mock.patch("stockings.data.StockingsMoney.convert")
    def test_add_converts_summand(self, mock_convert):
        """Does `add()` correctly apply currency conversion while adding?"""

        # set up the mock
        mock_convert.return_value = StockingsMoney(6, "EUR")

        # create a (valid) `StockingsMoney` object
        a = StockingsMoney(1337, "EUR")

        # conversion is required; the actual call is mocked
        b = a.add(StockingsMoney(5, "FOO"))

        self.assertEqual(mock_convert.called, True)
        self.assertEqual(b.amount, 1337 + 6)

    @mock.patch("stockings.data.now")
    def test_add_updates_timestamp(self, mock_now):
        """Does `add()` updates the timestamp?"""

        # create a (valid) `StockingsMoney` object
        a = StockingsMoney(1337, "EUR", timestamp="foo")

        b = a.add(StockingsMoney(5, "EUR", timestamp="bar"))

        self.assertEqual(mock_now.called, True)
        self.assertEqual(b.timestamp, mock_now.return_value)

    def test_currency_conversion(self):
        """Currency conversion is currently not implemented, an error should be raised."""

        a = StockingsMoney(1337, "EUR")
        with self.assertRaises(NotImplementedError):
            a.convert("USD")
