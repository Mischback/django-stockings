"""Provides the :class:`~stockings.models.portfolioitem.PortfolioItem`."""

# Django imports
from django.apps import apps
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.portfolio import Portfolio
from stockings.models.stock import StockItem


class PortfolioItemManager(models.Manager):
    """Custom manager for :class:`~stockings.models.portfolio.PortfolioItem`.

    This manager is applied as the default manager (see
    :attr:`PortfolioItem.objects <stockings.models.portfolio.PortfolioItem.objects>`).

    Warnings
    --------
    The class documentation only includes code, that is actually shipped by the
    `stockings` app. Inherited attributes/methods (provided by Django's
    :class:`~django.db.models.Manager`) are not documented here.
    """

    def get_queryset(self):
        """Provide the base queryset, annotated with an `is_active` field.

        :class:`~stockings.models.portfolio.PortfolioItem` instances are used to
        track a given :class:`~stockings.models.stock.StockItem` in the context
        of the app. Logically, a `PortfolioItem` can be considered *inactive*,
        if its :attr:`~stockings.models.portfolio.PortfolioItem.stock_count` is
        ``0``, meaning, currently the tracked `StockItem` is currently not in
        the possession of the user.

        The provided `is_active` flag can be used to distinguish between these
        states.

        Returns
        -------
        :class:`~django.db.models.query.QuerySet`
            The annotated base queryset.
        """
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

    # TODO: Should Meta.default_manager_name be set aswell?
    objects = PortfolioItemManager()
    """The default manager for these objects."""

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    """Reference to the :class:`~stockings.models.portfolio.Portfolio`.

    Notes
    -------
    This is implemented as a :class:`~django.db.models.ForeignKey` with
    ``on_delete=CASCADE``, meaning if the referenced
    :class:`~stockings.models.portfolio.Portfolio` object is deleted, all
    referencing `PortfolioItem` objects are discarded aswell.
    """

    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT)
    """Reference to a :class:`~stockings.models.stock.StockItem`.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.ForeignKey` to
    :class:`~stockings.models.stock.StockItem` with ``on_delete=PROTECT``,
    meaning that it is not possible to delete the
    :class:`~stockings.models.stock.StockItem` while it is referenced by a
    `PortfolioItem` object.
    """

    _cash_in_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    """The `amount` part of :attr:`cash_in` (:obj:`decimal.Decimal`).

    Notes
    -----
    This is implemented as :class:`django.db.models.DecimalField`.
    """

    _cash_in_timestamp = models.DateTimeField(default=now)
    """The `timestamp` part of :attr:`cash_in` (:obj:`datetime.datetime`).

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DateTimeField`,
    providing :obj:`django.utils.timezone.now` as its default value.
    """

    _cash_out_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    """The `amount` part of :attr:`cash_out` (:obj:`decimal.Decimal`).

    Notes
    -----
    This is implemented as :class:`django.db.models.DecimalField`.
    """

    _cash_out_timestamp = models.DateTimeField(default=now)
    """The `timestamp` part of :attr:`cash_out` (:obj:`datetime.datetime`).

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DateTimeField`,
    providing :obj:`django.utils.timezone.now` as its default value.
    """

    _costs_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    """The `amount` part of :attr:`costs` (:obj:`decimal.Decimal`).

    Notes
    -----
    This is implemented as :class:`django.db.models.DecimalField`.
    """

    _costs_timestamp = models.DateTimeField(default=now)
    """The `timestamp` part of :attr:`costs` (:obj:`datetime.datetime`).

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DateTimeField`,
    providing :obj:`django.utils.timezone.now` as its default value.
    """

    _stock_value_amount = models.DecimalField(
        decimal_places=4, default=0, max_digits=19
    )
    """The `amount` part of :attr:`stock_value` (:obj:`decimal.Decimal`).

    Notes
    -----
    This is implemented as :class:`django.db.models.DecimalField`.
    """

    _stock_value_timestamp = models.DateTimeField(default=now)
    """The `timestamp` part of :attr:`stock_value` (:obj:`datetime.datetime`).

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DateTimeField`,
    providing :obj:`django.utils.timezone.now` as its default value.
    """

    # Stores the quantity of ``StockItem`` in this ``Portfolio``.
    # This directly influences the ``deposit``, specifically the
    # ``_deposit_amount``. See ``update_deposit()`` for details.
    _stock_count = models.PositiveIntegerField(default=0)
    """The number of shares of the referenced `StockItem` (:obj:`int`).

    Notes
    -----
    This attribute is implemented as
    :class:`~django.db.models.PositiveIntegerField` with ``default=0``.

    Obviously it doesn't make sense to obtain a negative `stock_count`, so this
    only allows positive values.
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        unique_together = ["portfolio", "stock_item"]
        verbose_name = _("Portoflio Item")
        verbose_name_plural = _("Portfolio Items")

    def __str__(self):  # noqa: D105
        return "{} - {}".format(self.portfolio, self.stock_item)  # pragma: nocover

    def apply_trade(self, trade_obj, skip_integrity_check=False):
        """Track a single trade operation and update object's fields."""
        # ensure, that the `trade_obj` is actually associated with this `PortfolioItem`
        if not skip_integrity_check and (
            (self.portfolio != trade_obj.portfolio)
            or (self.stock_item != trade_obj.stock_item)
        ):
            raise StockingsInterfaceError(
                "Could not apply trade, `trade_obj` does not belong to this `PortfolioItem`."
            )  # pragma: nocover

        # track the costs of this trade
        self.update_costs(trade_obj.costs)

        # 'BUY' means a cash flow into the `PortfolioItem` and an increase of the `stock_count`
        if trade_obj.trade_type == "BUY":
            self.update_cash_in(trade_obj.price.multiply(trade_obj.item_count))
            self.update_stock_value(
                item_price=trade_obj.price,
                item_count=self.stock_count + trade_obj.item_count,
            )

        # 'SELL' means a cash flow out of the `PortfolioItem` and a decrease of the `stock_count`
        if trade_obj.trade_type == "SELL":
            self.update_cash_out(trade_obj.price.multiply(trade_obj.item_count))
            self.update_stock_value(
                item_price=trade_obj.price,
                item_count=self.stock_count - trade_obj.item_count,
            )

    def reapply_trades(self):
        """Reset all of the object's money-related fields and then reapplies all trades."""
        # reset all money-related fields by assigning `_amount`= 0
        self._cash_in_amount = 0
        self._cash_out_amount = 0
        self._costs_amount = 0
        self._stock_value_amount = 0

        # reset the `stock_count`
        self._stock_count = 0

        # fetch the associated `Trade` objects
        # The objects have to be ordered by date (`Trade.timestamp`) to ensure,
        # that they are re-applied in the correct order.
        # The `Trade` model can not be imported at the top of this file, because this
        # would lead to a circular import.
        # However, this is the only occurence of `Trade`, so the class is fetched
        # Django's app registry.
        trade_set = (
            apps.get_model("stockings.Trade")
            .objects.filter(portfolio=self.portfolio, stock_item=self.stock_item)
            .order_by("timestamp")
        )

        for trade in trade_set.iterator():
            # The integrity check can actually be skipped, because the `trade_set`
            # applies a filter to ensure correct objects.
            self.apply_trade(trade, skip_integrity_check=True)

    def update_cash_in(self, new_cash_flow):
        """TODO."""
        # calculate new value (old value + new cash flow)
        # Currency conversion is implicitly provided, because
        # `StockingsMoney.add()` ensures a target currency.
        new_value = self.cash_in.add(new_cash_flow)

        # update with new value
        self._cash_in_amount = new_value.amount
        self._cash_in_timestamp = new_value.timestamp

    def update_cash_out(self, new_cash_flow):
        """TODO."""
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
        """TODO."""
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
    def callback_stockitemprice_update_stock_value(
        cls, sender, instance, created, raw, *args, **kwargs
    ):
        """Update PortfolioItem's `stock_value` with new price information.

        This is a signal handler, that is attached as a post_save handler in
        the app's ``StockingsConfig``'s ``ready`` method.
        """
        # Do nothing, if this is a raw save-operation.
        if raw:
            return None

        # Fetch all ``PortfolioItem`` objects, that are linked to the sender's
        # instance stock item.
        portfolio_item_set = cls.objects.filter(stock_item=instance.stock_item)

        # Store the new price outside of the loop.
        new_price = instance.price

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

        item, item_state = cls.objects.get_or_create(
            portfolio=instance.portfolio,
            stock_item=instance.stock_item,
            # defaults={},
        )

        # Another safety to ensure, that no stock can be sold, that is not present
        # in the `Portfolio`.
        if instance.trade_type == "SELL" and item_state is True:
            raise RuntimeError(
                "Trying to sell stock, that are not in the portfolio! "
                "Something went terribly wrong!"
            )

        # actually update the `PortfolioItem`'s fields
        item.apply_trade(instance)
        item.save()

    def _apply_new_currency(self, new_currency):
        """Set a new currency for the object and update all money-related fields."""
        # cash_in
        new_value = self.cash_in.convert(new_currency)
        self._cash_in_amount = new_value.amount
        self._cash_in_timestamp = new_value.timestamp

        # cash_out
        new_value = self.cash_out.convert(new_currency)
        self._cash_out_amount = new_value.amount
        self._cash_out_timestamp = new_value.timestamp

        # costs
        new_value = self.costs.convert(new_currency)
        self._costs_amount = new_value.amount
        self._costs_timestamp = new_value.timestamp

        # stock_value
        new_value = self.stock_value.convert(new_currency)
        self._stock_value_amount = new_value.amount
        self._stock_value_timestamp = new_value.timestamp

    def _get_cash_in(self):
        """`getter` for :attr:`cash_in`.

        Returns
        --------
        :class:`~stockings.data.StockingsMoney`
            The total cash flow into this object.

        See Also
        --------
        :meth:`_return_money`
        """
        return self._return_money(
            self._cash_in_amount, timestamp=self._cash_in_timestamp
        )

    def _get_cash_out(self):
        """`getter` for :attr:`cash_out`.

        Returns
        --------
        :class:`~stockings.data.StockingsMoney`
            The total cash flow out of this object.

        See Also
        --------
        :meth:`_return_money`
        """
        return self._return_money(
            self._cash_out_amount, timestamp=self._cash_out_timestamp
        )

    def _get_costs(self):
        """`getter` for :attr:`costs`.

        Returns
        --------
        :class:`~stockings.data.StockingsMoney`
            The costs associated with this object.

        See Also
        --------
        :meth:`_return_money`
        """
        return self._return_money(self._costs_amount, timestamp=self._costs_timestamp)

    def _get_currency(self):
        """`getter` for :attr:`currency`.

        Returns
        -------
        :obj:`str`
            The :attr:`currency` of the object.

        Notes
        -----
        The `currency` is actually fetched from the associated
        :class:`~stockings.models.portfolio.Portfolio` object.
        """
        return self.portfolio.currency

    def _get_stock_count(self):
        """`getter` for :attr:`stock_count`.

        Returns
        -------
        :obj:`int`
            The count of stocks of this object.
        """
        return self._stock_count

    def _get_stock_value(self):
        """`getter` for :attr:`stock_value`.

        Returns
        --------
        :class:`~stockings.data.StockingsMoney`
            The total value of stocks of this object.

        See Also
        --------
        :meth:`_return_money`
        """
        return self._return_money(
            self._stock_value_amount, timestamp=self._stock_value_timestamp
        )

    def _return_money(self, amount, currency=None, timestamp=None):
        """Return a `StockingsMoney` instance with the given parameters.

        This is a utility method to provide a generic interface for all
        money-related fields of `PortfolioItem`.

        Parameters
        ----------
        amount : :obj:`decimal.Decimal`
        currency : :obj:`str`, optional
        timestamp : :obj:`datetime.datetime`, optional

        Returns
        --------
        :class:`~stockings.data.StockingsMoney`
            Instance's values depends on parameters.

        Notes
        -----
        This method is used to return money-related information using a
        :class:`~stockings.data.StockingsMoney` instance.

        ``amount`` and ``timestamp`` are fetched from the object, depending
        on the accessed attribute.

        If ``currency`` is not provided, the value of :attr:`currency` is used.
        """
        return StockingsMoney(
            amount,
            currency or self.currency,
            # `StockingsMoney` will set the timestamp to `now()`, if no
            # timestamp is provided.
            timestamp,
        )

    def _set_cash_in(self, value):
        """`setter` for :attr:`cash_in`.

        This attribute can not be set directly.

        Parameters
        ----------
        new_currency : :obj:`str`
            This parameter is only provided to match the required prototype for
            this `setter`, it is actually not used.

        Raises
        ------
        :exc:`~stockings.exceptions.StockingsInterfaceError`
            This attribute can not be set directly.

        See Also
        --------
        :meth:`update_cash_in`
        """
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "You might want to use 'update_cash_in()'."
        )

    def _set_cash_out(self, value):
        """`setter` for :attr:`cash_out`.

        This attribute can not be set directly.

        Parameters
        ----------
        new_currency : :obj:`str`
            This parameter is only provided to match the required prototype for
            this `setter`, it is actually not used.

        Raises
        ------
        :exc:`~stockings.exceptions.StockingsInterfaceError`
            This attribute can not be set directly.

        See Also
        --------
        :meth:`update_cash_out`
        """
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "You might want to use 'update_cash_out()'."
        )

    def _set_costs(self, value):
        """`setter` for :attr:`costs`.

        This attribute can not be set directly.

        Parameters
        ----------
        new_currency : :obj:`str`
            This parameter is only provided to match the required prototype for
            this `setter`, it is actually not used.

        Raises
        ------
        :exc:`~stockings.exceptions.StockingsInterfaceError`
            This attribute can not be set directly.

        See Also
        --------
        :meth:`update_costs`
        """
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "You might want to use 'update_costs()'."
        )

    def _set_currency(self, value):
        """`setter` for :attr:`currency`.

        This attribute can not be set directly. The :attr:`currency` is
        actually fetched from the associated
        :class:`stockings.models.portfolio.Portfolio` object.

        Parameters
        ----------
        new_currency : :obj:`str`
            This parameter is only provided to match the required prototype for
            this `setter`, it is actually not used.

        Raises
        ------
        :exc:`~stockings.exceptions.StockingsInterfaceError`
            This attribute can not be set directly.

        See Also
        --------
        :meth:`_apply_new_currency`
        """
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "The currency may only be set on `Portfolio` level."
        )

    def _set_stock_count(self, value):
        """`setter` for :attr:`stock_count`.

        By using this `setter`, the :attr:`stock_count` is set to the new
        `` value`` and the object's :attr:`stock_value` is updated.

        Parameters
        ----------
        value : :obj:`int`
            The new count to be applied.

        See Also
        --------
        :meth:`update_stock_value`
        """
        self.update_stock_value(item_count=value)

    def _set_stock_value(self, value):
        """`setter` for :attr:`stock_value`.

        This attribute can not be set directly.

        Parameters
        ----------
        new_currency : :obj:`str`
            This parameter is only provided to match the required prototype for
            this `setter`, it is actually not used.

        Raises
        ------
        :exc:`~stockings.exceptions.StockingsInterfaceError`
            This attribute can not be set directly.

        See Also
        --------
        :meth:`update_stock_value`
        """
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "You might want to use 'update_stock_value()'."
        )

    cash_in = property(_get_cash_in, _set_cash_in)
    """Cash flow into this `PortfolioItem`
    (:class:`~stockings.data.StockingsMoney`).

    Notes
    -----
    This attribute is implemented as a `property`, you may refer to
    :meth:`_get_cash_in` and :meth:`_set_cash_in`.

    **get**

    Accessing the attribute returns a `StockingsMoney` object.

    - ``amount`` is stored in :attr:`_cash_in_amount` as :obj:`decimal.Decimal`.
    - ``currency`` is fetched from the object's :attr:`currency`.
    - ``timestamp`` is fetched from the object's :attr:`_cash_in_timestamp`.

    **set**

    This property may not be set directly, trying to do so will raise a
    :exc:`~stockings.exceptions.StockingsInterfaceException`.

    To update `cash_in`, use :meth:`update_cash_in`.

    **del**

    This is not implemented, thus an :exc:`AttributeError` will be raised.
    """

    cash_out = property(_get_cash_out, _set_cash_out)
    """Cash flow out of this `PortfolioItem`
    (:class:`~stockings.data.StockingsMoney`).

    Notes
    -----
    This attribute is implemented as a `property`, you may refer to
    :meth:`_get_cash_out` and :meth:`_set_cash_out`.

    **get**

    Accessing the attribute returns a `StockingsMoney` object.

    - ``amount`` is stored in :attr:`_cash_out_amount` as :obj:`decimal.Decimal`.
    - ``currency`` is fetched from the object's :attr:`currency`.
    - ``timestamp`` is fetched from the object's :attr:`_cash_out_timestamp`.

    **set**

    This property may not be set directly, trying to do so will raise a
    :exc:`~stockings.exceptions.StockingsInterfaceException`.

    To update `cash_out`, use :meth:`update_cash_out`.

    **del**

    This is not implemented, thus an :exc:`AttributeError` will be raised.
    """

    costs = property(_get_costs, _set_costs)
    """Costs associated with this `PortfolioItem`
    (:class:`~stockings.data.StockingsMoney`).

    Notes
    -----
    This attribute is implemented as a `property`, you may refer to
    :meth:`_get_costs` and :meth:`_set_costs`.

    **get**

    Accessing the attribute returns a `StockingsMoney` object.

    - ``amount`` is stored in :attr:`_costs_amount` as :obj:`decimal.Decimal`.
    - ``currency`` is fetched from the object's :attr:`currency`.
    - ``timestamp`` is fetched from the object's :attr:`_costs_timestamp`.

    **set**

    This property may not be set directly, trying to do so will raise a
    :exc:`~stockings.exceptions.StockingsInterfaceException`.

    To update `costs`, use :meth:`update_costs`.

    **del**

    This is not implemented, thus an :exc:`AttributeError` will be raised.
    """

    currency = property(_get_currency, _set_currency)
    """The currency for all money-related fields (:obj:`str`, read-only).

    Notes
    -----
    This attribute is implemented as a `property`, and its value is actually
    fetched from the referenced :class:`~stockings.models.portfolio.Portfolio`
    object.

    Setting this attribute is not possible and will raise
    :exc:`~stockings.exceptions.StockingsInterfaceError`. Deleting the attribute
    will raise :exc:`AttributeError`.
    """

    stock_count = property(_get_stock_count, _set_stock_count)
    """The number of shares of the referenced `StockItem` (:obj:`int`).

    Notes
    -----
    This attribute is implemented as a `property`, you may refer to
    :meth:`_get_stock_count` and :meth:`_set_stock_count`.

    **get**

    Accessing the attribute returns :attr:`_stock_count`.

    **set**

    This attribute may be set by providing an :obj:`int`.

    **del**

    This is not implemented, thus an :exc:`AttributeError` will be raised.
    """

    stock_value = property(_get_stock_value, _set_stock_value)
    """The value of stocks of this `PortfolioItem`
    (:class:`~stockings.data.StockingsMoney`).

    This is the total value. The *price per item* of the referenced
    :attr:`stock_item` is multiplied with this object's :attr:`stock_count`.

    Notes
    -----
    This attribute is implemented as a `property`, you may refer to
    :meth:`_get_stock_value` and :meth:`_set_stock_value`.

    **get**

    Accessing the attribute returns a `StockingsMoney` object.

    - ``amount`` is stored in :attr:`_stock_value_amount` as :obj:`decimal.Decimal`.
    - ``currency`` is fetched from the object's :attr:`currency`.
    - ``timestamp`` is fetched from the object's :attr:`_stock_value_timestamp`.

    **set**

    This property may not be set directly, trying to do so will raise a
    :exc:`~stockings.exceptions.StockingsInterfaceException`.

    To update `stock_value`, use :meth:`update_stock_value`.

    **del**

    This is not implemented, thus an :exc:`AttributeError` will be raised.
    """
