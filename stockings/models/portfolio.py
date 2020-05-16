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

    # The currency for all money-related fields.
    currency = models.CharField(default=STOCKINGS_DEFAULT_CURRENCY, max_length=3)

    # A human-readable name of the ``Portolio`` object.
    name = models.CharField(max_length=50,)

    # Reference to Django's ``User`` object.
    # In fact, the project may have substituted Django's default user object,
    # so this is as pluggable as possible.
    # Please note, that Django's ``User`` object (or its substitute) will not
    # have a backwards relation to this object.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )

    class Meta:
        app_label = "stockings"
        unique_together = ["name", "user"]
        verbose_name = _("Portfolio")
        verbose_name_plural = _("Portfolios")

    def __str__(self):
        return "{} ({})".format(self.name, self.user)  # pragma: nocover


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
        app_label = "stockings"
        unique_together = ["portfolio", "stock_item"]
        verbose_name = _("Portoflio Item")
        verbose_name_plural = _("Portfolio Items")

    def __str__(self):
        return "{} - {}".format(self.portfolio, self.stock_item)  # pragma: nocover

    def update_cash_in(self, new_cash_flow):
        # calculate new value (old value + new cash flow)
        # Currency conversion is implicitly provided, because
        # `StockingsMoney.add()` ensures a target currency.
        new_value = self.cash_in.add(new_cash_flow)

        # update with new value
        self._cash_in_amount = new_value.amount
        self._cash_in_timestamp = new_value.timestamp

    def update_cash_out(self, new_cash_flow):
        # calculate new value (old value + new cash flow)
        # currency changes are implicitly prohibited, because
        # `StockingsMoney.add()` ensures a target currency.
        new_value = self.cash_out.add(new_cash_flow)

        # update with new value
        self._cash_out_amount = new_value.amount
        self._cash_out_timestamp = new_value.timestamp

    def update_costs(self, new_costs):
        """Update the value of costs, by adding the costs of a trade."""

        # calculate new value (old value + new costs)
        # Currency conversion is implicitly provided, because
        # `StockingsMoney.add()` ensures the target currency.
        new_value = self.costs.add(new_costs)

        self._costs_amount = new_value.amount
        self._costs_timestamp = new_value.timestamp

    def update_stock_value(self, item_price=None, item_count=None):

        if item_price is None:
            item_price = self.stock_item.latest_price

        if item_count is None:
            item_count = self._stock_count

        # calculate new value (item_price * item_count)
        new_value = item_price.multiply(item_count)

        self._stock_value_amount = new_value.amount
        self._stock_value_timestamp = new_value.timestamp
        self._stock_count = item_count

    @classmethod
    def callback_stockitem_update_stock_value(
        cls, sender, instance, created, raw, *args, **kwargs
    ):
        """Update PortfolioItem's `stock_value` with new price information.

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
            item.update_stock_value(item_price=new_price)
            item.save()

    @classmethod
    def callback_trade_apply_trade(
        cls, sender, instance, created, raw, *args, **kwargs
    ):
        """Update several of PortfolioItem's fields to track the trade operation."""

        # Do nothing, if this is a raw save-operation.
        if raw:
            return None

        # Do nothing, if this is an edit of an existing trade.
        if not created:
            return None

        fetch_item = cls.objects.get_or_create(
            portfolio=instance.portfolio,
            stock_item=instance.stock_item,
            # defaults={},
        )
        item = fetch_item[0]
        item_state = fetch_item[1]

        item.update_costs(instance.costs)

        if instance.trade_type == "BUY":
            item.update_cash_in(instance.price.multiply(instance.item_count))
            item.update_stock_value(
                item_price=instance.price,
                item_count=item.stock_count + instance.item_count,
            )

        if instance.trade_type == "SELL":
            if item_state is True:
                raise RuntimeError(
                    "Trying to sell stock, that are not in the portfolio! "
                    "Something went terribly wrong!"
                )

            item.update_cash_out(instance.price.multiply(instance.item_count))
            item.update_stock_value(
                item_price=instance.price,
                item_count=item.stock_count - instance.item_count,
            )

        item.save()

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
        return self.portfolio.currency

    def _get_stock_count(self):
        return self._stock_count

    def _get_stock_value(self):
        return self._return_money(
            self._stock_value_amount, timestamp=self._stock_value_timestamp
        )

    def _return_money(self, amount, currency=None, timestamp=None):
        return StockingsMoney(
            amount,
            currency or self.currency,
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
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "The currency may only be set on `Portfolio` level."
        )

    def _set_currency_old(self, value):
        """Set a new currency for the object and update all money-related fields."""

        # cash_in
        new_value = self.cash_in.convert(value)
        self._cash_in_amount = new_value.amount
        self._cash_in_timestamp = new_value.timestamp

        # cash_out
        new_value = self.cash_out.convert(value)
        self._cash_out_amount = new_value.amount
        self._cash_out_timestamp = new_value.timestamp

        # costs
        new_value = self.costs.convert(value)
        self._costs_amount = new_value.amount
        self._costs_timestamp = new_value.timestamp

        # stock_value
        new_value = self.stock_value.convert(value)
        self._stock_value_amount = new_value.amount
        self._stock_value_timestamp = new_value.timestamp

        # actually update the object's attribute
        self._currency = value

    def _set_stock_count(self, value):
        """Set a new `stock_count` and recalculate the object's `stock_value`."""

        self.update_stock_value(item_count=value)

    def _set_stock_value(self, value):
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "You might want to use 'update_stock_value()'."
        )

    cash_in = property(_get_cash_in, _set_cash_in, doc="TODO: Add docstring here")

    cash_out = property(_get_cash_out, _set_cash_out, doc="TODO: Add docstring here")

    costs = property(_get_costs, _set_costs, doc="TODO: Add docstring here")

    currency = property(_get_currency, _set_currency, doc="TODO: Add docstring here")

    stock_count = property(
        _get_stock_count, _set_stock_count, doc="TODO: Add docstring here"
    )

    stock_value = property(
        _get_stock_value, _set_stock_value, doc="TODO: Add docstring here"
    )
