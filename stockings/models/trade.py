# Django imports
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.models.portfolio import Portfolio, PortfolioItem
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
        StockItem, on_delete=models.PROTECT, related_name='+'
    )

    # Number of traded items.
    # This number is always positive. The semantic difference of *buy* and *sell*
    # trades is handled in the respective classes' methods.
    item_count = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(1)]
    )

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
        """Provide some validation, before actually 'performing' the trade.

        These validations are not strictly tied to one specific field. In
        particular, they require data from other models."""

        # There are some restrictions for 'SELL' trades:
        # 1. The ``stock_item`` must have a corresponding ``PortfolioItem``
        #   object in ``portfolio``.
        # 2. You are not able to sell more items than available in your
        #   portfolio.
        if self.trade_type == 'SELL':
            # Get the ``PortfolioItem``...
            try:
                portfolio_item = self.portfolio.portfolioitem_set.get(
                    stock_item=self.stock_item
                )
            except PortfolioItem.DoesNotExist:
                raise ValidationError(
                    _(
                        'You are trying to sell stock, that is not present in your portfolio!'
                    ),
                    code='invalid',
                )

            # Trying to sell more items than available. Setting a maximum value
            # for this trade.
            # TODO: Add a notification of some sort... django messages?
            if self.item_count > portfolio_item.stock_count:
                self.item_count = portfolio_item.stock_count

    @property
    def costs(self):
        return StockingsMoney(self._costs_amount, self._costs_currency, self.timestamp)

    @property
    def price(self):
        return StockingsMoney(self._price_amount, self._price_currency, self.timestamp)
