"""Provides tests for module `stockings.models.stockitemprice`."""

# Python imports
from datetime import timedelta
from decimal import Decimal
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.data import StockingsMoney
from stockings.models.stockitem import StockItem
from stockings.models.stockitemprice import StockItemPrice

# app imports
from ..util.testcases import StockingsORMTestCase, StockingsTestCase


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
        "stockings.models.stockitemprice.StockItemPrice.stockitem",
        new_callable=mock.PropertyMock,
    )
    def test_currency_get_with_annotations(self, mock_stockitem):
        """Property's getter uses annotated attributes."""
        # get a StockItemPrice
        a = StockItemPrice()
        # This attribute can't be mocked by patch, because it is no part of the
        # actual class. Provide it here to simulate Django's annotation
        a._currency = mock.MagicMock()

        # actually access the attribute
        b = a.currency

        self.assertFalse(mock_stockitem.called)
        self.assertEqual(b, a._currency)

    @mock.patch(
        "stockings.models.stockitemprice.StockItemPrice.stockitem",
        new_callable=mock.PropertyMock,
    )
    def test_currency_get_without_annotations(self, mock_stockitem):
        """Property's getter retrieves missing attributes."""
        # get a StockItemPrice
        a = StockItemPrice()

        # actually access the attribute
        b = a.currency

        self.assertTrue(mock_stockitem.called)
        self.assertEqual(b, mock_stockitem.return_value.currency)

    def test_currency_set(self):
        """Property is read-only."""
        a = StockItemPrice()

        with self.assertRaises(AttributeError):
            a.currency = "foobar"

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

    @mock.patch(
        "stockings.models.stockitemprice.StockItemPrice.currency",
        new_callable=mock.PropertyMock,
    )
    def test_price_get(self, mock_currency):
        """Return the instances attributes as StockingsMoney instance."""
        a = StockItemPrice()

        b = a.price

        self.assertEqual(a._price_amount, b.amount)
        self.assertEqual(mock_currency.return_value, b.currency)
        self.assertEqual(a._price_timestamp, b.timestamp)

    def test_price_set(self):
        """Property is read-only."""
        a = StockItemPrice()

        with self.assertRaises(AttributeError):
            a.price = "foobar"


@tag("integrationtest", "models", "stockitemprice")
class StockItemPriceORMTest(StockingsORMTestCase):
    """Provide tests with fixture data."""

    def test_currency_get_with_annotations(self):
        """Property's getter uses annotated attributes."""
        # get the StockItem
        stockitem = StockItem.objects.get(isin="XX0000000001")

        # with annotation, no additional database query is required (total = 1)
        with self.assertNumQueries(1):
            # get one of the StockItemPrice instances
            stockitemprice_currency = (
                StockItemPrice.stockings_manager.filter(stockitem=stockitem)
                .latest()
                .currency
            )

        self.assertEqual(stockitem.currency, stockitemprice_currency)

    def test_currency_get_without_annotations(self):
        """Property's getter retrieves missing attributes."""
        # get the StockItem
        stockitem = StockItem.objects.get(isin="XX0000000001")

        # with annotation, one additional database query is required (total = 2)
        with self.assertNumQueries(2):
            # get one of the StockItemPrice instances
            stockitemprice_currency = (
                StockItemPrice.objects.filter(stockitem=stockitem).latest().currency
            )

        self.assertEqual(stockitem.currency, stockitemprice_currency)


@tag("integrationtest", "manager", "stockitemprice", "stockitempricemanager")
class StockItemPriceManagerORMTest(StockingsORMTestCase):
    """Provide tests with fixture data."""

    def test_get_latest_price_object(self):
        """Fetches the correct StockItemPrice object."""
        # get a StockItem
        stockitem = StockItem.objects.get(isin="XX0000000001")

        # get a StockItemPrice by the tested method
        test_object = StockItemPrice.stockings_manager.get_latest_price_object(
            stockitem
        )

        # find the StockItemPrice object by Django ORM
        reference = StockItemPrice.objects.filter(stockitem=stockitem).latest()

        # assert equality
        self.assertEqual(test_object, reference)

    def test_set_latest_price_new_date(self):
        """Create a new instance, if new date."""
        # get a StockItem
        stockitem = StockItem.objects.get(isin="XX0000000001")

        # get the most recent StockItemPrice
        latest_price = StockItemPrice.stockings_manager.get_latest_price_object(
            stockitem
        ).price

        # build the new value
        new_price = StockingsMoney(
            latest_price.amount,
            latest_price.currency,
            timestamp=latest_price.timestamp + timedelta(days=1),
        )

        self.assertTrue(
            StockItemPrice.stockings_manager.set_latest_price(stockitem, new_price)
        )

        self.assertNotEqual(latest_price, stockitem.latest_price)
        self.assertEqual(new_price, stockitem.latest_price)

    def test_set_latest_price_existing_date_new_data(self):
        """Update an existing instance, if newer value."""
        # get a StockItem
        stockitem = StockItem.objects.get(isin="XX0000000001")

        # get the most recent StockItemPrice
        latest_price = StockItemPrice.stockings_manager.get_latest_price_object(
            stockitem
        ).price

        # build the new value
        new_price = StockingsMoney(
            latest_price.amount,
            latest_price.currency,
            timestamp=latest_price.timestamp + timedelta(minutes=10),
        )

        self.assertTrue(
            StockItemPrice.stockings_manager.set_latest_price(stockitem, new_price)
        )

        self.assertNotEqual(latest_price, stockitem.latest_price)
        self.assertEqual(new_price, stockitem.latest_price)

    def test_set_latest_price_no_existing_price_objects(self):
        """Create first StockItemPrice instance."""
        # get a StockItem
        stockitem = StockItem.objects.get(isin="XX0000000006")

        # build the new value
        new_price = StockingsMoney(
            Decimal(1.11),
            stockitem.currency,
            # timestamp=datetime.now()
        )

        self.assertTrue(
            StockItemPrice.stockings_manager.set_latest_price(stockitem, new_price)
        )
        self.assertAlmostEqual(new_price.amount, stockitem.latest_price.amount)
        self.assertEqual(new_price.currency, stockitem.latest_price.currency)
        self.assertEqual(new_price.timestamp, stockitem.latest_price.timestamp)

    def test_set_latest_price_old_data(self):
        """Old data does not perform any action."""
        # get a StockItem
        stockitem = StockItem.objects.get(isin="XX0000000001")

        # get the most recent StockItemPrice
        latest_price = StockItemPrice.stockings_manager.get_latest_price_object(
            stockitem
        ).price

        # build the new value
        new_price = StockingsMoney(
            latest_price.amount,
            latest_price.currency,
            timestamp=latest_price.timestamp - timedelta(days=1),
        )

        self.assertFalse(
            StockItemPrice.stockings_manager.set_latest_price(stockitem, new_price)
        )

        self.assertEqual(latest_price, stockitem.latest_price)
        self.assertNotEqual(new_price, stockitem.latest_price)
