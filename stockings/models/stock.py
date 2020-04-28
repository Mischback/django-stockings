"""Provides classes that represent stock items."""

# Django imports
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
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

    # The latest price information for the item.
    _latest_price_amount = models.DecimalField(
        decimal_places=4, default=0, max_digits=19
    )
    _latest_price_currency = models.CharField(
        default=STOCKINGS_DEFAULT_CURRENCY, max_length=3
    )
    _latest_price_timestamp = models.DateTimeField(default=now)

    class Meta:
        app_label = 'stockings'
        verbose_name = _('Stock Item')
        verbose_name_plural = _('Stock Items')

    def __str__(self):
        if self.name != '':
            return '{} ({})'.format(self.name, self.isin,)
        else:
            return '{}'.format(self.isin,)

    def get_fullname_by_isin(self):
        """Fetch the ``full_name`` of an item using a data provider."""

        raise NotImplementedError('Needs an implementation of automatic data providers')

    @classmethod
    def get_sentinel_item(cls):
        """Return a sentinel / placeholder object to maintain database integrity."""

        # ``get_or_create`` returns a tuple, consisting of the (fetched or
        # created) object and a boolean flag (indicating, if the object was
        # created *freshly*). Only the first item of that tuple (the object)
        # is returned.
        return cls.object.get_or_create(
            isin='XX0000000000',
            defaults={
                'full_name': 'The referenced item got deleted!',
                'name': 'Deleted Item',
            },
        )[0]

    @property
    def latest_price(self):
        return StockingsMoney(
            self._latest_price_amount,
            self._latest_price_currency,
            self._latest_price_timestamp,
        )

    @latest_price.setter
    def latest_price(self, new_price):
        """Set the different parts of the object's ``latest_price``.

        As of now, this only works, if the currency doesn't change."""

        if self._latest_price_currency != new_price.currency:
            new_price.amount = new_price.convert(self._latest_price_currency)
            new_price.currency = self._latest_price_currency

        self._latest_price_amount = new_price.amount
        # self._latest_price_currency = new_price.currency
        self._latest_price_timestamp = new_price.timestamp
