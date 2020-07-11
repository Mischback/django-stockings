"""Provides tests for module `stockings.models.stockitem`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.models.stockitem import StockItem

# app imports
from ..util.testcases import StockingsORMTestCase, StockingsTestCase


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

    @mock.patch("stockings.models.stockitem.StockItem.currency")
    @mock.patch("stockings.models.stockitem.StockItem.prices")
    def test_latest_price_get_with_annotations(self, mock_prices, mock_currency):
        """Property's getter uses annotated attributes."""
        # get a StockItem object
        a = StockItem()
        # These attributes can't be mocked by patch, because they are not part
        # of the actual class. Provide them here to simulate Django's annotation
        a._latest_price_amount = mock.MagicMock()
        a._latest_price_timestamp = mock.MagicMock()

        # actually access the attribute
        b = a.latest_price

        self.assertFalse(mock_prices.return_value.get_latest_price_object.called)
        self.assertEqual(
            b,
            StockingsMoney(
                a._latest_price_amount, mock_currency, a._latest_price_timestamp
            ),
        )

    @mock.patch("stockings.models.stockitem.StockItem.currency")
    @mock.patch("stockings.models.stockitem.StockItem.prices")
    def test_latest_price_get_without_annotations(self, mock_prices, mock_currency):
        """Property's getter retrieves missing attributes."""
        # set up the mock
        mock_amount = mock.MagicMock()
        mock_timestamp = mock.MagicMock()
        mock_prices.return_value.get_latest_price_object.return_value.price.amount = (
            mock_amount
        )
        mock_prices.return_value.get_latest_price_object.return_value.price.timestamp = (
            mock_timestamp
        )

        # get a StockItem object
        a = StockItem()

        # actually access the attribute
        b = a.latest_price

        self.assertTrue(mock_prices.return_value.get_latest_price_object.called)
        self.assertEqual(b, StockingsMoney(mock_amount, mock_currency, mock_timestamp))

    @mock.patch("stockings.models.stockitem.StockItem.prices")
    def test_latest_price_set(self, mock_prices):
        """Property's setter accesses StockItemPrice."""
        # get a StockItem object
        a = StockItem()

        a.latest_price = StockingsMoney(1.1, "FOO")

        self.assertTrue(mock_prices.return_value.set_latest_price.called)

    def test_latest_price_del(self):
        """Property can not be deleted."""
        # get a StockItem object
        a = StockItem()

        with self.assertRaises(AttributeError):
            del a.latest_price


@tag("integrationtest", "models", "stockitem")
class StockItemORMTest(StockingsORMTestCase):
    """Provide tests with fixture data."""

    @skip("depends on currency conversion")
    def test_currency_set(self):
        """Property's setter updates `StockItemPrice` instances.

        While `StockItemPrice._apply_new_currency()` is already implemented, it
        relies on `StockingsMoney.convert()`, which is not implemented yet and
        will raise `NotImplementedError`. So, while this test method is already
        implemented, it does not produce real results.
        """
        a = StockItem.objects.get(isin="XX0000000003")

        with self.assertRaises(NotImplementedError):
            a.currency = "FOO"

    @skip("to be done")
    def test_latest_price_get_with_annotations(self):
        """Property's getter uses annotated attributes."""
        raise NotImplementedError

    @skip("to be done")
    def test_latest_price_get_without_annotations(self):
        """Property's getter retrieves missing attributes."""
        raise NotImplementedError

    @skip("to be done")
    def test_latest_price_set(self):
        """Property's setter accesses StockItemPrice."""
        raise NotImplementedError
