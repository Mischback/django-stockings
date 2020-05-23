"""Provides classes that represent stock items."""

# Django imports
from django.db import models
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.settings import STOCKINGS_DEFAULT_CURRENCY


class StockItem(models.Model):
    """Represents one distinct tradeable item, most likely a stock."""

    # The full name of the item.
    # This should be set to the item's official name.
    # TODO: Can this be determined automatically, if the ISIN is given? See
    # ``get_fullname_by_isin()``.
    full_name = models.CharField(blank=True, max_length=255)

    # The International Securities Identification Number (ISIN) is used as the
    # primary identifier of any StockItem.
    # It is already unique (per its definition) and used as the primary key
    # for database representation.
    # See: https://en.wikipedia.org/wiki/International_Securities_Identification_Number
    # TODO: Is a validator required?
    isin = models.CharField(db_index=True, max_length=12, primary_key=True, unique=True)

    # A short version of the item's ``full_name`` attribute.
    # This is the object's main representation in the front end.
    name = models.CharField(blank=True, max_length=100)

    # The currency for all money-related fields.
    _currency = models.CharField(default=STOCKINGS_DEFAULT_CURRENCY, max_length=3)

    class Meta:
        app_label = "stockings"
        verbose_name = _("Stock Item")
        verbose_name_plural = _("Stock Items")

    def __str__(self):
        if self.name != "":
            return "{} ({})".format(self.name, self.isin,)
        else:
            return "{}".format(self.isin,)

    def get_fullname_by_isin(self):
        """Fetch the ``full_name`` of an item using a data provider."""

        raise NotImplementedError(
            "Needs an implementation of automatic data providers"
        )  # pragma: nocover

    @classmethod
    def get_sentinel_item(cls):  # pragma: nocover
        """Return a sentinel / placeholder object to maintain database integrity.

        Currently, this is not actively used, because all ForeignKey relations
        to StockItem are set to 'PROTECTED'. Anyway, this might be useful, if
        deletion of StockItem should be enabled in future releases."""

        # ``get_or_create`` returns a tuple, consisting of the (fetched or
        # created) object and a boolean flag (indicating, if the object was
        # created *freshly*). Only the first item of that tuple (the object)
        # is returned.
        return cls.object.get_or_create(
            isin="XX0000000000",
            defaults={
                "full_name": "The referenced item got deleted!",
                "name": "Deleted Item",
            },
        )[0]

    def _is_active(self):
        """Return bool to indicate, that this StockItem is active.

        A StockItem is considered active, if it is referenced by at least one
        PortfolioItem, that is active itsself."""

        return self.portfolioitem_set.filter(is_active=True).count() > 0

    def _get_currency(self):
        return self._currency

    def _get_latest_price(self):
        return StockItemPrice.get_latest_price(self)

    def _set_currency(self, new_currency):
        """Set the currency for all associated `StockItemPrice` objects."""

        for item in self.stockitemprice_set.iterator():
            item._apply_new_currency(new_currency)
            item.save()

        self._currency = new_currency

    def _set_latest_price(self, value):
        StockItemPrice.set_latest_price(self, value)

    currency = property(_get_currency, _set_currency, doc="TODO: Add docstring here!")

    is_active = property(_is_active, doc="TODO: Add docstring here!")

    latest_price = property(
        _get_latest_price, _set_latest_price, doc="TODO: Add docstring here!"
    )


class StockItemPriceManager(models.Manager):
    """Custom manager to provide some methods specific to `StockItemPrice`."""

    def get_latest_price_object(self, stock_item):
        """Return the most recent object for a given `stock_item`.

        The most recent object is defined as the one with the most recent `_timestamp`."""

        return (
            self.get_queryset().filter(stock_item=stock_item).latest("_price_timestamp")
        )

    def get_queryset(self):
        """Annotate the queryset with a `date` field."""

        return super().get_queryset().annotate(date=TruncDate("_price_timestamp"))


class StockItemPrice(models.Model):
    """Tracks the price of a given `StockItem`."""

    objects = StockItemPriceManager()

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, unique_for_date="_price_timestamp"
    )

    # The latest price information for the item.
    _price_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _price_timestamp = models.DateTimeField(default=now)

    class Meta:
        app_label = "stockings"
        verbose_name = _("Stock Item Price")
        verbose_name_plural = _("Stock Item Prices")

    def __str__(self):
        return "{} - {} {} ({})".format(
            self.stock_item, self.currency, self._price_amount, self._price_timestamp,
        )  # pragma: nocover

    @classmethod
    def get_latest_price(cls, stock_item):
        """Return `StockingsMoney` instance with the most recent price information."""

        return cls.objects.get_latest_price_object(stock_item=stock_item).price

    @classmethod
    def set_latest_price(cls, stock_item, value):
        """Set latest price information for a given `stock_item`.

        The method evaluates `value.timestamp` to determine if either:
            - an existing `StockItemPrice` object can be updated
            - a new `StockItemPrice` object has to be created
            - no action is required
        """

        # get the latest available object
        latest_obj = cls.objects.get_latest_price_object(stock_item=stock_item)

        # `latest_obj` is more recent than the provided value -> do nothing
        if latest_obj._price_timestamp >= value.timestamp:
            return None

        # provided value is actually on a new day/date
        if latest_obj._price_timestamp.date() < value.timestamp.date():
            latest_obj = cls.objects.create(
                stock_item=stock_item, _price_timestamp=value.timestamp
            )

        latest_obj._set_price(value)
        latest_obj.save()

    def _apply_new_currency(self, new_currency):
        """Set a new currency for the object and convert price information."""

        new_value = self.price.convert(new_currency)
        self._price_amount = new_value.amount
        self._price_timestamp = new_value.timestamp

    def _get_currency(self):
        return self.stock_item.currency

    def _get_price(self):
        return StockingsMoney(self._price_amount, self.currency, self._price_timestamp,)

    def _set_currency(self, value):
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "The currency may only be set on `StockItem` level."
        )

    def _set_price(self, value):

        # only update the price, if the provided value is more recent
        if self._price_timestamp >= value.timestamp:
            return

        if self.currency != value.currency:
            value.amount = value.convert(self.currency)
            # value.currency = self._price_currency

        self._price_amount = value.amount
        # self._price_currency = value.currency
        self._price_timestamp = value.timestamp

    currency = property(_get_currency, _set_currency, doc="TODO: Add docstring here!")

    price = property(_get_price, _set_price, doc="TODO: Add docstring here!")
