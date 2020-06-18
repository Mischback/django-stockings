"""Provides the :class:`~stockings.models.portfolioitem.PortfolioItem`."""

# Python imports
import logging

# Django imports
from django.db import models
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.portfolio import Portfolio
from stockings.models.stock import StockItem
from stockings.models.trade import Trade

# get a module-level logger
logger = logging.getLogger(__name__)


class PortfolioItemQuerySet(models.QuerySet):
    """App-specific implementation of :class:`django.db.modesl.QuerySet`.

    Notes
    -----
    This :class:`~django.db.models.QuerySet` implementation provides
    app-specific augmentations.

    The provided methods augment/extend the retrieved
    :class:`stockings.models.portfolioitem.PortfolioItem` instances by
    annotating them with additional information.
    """

    def default(self):
        """Return a queryset with all app-specific annotations.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The fully annotated queryset.
        """
        return self._annotate_trade_information()

    def _annotate_trade_information(self):
        """Annotate the instances with their cash flows.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The annotated queryset.
        """
        trade_objects = (
            Trade
            # 1) Use the app-/model-specific manager.
            # 2) Filter by `portfolio` and `stock_item`:
            #    There is no direct reference between `Trade` and
            #    `PortfolioItem` instances.
            .stockings_manager.filter(
                portfolio=models.OuterRef("portfolio"),
                stock_item=models.OuterRef("stock_item"),
            )
            # Removes any pre-defined `ORDER BY`-clause.
            .order_by()
            # Groups by `stock_item`.
            .values("stock_item")
            # Let the magic happen and determine cash flows into and out of the
            # `PortfolioItem`.
            # Because the `PortfolioItem` is directly linked with `StockItem`,
            # these cash flows can then be used to annotate the `PortfolioItem`
            # instances.
            .annotate(
                cash_in_amount=Coalesce(
                    models.Sum(
                        "_trade_volume_amount", filter=models.Q(trade_type="BUY")
                    ),
                    models.Value(0),
                ),
                cash_in_timestamp=models.Max(
                    "timestamp", filter=models.Q(trade_type="BUY")
                ),
                cash_out_amount=Coalesce(
                    models.Sum(
                        "_trade_volume_amount", filter=models.Q(trade_type="SELL")
                    ),
                    models.Value(0),
                ),
                cash_out_timestamp=models.Max(
                    "timestamp", filter=models.Q(trade_type="SELL")
                ),
                costs_amount=Coalesce(models.Sum("_costs_amount"), models.Value(0)),
                costs_timestamp=models.Max("timestamp"),
                stock_buy_count=Coalesce(
                    models.Sum("item_count", filter=models.Q(trade_type="BUY")),
                    models.Value(0),
                ),
                stock_sell_count=Coalesce(
                    models.Sum("item_count", filter=models.Q(trade_type="SELL")),
                    models.Value(0),
                ),
            )
        )

        # The annotations are extendable, so that other cash flows (e.g.
        # dividends) may be included.
        return self.annotate(
            _cash_in_amount=models.ExpressionWrapper(
                0 + models.Subquery(trade_objects.values("cash_in_amount")),
                output_field=models.DecimalField(),
            ),
            _cash_in_timestamp=models.ExpressionWrapper(
                models.Subquery(trade_objects.values("cash_in_timestamp")),
                output_field=models.DateTimeField(),
            ),
            _cash_out_amount=models.ExpressionWrapper(
                0 + models.Subquery(trade_objects.values("cash_out_amount")),
                output_field=models.DecimalField(),
            ),
            _cash_out_timestamp=models.ExpressionWrapper(
                models.Subquery(trade_objects.values("cash_out_timestamp")),
                output_field=models.DateTimeField(),
            ),
            _costs_amount=models.ExpressionWrapper(
                0 + models.Subquery(trade_objects.values("costs_amount")),
                output_field=models.DecimalField(),
            ),
            _costs_timestamp=models.ExpressionWrapper(
                models.Subquery(trade_objects.values("costs_timestamp")),
                output_field=models.DateTimeField(),
            ),
            _stock_count=models.ExpressionWrapper(
                models.Subquery(trade_objects.values("stock_buy_count"))
                - models.Subquery(trade_objects.values("stock_sell_count")),
                output_field=models.PositiveIntegerField(),
            ),
        )


class PortfolioItemManager(models.Manager):
    """App-/model-specific implementation of :class:`django.db.models.Manager`.

    Notes
    -----
    This :class:`~django.db.models.Manager` implementation is used as an
    additional manager of :class:`~stockings.models.portfolio.PortfolioItem` (see
    :attr:`stockings.models.portfolio.PortfolioItem.stockings_manager`.

    This implementation inherits its functionality from
    :class:`django.db.models.Manager` and provides identical funtionality.
    Furthermore, it augments the retrieved objects with additional attributes,
    using the custom :class:`~django.db.models.QuerySet` implementation
    :class:`~stockings.models.portfolio.PortfolioItemQuerySet`.
    """

    def get_queryset(self):
        """Use the app-/model-specific :class:`~stockings.models.portfolio.PortfolioItemQuerySet` by default.

        Returns
        -------
        :class:`django.models.db.QuerySet`
            This queryset is provided by
            :class:`stockings.models.portfolio.PortfolioItemQuerySet` and
            applies its
            :meth:`~stockings.models.portfolio.PortfolioItemQuerySet.full`
            method. The retrieved objects will be annotated with additional
            attributes.
        """
        return PortfolioItemQuerySet(self.model, using=self._db).default()


