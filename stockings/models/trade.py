# Django imports
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.models.portfolio import Portfolio
from stockings.models.stock import StockItem
from stockings.settings import STOCKINGS_DEFAULT_CURRENCY


class Trade(models.Model):

    # Define the choices for `type` field.
    # TODO: Django 3.0 introduces another way for this!
    # See: https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
    # Don't use this, if it is the only 3.0 feature to keep backwards compatibility,
    # but DO use this, if there are other 3.0 features, that *must* be used!
    TRADE_TYPES = [
        ('BUY', _('Buy')),
        ('SELL', _('Sell')),
    ]

    # Reference to the Portfolio.
    # If the Portfolio object is deleted, all associated Trade objects are discarded!
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)

    # Reference to the traded StockItem.
    stock_item = models.ForeignKey(
        StockItem, on_delete=models.SET(StockItem.get_sentinel_item), related_name='+'
    )

    # Number of traded items.
    # This number is always positive. The semantic difference of *buy* and *sell*
    # trades is handled in the respective classes' methods.
    # TODO: Add a custom validator! MAY NOT BE ZERO!
    item_count = models.PositiveIntegerField(default=0)

    # Date and time of the trade.
    timestamp = models.DateTimeField(default=now)

    # The type of the trade, e.g. `Buy` and `Sell`
    trade_type = models.CharField(choices=TRADE_TYPES, max_length=4)

    # Costs for this trade, e.g. whatever the bank charges
    _costs_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _costs_currency = models.CharField(default=STOCKINGS_DEFAULT_CURRENCY, max_length=3)

    # Price **per item** for this trade.
    _price_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _price_currency = models.CharField(default=STOCKINGS_DEFAULT_CURRENCY, max_length=3)

    class Meta:
        app_label = 'stockings'
        verbose_name = _('Trade')
        verbose_name_plural = _('Trades')

    def __str__(self):
        return '[{}] {} - {} ({})'.format(
            self.trade_type, self.portfolio, self.stock_item, self.timestamp
        )

    def clean(self):
        # TODO: Things to implement here:
        #     - ensure, that a `Sell` Trade can not be done for a `stock_item`,
        #       that is not represented by a `PortfolioItem` in `portfolio`
        #     - ensure, that a `Sell` Trade can not have `item_count` > The
        #       `PortfolioItem`'s `count`
        raise NotImplementedError('Provide model specific cleaning here!')

    @property
    def costs(self):
        return StockingsMoney(self._costs_amount, self._costs_currency, self.timestamp)

    @property
    def price(self):
        return StockingsMoney(self._price_amount, self._price_currency, self.timestamp)
