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

    @mock.patch("stockings.models.portfolio.StockingsMoney.add")
    def test_update_cash_in(self, mock_add):

        # get a PortfolioItem object
        a = PortfolioItem()

        # Set up the mock
        # Please note, that `timestamp` is set to an illegal value, that may
        # not be stored into the database. But it should be sufficient for
        # testing.
        mock_add.return_value = StockingsMoney(5, "EUR", timestamp="foo")

        # Actually it is assumed, that the method is called with a `StockingsMoney`
        # instance, but for this test, that part is mocked out anyway...
        a.update_cash_in("StockingsMoney")

        self.assertTrue(mock_add.called)
        self.assertEqual(a._cash_in_amount, 5)
        self.assertEqual(a._cash_in_timestamp, "foo")

    @mock.patch("stockings.models.portfolio.StockingsMoney.add")
    def test_update_cash_out(self, mock_add):

        # get a PortfolioItem object
        a = PortfolioItem()

        # Set up the mock
        # Please note, that `timestamp` is set to an illegal value, that may
        # not be stored into the database. But it should be sufficient for
        # testing.
        mock_add.return_value = StockingsMoney(5, "EUR", timestamp="foo")

        # Actually it is assumed, that the method is called with a `StockingsMoney`
        # instance, but for this test, that part is mocked out anyway...
        a.update_cash_out("StockingsMoney")

        self.assertTrue(mock_add.called)
        self.assertEqual(a._cash_out_amount, 5)
        self.assertEqual(a._cash_out_timestamp, "foo")

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_get_cash_in(self, mock_return_money):
        """Calls `_return_money()` with correct arguments."""

        # get a PortfolioItem object
        a = PortfolioItem()

        b = a._get_cash_in()
        self.assertTrue(mock_return_money.called)
        mock_return_money.assert_called_with(
            a._cash_in_amount, timestamp=a._cash_in_timestamp
        )
        self.assertEqual(b, mock_return_money.return_value)

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_get_cash_out(self, mock_return_money):
        """Calls `_return_money()` with correct arguments."""

        # get a PortfolioItem object
        a = PortfolioItem()

        b = a._get_cash_out()
        self.assertTrue(mock_return_money.called)
        mock_return_money.assert_called_with(
            a._cash_out_amount, timestamp=a._cash_out_timestamp
        )
        self.assertEqual(b, mock_return_money.return_value)

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_get_costs(self, mock_return_money):
        """Calls `_return_money()` with correct arguments."""

        # get a PortfolioItem object
        a = PortfolioItem()

        b = a._get_costs()
        self.assertTrue(mock_return_money.called)
        mock_return_money.assert_called_with(
            a._costs_amount, timestamp=a._costs_timestamp
        )
        self.assertEqual(b, mock_return_money.return_value)

    def test_get_currency(self):
        """Returns the object's `_currency`."""

        # get a PortfolioItem object
        a = PortfolioItem()

        self.assertEqual(a._get_currency(), a._currency)

        a._currency = "FOO"

        self.assertEqual(a._get_currency(), a._currency)

    def test_get_stock_count(self):
        """Returns the object's `_stock_count`."""

        # get a PortfolioItem object
        a = PortfolioItem()

        self.assertEqual(a._get_stock_count(), a._stock_count)

        a._stock_count = 1337

        self.assertEqual(a._get_stock_count(), a._stock_count)

    @mock.patch("stockings.models.portfolio.PortfolioItem._return_money")
    def test_get_stock_value(self, mock_return_money):
        """Calls `_return_money()` with correct arguments."""

        # get a PortfolioItem object
        a = PortfolioItem()

        b = a._get_stock_value()
        self.assertTrue(mock_return_money.called)
        mock_return_money.assert_called_with(
            a._stock_value_amount, timestamp=a._stock_value_timestamp
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
        self.assertTrue(mock_now.called)
        self.assertEqual(b.timestamp, mock_now.return_value)
        mock_now.reset_mock()

        # Providing a `currency` manually.
        b = a._return_money(1338, currency="FOO")
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 1338)
        self.assertNotEqual(b.currency, a._currency)
        self.assertEqual(b.currency, "FOO")
        self.assertTrue(mock_now.called)
        self.assertEqual(b.timestamp, mock_now.return_value)
        mock_now.reset_mock()

        # Providing a `timestamp` manually
        b = a._return_money(1339, timestamp="bar")
        self.assertIsInstance(b, StockingsMoney)
        self.assertEqual(b.amount, 1339)
        self.assertEqual(b.currency, a._currency)
        self.assertFalse(mock_now.called)
        self.assertEqual(b.timestamp, "bar")
