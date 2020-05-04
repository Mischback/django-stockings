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
        return '{} ({})'.format(self.name, self.user)  # pragma: nocover


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

    # Stores the details of ``cash_in``, which represents the accumulated
    # prices of stocks, at the time of buying them.
    _cash_in_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _cash_in_timestamp = models.DateTimeField(default=now)

    # Stores the details of ``cash_out``, which represents the accumulated
    # prices of stocks, at the time of selling them.
    _cash_out_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _cash_out_timestamp = models.DateTimeField(default=now)

    # Stores the details of ``costs``, which represents the accumulated costs
    # spent for buying or selling stock items.
    _costs_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _costs_timestamp = models.DateTimeField(default=now)

    # The currency for all money-related fields.
    _currency = models.CharField(default=STOCKINGS_DEFAULT_CURRENCY, max_length=3)

    # Stores the details of the ``stock_value``, which tracks the current value
    # of the associated ``StockItem``s.
    _stock_value_amount = models.DecimalField(
        decimal_places=4, default=0, max_digits=19
    )
    _stock_value_timestamp = models.DateTimeField(default=now)

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
        return '{} - {}'.format(self.portfolio, self.stock_item)  # pragma: nocover

    def _get_cash_in(self):
        return self._return_money(
            self._cash_in_amount, timestamp=self._cash_in_timestamp
        )

    def _get_cash_out(self):
        return self._return_money(
            self._cash_out_amount, timestamp=self._cash_out_timestamp
        )

    def _get_costs(self):
        return self._return_money(self._costs_amount, timestamp=self._costs_timestamp)

    def _get_currency(self):
        return self._currency

    def _get_stock_count(self):
        return self._stock_count

    def _get_stock_value(self):
        return self._return_money(
            self._stock_value_amount, timestamp=self._stock_value_timestamp
        )

    def _return_money(self, amount, currency=None, timestamp=None):
        return StockingsMoney(
            amount,
            currency or self._currency,
            # `StockingsMoney` will set the timestamp to `now()`, if no
            # timestamp is provided.
            timestamp,
        )

    def _set_cash_in(self, value):
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "You might want to use 'update_cash_in()'."
        )

    def _set_cash_out(self, value):
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "You might want to use 'update_cash_out()'."
        )

    def _set_costs(self, value):
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "You might want to use 'update_costs()'."
        )

    def _set_currency(self, value):
        # TODO: Has to be done when all attributes have been adjusted
        raise NotImplementedError('to be done...')

    def _set_stock_count(self, value):
        raise NotImplementedError('to be done...')

    def _set_stock_value(self, value):
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "You might want to use 'update_stock_value()'."
        )

    def __del_attribute(self):
        raise StockingsInterfaceError('This attribute may not be deleted!')

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

    def perform_buy(self, count, price, costs):
        """Perform a buy operation.

        This method is called by ``callback_perform_trade()`` to actually
        modify the object's attributes.

        To handle the purchase of stock items, the actual price of the stock
        is calculated (price per item * count of stock) and added to the
        ``expenses``. The costs of the purchase (whatever the bank charges)
        are tracked by calling ``update_costs()``. Finally, the ``stock_count``
        is adjusted to reflect the newly purchased items (this triggers the
        update of re-calculating the ``deposit`` automatically)."""

        # track the costs
        self.update_costs(costs)

        if self._expenses_currency != price.currency:
            price.amount = price.convert(self._expenses_currency)
            price.currency = self._expenses_currency

        # update expenses
        self._expenses_amount += price.amount * count
        self._expenses_timestamp = price.timestamp

        # update stock_count
        self.stock_count += count

    def perform_sell(self, count, price, costs):
        """Perform a sell operation.

        This method is called by ``callback_perform_trade()`` to actually
        modify the object's attributes.

        To handle the sale of stock items, the actual value of the stock is
        calculated (price per item * count of stock) and added to the
        ``proceeds``. The costs of the sale (whatever the bank charges) are
        tracked by calling ``update_costs()``. Finally, the ``stock_count`` is
        adjusted to reflect the sold items (this triggers the update of
        re-calculating the ``deposit`` automatically)."""

        # track the costs
        self.update_costs(costs)

        if self._proceeds_currency != price.currency:
            price.amount = price.convert(self._proceeds_currency)
            price.currency = self._proceeds_currency

        # update proceeds
        self._proceeds_amount += price.amount * count
        self._proceeds_timestamp = price.timestamp

        # update stock_count
        self.stock_count -= count

    def update_costs(self, costs):
        """Update the value of costs, by adding the costs of a trade."""

        if self._costs_currency != costs.currency:
            costs.amount = costs.convert(self._costs_currency)
            costs.currency = self._costs_currency

        self._costs_amount += costs.amount
        self._costs_timestamp = costs.timestamp

    def update_deposit(self, new_price=None):
        """Update the value of the deposit, by recalculating the value based
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
    def callback_perform_trade(
        cls, sender, instance, created, raw, using, update_fields, *args, **kwargs
    ):
        """Handle trade operations.

        The callback only works on newly created Trade objects. It determines
        the correct PortfolioItem (or creates a new one) and calls the method
        to either handle a buy or sell of stocks.
        See ``perform_buy()`` / ``perform_sell()`` for details.

        This is a singal handler, that is attached as a post_save handler in
        the apps's ``StockingsConfig``'s ``ready`` method."""

        # Do nothing, if this is a raw save-operation.
        if raw:
            return None

        # Do nothing, if this is an edit of an existing trade.
        if not created:
            return None

        # BUYing stock
        if instance.trade_type == 'BUY':
            item = cls.objects.get_or_create(
                portfolio=instance.portfolio,
                stock_item=instance.stock_item,
                # defaults={},
            )[0]
            item.perform_buy(instance.item_count, instance.price, instance.costs)
            item.save()

        # SELLing stock
        if instance.trade_type == 'SELL':
            # This try/catch is *very* defensive! It should not be possible to
            # save a ``Trade`` item of type ``SELL``, that is not backed by a
            # ``PortfolioItem``, see ``clean()`` in ``Trade``.
            try:
                item = cls.objects.get(
                    portfolio=instance.portfolio, stock_item=instance.stock_item
                )
            except cls.DoesNotExist:
                raise RuntimeError(
                    'Trying to sell stock, that are not in the portfolio! Something went terribly wrong!'
                )
            item.perform_sell(instance.item_count, instance.price, instance.costs)
            item.save()

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

    cash_in = property(
        _get_cash_in, _set_cash_in, __del_attribute, 'TODO: Add docstring here'
    )

    cash_out = property(
        _get_cash_out, _set_cash_out, __del_attribute, 'TODO: Add docstring here'
    )

    costs = property(
        _get_costs, _set_costs, __del_attribute, 'TODO: Add docstring here'
    )

    currency = property(
        _get_currency, _set_currency, __del_attribute, 'TODO: Add docstring here'
    )

    stock_count = property(
        _get_stock_count, _set_stock_count, __del_attribute, 'TODO: Add docstring here'
    )

    stock_value = property(
        _get_stock_value, _set_stock_value, __del_attribute, 'TODO: Add docstring here'
    )
