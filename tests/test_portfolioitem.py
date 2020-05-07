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
    """Provide tests for PortfolioItem class."""

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_get_cash_in(self, mock_return_money):
        """Calls `_return_money()` with correct arguments."""

        # get a PortfolioItem object
        a = PortfolioItem()

        b = a._get_stock_value()
        self.assertEqual(mock_return_money.called, True)
        self.assertTrue(
            mock_return_money.called_with(
                a._cash_in_amount, timestamp=a._cash_in_timestamp
            ),
            True,
        )
        self.assertEqual(b, mock_return_money.return_value)

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_get_cash_out(self, mock_return_money):
        """Calls `_return_money()` with correct arguments."""

        # get a PortfolioItem object
        a = PortfolioItem()

        b = a._get_stock_value()
        self.assertEqual(mock_return_money.called, True)
        self.assertTrue(
            mock_return_money.called_with(
                a._cash_out_amount, timestamp=a._cash_out_timestamp
            ),
            True,
        )
        self.assertEqual(b, mock_return_money.return_value)

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_get_costs(self, mock_return_money):
        """Calls `_return_money()` with correct arguments."""

        # get a PortfolioItem object
        a = PortfolioItem()

        b = a._get_stock_value()
        self.assertEqual(mock_return_money.called, True)
        self.assertTrue(
            mock_return_money.called_with(
                a._costs_amount, timestamp=a._costs_timestamp
            ),
            True,
        )
        self.assertEqual(b, mock_return_money.return_value)

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_get_stock_value(self, mock_return_money):
        """Calls `_return_money()` with correct arguments."""

        # get a PortfolioItem object
        a = PortfolioItem()

        b = a._get_stock_value()
        self.assertEqual(mock_return_money.called, True)
        self.assertTrue(
            mock_return_money.called_with(
                a._stock_value_amount, timestamp=a._stock_value_timestamp
            ),
            True,
        )
        self.assertEqual(b, mock_return_money.return_value)

    def test_is_active(self):
        """Returns True/False depending on `_stock_count`."""

        # get a PortfolioItem object
        a = PortfolioItem()

        self.assertEqual(a._stock_count, 0)
        self.assertFalse(a._is_active())

        a._stock_count = 1
        self.assertTrue(a._is_active())

    @mock.patch("stockings.data.now")
    def test_return_money(self, mock_now):
        """Returns correctly populated `StockingsMoney` object."""

        # get a PortfolioItem object
        a = PortfolioItem()

        # Only provide `amount`, let `currency` and `timestamp` be provided
        # automatically.
        b = a._return_money(1337)
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 1337)
        self.assertEqual(b.currency, a._currency)
        self.assertEqual(mock_now.called, True)
        self.assertEqual(b.timestamp, mock_now.return_value)
        mock_now.reset_mock()

        # Providing a `currency` manually.
        b = a._return_money(1338, currency="FOO")
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 1338)
        self.assertNotEqual(b.currency, a._currency)
        self.assertEqual(b.currency, "FOO")
        self.assertEqual(mock_now.called, True)
        self.assertEqual(b.timestamp, mock_now.return_value)
        mock_now.reset_mock()

        # Providing a `timestamp` manually
        b = a._return_money(1339, timestamp="bar")
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 1339)
        self.assertEqual(b.currency, a._currency)
        self.assertEqual(mock_now.called, False)
        self.assertEqual(b.timestamp, "bar")
