"""Provides classes that represent stock items."""

# Django imports
from django.db import models
from django.utils.timezone import now
# Python
from django.utils.translation import ugettext_lazy as _


class StockItem(models.Model):
    """Represents one distinct tradeable item, most likely a stock."""

    # The full name of the item.
    # This should be set to the item's official name.
    # TODO: Can this be determined automatically, if the ISIN is given? See
    # ``get_fullname_by_isin()``.
    full_name = models.CharField(
        blank=True,
        max_length=255,
    )

    # The International Securities Identification Number (ISIN) is used as the
    # primary identifier of any StockItem.
    # It is already unique (per its definition) and used as the primary key
    # for database representation.
    # See: https://en.wikipedia.org/wiki/International_Securities_Identification_Number
    # TODO: Is a validator required?
    isin = models.CharField(
        db_index=True,
        max_length=12,
        primary_key=True,
        unique=True,
    )

    # A short version of the item's ``full_name`` attribute.
    # This is the object's main representation in the front end.
    name = models.CharField(
        blank=True,
        max_length=100,
    )

    # The latest price information for the item.
    _latest_price_value = models.DecimalField(
        blank=True,
        decimal_places=4,
        max_digits=19,
    )

    # The currency of the latest price.
    _latest_price_currency = models.CharField(
        blank=True,
        max_length=3,
    )

    # The timestamp of the latest price.
    _latest_price_timestamp = models.DateTimeField(
        null=True,
    )

    class Meta:
        app_label = 'stockings'
        verbose_name = _('Stock Item')
        verbose_name_plural = _('Stock Items')

    def __str__(self):
        if self.name != '':
            return '{} ({})'.format(
                self.name,
                self.isin,
            )
        else:
            return '{}'.format(
                self.isin,
            )

    def get_fullname_by_isin(self):
        """Fetch the ``full_name`` of an item using a data provider."""

        raise NotImplementedError(
            'Needs an implementation of automatic data providers'
        )

    def get_latest_price(self):
        """Return the latest price information of this item."""
        raise NotImplementedError('Not yet implemented!')

    def set_latest_price(self, value, currency, timestamp=None):
        """Update the latest price information of this item."""
        raise NotImplementedError('Not yet implemented!')
