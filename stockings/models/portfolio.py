"""These classes represent a portfolio and its items."""

# Django imports
from django.conf import settings
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.stock import StockItem
from stockings.settings import STOCKINGS_DEFAULT_CURRENCY


class Portfolio(models.Model):
    """Represents a portolio of stocks."""

    # A human-readable name of the ``Portolio`` object.
    name = models.CharField(max_length=50,)

    # Reference to Django's ``User`` object.
    # In fact, the project may have substituted Django's default user object,
    # so this is as pluggable as possible.
    # Please note, that Django's ``User`` object (or its substitute) will not
    # have a backwards relation to this object.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+'
    )

    class Meta:
        app_label = 'stockings'
        unique_together = ['name', 'user']
        verbose_name = _('Portfolio')
        verbose_name_plural = _('Portfolios')

    def __str__(self):
        return '{} ({})'.format(self.name, self.user)


class PortfolioItemManager(models.Manager):
    """Custom manager to provide custom properties for Django querysets."""

    def get_queryset(self):
        """Return a modified queryset.

        The original queryset is annotated with additional fields to provide
        ``PortfolioItem``'s properties in Django querysets."""
        return (
            super()
            .get_queryset()
            .annotate(
                is_active=models.Case(
                    models.When(_stock_count=0, then=models.Value(False)),
                    default=models.Value(True),
                    output_field=models.BooleanField(),
                )
            )
        )


class PortfolioItem(models.Model):
    """Tracks one single ``StockItem`` in a user's ``Portfolio``."""

    # Use the custom manager as default
    # TODO: Should Meta.default_manager_name be set aswell?
    objects = PortfolioItemManager()

    # Reference to the ``Portfolio``.
    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)

    # Reference to the ``StockItem``.
    # The deletion of ``StockItem``s must be prevented, if a ``PortfolioItem``
    # is still referencing them. That's the reason for ``on_delete=models.PROTECT``.
    # The referenced ``StockItem`` does not have to know, which portoflios
    # referenced it, so ``related_name='+'`` disables the backwards relation.
    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT)

    # Stores the details of ``costs``, which represents the accumulated costs
    # spent for buying or selling stock items.
    _costs_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _costs_currency = models.CharField(default=STOCKINGS_DEFAULT_CURRENCY, max_length=3)
    _costs_timestamp = models.DateTimeField(default=now)

    # Stores the details of the ``deposit``, which tracks the current value of
    # the associated ``StockItem``s.
    _deposit_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _deposit_currency = models.CharField(
        default=STOCKINGS_DEFAULT_CURRENCY, max_length=3
    )
    _deposit_timestamp = models.DateTimeField(default=now)

    # Stores the details of ``expenses``, which represents the accumulated
    # prices of stocks, at the time of buying them.
    _expenses_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _expenses_currency = models.CharField(
        default=STOCKINGS_DEFAULT_CURRENCY, max_length=3
    )
    _expenses_timestamp = models.DateTimeField(default=now)

    # Stores the details of ``proceeds``, which represents the accumulated
    # prices of stocks, at the time of selling them.
    _proceeds_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _proceeds_currency = models.CharField(
        default=STOCKINGS_DEFAULT_CURRENCY, max_length=3
    )
    _proceeds_timestamp = models.DateTimeField(default=now)

    # Stores the quantity of ``StockItem`` in this ``Portfolio``.
    # This directly influences the ``deposit``, specifically the
    # ``_deposit_amount``. See ``update_deposit()`` for details.
    _stock_count = models.PositiveIntegerField(default=0)

    class Meta:
        app_label = 'stockings'
        unique_together = ['portfolio', 'stock_item']
        verbose_name = _('Portoflio Item')
        verbose_name_plural = _('Portfolio Items')

    def __str__(self):
        return '{} - {}'.format(self.portfolio, self.stock_item)

    @property
    def costs(self):
        return StockingsMoney(
            self._costs_amount, self._costs_currency, self._costs_timestamp
        )

    @costs.setter
    def costs(self, value):
        """The value of costs may not be set directly."""
        raise StockingsInterfaceError('This attribute may not be set directly.')

    @property
    def deposit(self):
        return StockingsMoney(
            self._deposit_amount, self._deposit_currency, self._deposit_timestamp
        )

    @deposit.setter
    def deposit(self, value):
        """The value of deposit may not be set directly."""
        raise StockingsInterfaceError('This attribute may not be set directly.')

    @property
    def expenses(self):
        return StockingsMoney(
            self._expenses_amount, self._expenses_currency, self._expenses_timestamp
        )

    @expenses.setter
    def expenses(self, value):
        """The value of expenses may not be set directly."""
        raise StockingsInterfaceError('This attribute may not be set directly.')

    @property
    def is_active(self):
        """Return bool to indicate status of the object.

        A PortfolioItem is considered 'active', if the stock count is > 0."""
        return self._stock_count > 0

    @is_active.setter
    def is_active(self, value):
        """Required dummy function.

        The property ``is_active`` is based on a logical operation. Properties
        are not accessible in Django querysets by default.
        The custom ``PortfolioItemManager`` makes the property accessible in
        querysets, by emulating its logical implementation. But if the
        ``PortfolioItemManager`` is used as the default manager, retrieving
        objects from the database requires a setter for the property."""
        pass

    def perform_buy(self, trade_stock_count, trade_price, trade_costs):
        raise NotImplementedError('to be done')

    def perform_sell(self, trade_stock_count, trade_price, trade_costs):
        raise NotImplementedError('to be done')

    @property
    def proceeds(self):
        return StockingsMoney(
            self._proceeds_amount, self._proceeds_currency, self._proceeds_timestamp
        )

    @proceeds.setter
    def proceeds(self, value):
        """The value of expenses may not be set directly."""
        raise StockingsInterfaceError('This attribute may not be set directly.')

    @property
    def stock_count(self):
        return self._stock_count

    @stock_count.setter
    def stock_count(self, value):
        self._stock_count = value
        self.update_deposit()

    def update_deposit(self, new_price=None):
        """Updates the value of the deposit, by recalculating the value based
        on a new price information.

        If no new price is given, the method will fetch the latest price
        information from the associated ``stock_item``.

        ``_deposit_value`` = ``new_price.amount`` * ``stock_item``
        """

        if new_price is None:
            new_price = self.stock_item.latest_price

        if self._deposit_currency != new_price.currency:
            new_price.amount = new_price.convert(self._deposit_currency)
            new_price.currency = self._deposit_currency

        self._deposit_amount = new_price.amount * self.stock_count
        # self._deposit_currency = new_price.currency
        self._deposit_timestamp = new_price.timestamp

    @classmethod
    def callback_price_update(
        cls, sender, instance, created, raw, using, update_fields, *args, **kwargs
    ):
        """Update the objects ``deposit`` value, based on latest price
        information.

        This is a signal handler, that is attached as a post_save handler in
        the app's ``StockingsConfig``'s ``ready`` method."""

        # Do nothing, if this is a raw save-operation.
        if raw:
            return None

        # Fetch all ``PortfolioItem`` objects, that are linked to the sender's
        # instance stock item.
        portfolio_item_set = cls.objects.filter(stock_item=instance)

        # Store the new price outside of the loop.
        new_price = instance.latest_price

        # Update all relevant ``PortfolioItem`` objects.
        for item in portfolio_item_set.iterator():
            item.update_deposit(new_price)
            item.save()