class PortfolioItem(models.Model):
    """Tracks one single ``StockItem`` in a user's ``Portfolio``."""

    objects = models.Manager()
    """The model's default manager.

    The default manager is set to :class:`django.db.models.Manager`, which is
    the default value. In order to add the custom :attr:`stockings_manager` as
    an *additional* manager, the default manager has to be provided explicitly
    (see :djangodoc:`topics/db/managers/#default-managers`).
    """

    stockings_manager = PortfolioItemManager()
    """App-/model-specific manager, that provides additional functionality.

    This manager is set to
    :class:`stockings.models.portfolio.PortfolioItemManager`. Its implementation
    provides augmentations of `PortfolioItem` objects, by annotating them on
    database level.

    The manager has to be used explicitly, see **Examples** section below.

    For a list of (virtual) attributes, that are solely provided as annotations,
    refer to :class:`stockings.models.portfolio.PortfolioItemQuerySet`.

    Warnings
    --------
    The attributes :attr:`cash_in`, :attr:`cash_out` and :attr:`costs` are only
    available, when the `PortfolioItem` instance is retrieved using
    :attr:`stockings_manager` (see **Examples** section below).

    Examples
    --------
    >>> pi = PortfolioItem.object.first()
    >>> pi.cash_in
    AttributeError
    >>> pi = PortfolioItem.stockings_manager.first()
    >>> pi.cash_in
    StockingsMoney instance
    """

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

    class Meta:  # noqa: D106
        app_label = "stockings"
        unique_together = ["portfolio", "stock_item"]
        verbose_name = _("Portoflio Item")
        verbose_name_plural = _("Portfolio Items")

    def __str__(self):  # noqa: D105
        return "{} - {}".format(self.portfolio, self.stock_item)  # pragma: nocover

    @cached_property
    def cash_in(self):  # noqa: D401
        """The cash flow into this `PortfolioItem` (:class:~stockings.data.StockingsMoney`, read-only).

        Warnings
        --------
        It is highly recommended to use
        :class:`~stockings.models.portfolioitem.PortfolioItemManager` to
        retrieve `PortfolioItem` objects from the database, because this will
        use a (rather complex) SQL statement which includes the required
        annotations to actually populate this property. However, only one
        database query is performed. When using
        :class:`~django.db.models.Manager`, accessing this attribute will result
        in another database access (and probably more than one, if the
        attributes :attr:`cash_out`, :attr:`costs`, :attr:`stock_count` or
        :attr:`stock_value` are accessed aswell).

        Notes
        -----
        `cash_in` is implemented as
        :class:`django.utils.functional.cached_property`.

        The required values to populate the
        :class:`~stockings.data.StockingsMoney` instance are not directly stored
        as attributes of this `PortfolioItem` object. Instead, they are
        dynamically calculated by evaluating other models, most notably
        :class:`stockings.models.trade.Trade`.

        This might be done while fetching the `PortfolioItem` object using
        :class:`the model-specific manager <stockings.models.portfolioitem.PortfolioItemManager>`
        as provided by :attr:`stockings_manager`; the required values are then
        provided as annotations to the `PortfolioItem` instance.

        If the `PortfolioItem` object was fetched using
        :class:`Django's default manager <django.db.models.Manager>`, as
        provided by :attr:`objects`, these annotations are missing, so the
        `getter` implementation performs additional database queries to retrieve
        these values (the implementation as
        :class:`~django.utils.functional.cached_property` ensures, that this
        *expensive* operation is only performed once during the lifetime of this
        instance).
        """
        try:
            return StockingsMoney(
                self._cash_in_amount, self.currency, self._cash_in_timestamp
            )
        except AttributeError:
            logger.info(
                "Missing values while accessing attribute 'cash_in'. "
                "Performing required database queries!"
            )
            logger.debug(
                "'cash_in' is accessed while required values are not available. Most "
                "likely, the 'PortfolioItem' was not fetched using "
                "'PortfolioItem.stockings_manager', so that the specific annotations "
                "are missing."
            )

            # collect the required information
            trade_information = Trade.stockings_manager.aggregation_by_portfolioitem(
                portfolio=self.portfolio, stock_item=self.stock_item
            ).first()

            return StockingsMoney(
                trade_information["purchase_amount"],
                self.currency,
                trade_information["purchase_latest_timestamp"],
            )

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

    def _apply_new_currency(self, new_currency):
        """Set a new currency for the object and update all money-related fields."""
        # stock_value
        new_value = self.stock_value.convert(new_currency)
        self._stock_value_amount = new_value.amount
        self._stock_value_timestamp = new_value.timestamp

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
