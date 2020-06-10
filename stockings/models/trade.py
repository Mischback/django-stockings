"""Provides the :class:`~stockings.models.trade.Trade` and its related classes.

This includes the Django model :class:`~stockings.models.trade.Trade`, the
app-/model-specific `Manager` :class:`~stockings.models.trade.TradeManager` and
the `QuerySet` :class:`~stockings.models.trade.TradeQuerySet`.

Instances of :class:`~stockings.models.trade.Trade` are the main mean to
model cash flows into the :class:`~stockings.models.portfolio.Portfolio` (by
buying stock) or out of the `Portfolio` (by selling stock).
"""

# Django imports
from django.apps import apps
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.portfolio import Portfolio
from stockings.models.stock import StockItem


class TradeQuerySet(models.QuerySet):
    """App-specific implementation of :class:`django.db.modesl.QuerySet`.

    Notes
    -----
    This :class:`~django.db.models.QuerySet` implementation provides
    app-specific augmentations.

    The provided methods augment/extend the retrieved
    :class:`stockings.models.trade.Trade` instances by annotating them with
    additional information.
    """

    def full(self):
        """Return a queryset with all app-specific annotations.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The fully annotated queryset.
        """
        return self._annotate_trade_volume()

    def _annotate_trade_volume(self):
        """Annotate each object with `_trade_volume_amount`.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The annotated queryset.

        Notes
        -----
        The attribute :attr:`~stockings.models.trade.Trade.trade_volume` of
        :class:`stockings.models.trade.Trade` is not actually stored as a
        Django model field. Instead, it is only provided by this annotation.
        """
        return self.annotate(
            _trade_volume_amount=models.ExpressionWrapper(
                models.F("item_count") * models.F("_price_amount"),
                output_field=models.DecimalField(),
            )
        )


class TradeManager(models.Manager):
    """App-/model-specific implementation of :class:`django.db.models.Manager`.

    Notes
    -----
    This :class:`~django.db.models.Manager` implementation is used as an
    additional manager of :class:`~stockings.models.trade.Trade` (see
    :attr:`stockings.models.trade.Trade.stockings_manager`.

    This implementation inherits its functionality from
    :class:`django.db.models.Manager` and provides identical funtionality.
    Furthermore, it augments the retrieved objects with additional attributes,
    using the custom :class:`~django.db.models.QuerySet` implementation
    :class:`~stockings.models.trade.TradeQuerySet`.
    """

    def get_queryset(self):
        """Use the app-/model-specific :class:`~stockings.models.trade.TradeQuerySet` by default.

        Returns
        -------
        :class:`django.models.db.QuerySet`
            This queryset is provided by
            :class:`stockings.models.trade.TradeQuerySet` and applies its
            :meth:`~stockings.models.trade.TradeQuerySet.full` method. The
            retrieved objects will be annotated with additional attributes.
        """
        return TradeQuerySet(self.model, using=self._db).full()


class Trade(models.Model):
    """Represents a single trade operation, i.e. the purchase or sale of stock.

    Objects of this class are the central mean to modify the portfolio of a
    user. By performing a purchase (object with ``trade_type="BUY"``), the
    given stock (specified by :attr:`stock_item`) is added to the portfolio, by
    updating or creating a :class:`~stockings.models.portfolio.PortfolioItem`
    with the provided :attr:`item_count`.

    Selling stock (object with ``trade_type="SELL"``) decreases the count of
    stock in :class:`~stockings.models.portfolio.PortfolioItem`, ultimately to
    zero.

    While performing trade operations, the
    :class:`~stockings.models.portfolio.PortfolioItem` is updated to track the
    cash flows and stock counts.

    See Also
    ---------
    stockings.models.portfolio.PortfolioItem.callback_trade_apply_trade :
        callback to update :class:`~stockings.models.portfolio.PortfolioItem`
        objects.
    stockings.models.portfolio.Portfolio :
        :class:`~stockings.models.portfolio.Portfolio` object, that in fact
        provides the :attr:`~stockings.models.trade.Trade.currency` attribute.
    stockings.models.stock.StockItem :
        The associated object, that represents a stock.

    Warnings
    ----------
    The class documentation only includes code, that is actually shipped by the
    `stockings` app. Inherited attributes/methods (provided by Django's
    :class:`~django.db.models.Model`) are not documented here.
    """

    objects = models.Manager()
    """The model's default manager.

    The default manager is set to :class:`django.db.models.Manager`, which is
    the default value. In order to add the custom :attr:`stockings_manager` as
    an *additional* manager, the default manager has to be provided explicitly
    (see :djangodoc:`topics/db/managers/#default-managers`).
    """

    stockings_manager = TradeManager()
    """App-/model-specific manager, that provides additional functionality.

    This manager is set to :class:`stockings.models.trade.TradeManager`. Its
    implementation provides augmentations of `Trade` objects, by annotating them
    on database level.

    The manager has to be used explicitly, see **Examples** section below.

    For a list of (virtual) attributes, that are solely provided as annotations,
    refer to :class:`stockings.models.trade.TradeQuerySet`.

    Warnings
    --------
    The :attr:`trade_volume` attribute is only available, when the `Trade`
    instance is retrieved using :attr:`stockings_manager` (see **Examples**
    section below).

    Examples
    --------
    >>> t = Trade.object.first()
    >>> t.trade_volume
    StockingsInterfaceError
    >>> t = Trade.stockings_manager.first()
    >>> t.trade_volume
    StockingsMoney instance

    Using stockings_manager in a reverse relation

    >>> from stockings.models.portfolio import Portfolio
    >>> p = Portfolio.objects.first()
    >>> p.trade_set(manager="stockings_manager").all()
    QuerySet including all Trade objects with portfolio=p
    """

    # Define the choices for `type` field.
    # TODO: Django 3.0 introduces another way for this!
    # See: https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
    # Don't use this, if it is the only 3.0 feature to keep backwards compatibility,
    # but DO use this, if there are other 3.0 features, that *must* be used!
    TRADE_TYPES = [
        ("BUY", _("Buy")),
        ("SELL", _("Sell")),
    ]

    item_count = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(1)]
    )
    """The count of traded stock (:obj:`int`).

    The count has to be positive, because purchase/sell are distinguished by
    the value of :attr:`trade_type`.

    Notes
    -----
    This attribute is implemented as
    :class:`~django.db.models.PositiveIntegerField` with an
    :class:`MinValueValidator(1) <django.core.validators.MinValueValidator>`
    attached.

    The value has to be ``>= 1``. Semantically, it doesn't make sense to have a
    `Trade` object with ``item_count = 0``.
    """

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    """Reference to a :class:`~stockings.models.portfolio.Portfolio`.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.ForeignKey` to
    :class:`~stockings.models.portfolio.Portfolio` with ``on_delete=CASCADE``,
    meaning that, if the :class:`~stockings.models.portfolio.Portfolio` object
    is deleted, all referencing `Trade` objects will be discarded aswell.
    """

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="+"
    )
    """Reference to a :class:`~stockings.models.stock.StockItem`.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.ForeignKey` to
    :class:`~stockings.models.stock.StockItem` with ``on_delete=PROTECT``,
    meaning that it is not possible to delete the
    :class:`~stockings.models.stock.StockItem` while it is referenced by a
    `Trade` object.

    The backwards relation (see
    :attr:`ForeignKey.related_name<django.db.models.ForeignKey.related_name>`)
    is disabled.
    """

    timestamp = models.DateTimeField(default=now)
    """The point of time of the trade operation (:obj:`datetime.datetime`).

    There is only one `timestamp` per object and this is used for :attr:`costs`
    aswell as :attr:`price`.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DateTimeField`,
    providing :obj:`django.utils.timezone.now` as its default value.
    """

    trade_type = models.CharField(choices=TRADE_TYPES, max_length=4)
    """Determines if this is a purchase or a sale (:obj:`str`).

    Values are limited to ``"BUY"`` and ``"SELL"``, as provided by the class's
    :attr:`TRADE_TYPES`.

    Notes
    -----
    This attribute is implemented as :class:`django.db.models.CharField`,
    limiting the accepted values to ``choices=TRADE_TYPE``.
    """

    _costs_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    """The `amount` part of :attr:`costs`.

    Notes
    -----
    This is implemented as :class:`django.db.models.DecimalField`.
    """

    _price_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    """The `amount` part of :attr:`price`.

    Notes
    -----
    This is implemented as :class:`django.db.models.DecimalField`.
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        verbose_name = _("Trade")
        verbose_name_plural = _("Trades")

    def __str__(self):  # noqa: D105
        return "[{}] {} - {} ({})".format(
            self.trade_type, self.portfolio, self.stock_item, self.timestamp
        )  # pragma: nocover

    def clean(self):
        """Provide some validation, before actually *performing* the trade.

        These validations are not strictly tied to one specific field. In
        particular, they require data from other models.

        Raises
        ------
        django.core.exceptions.ValidationError
            Raised if a sale should be performed, while the stock to be traded
            is currently not in the portfolio.

        Notes
        -----
        This a rather expensive validation step, because the database is hit to
        verify, that the :class:`~stockings.models.stock.StockItem` object to be
        sold is actually available in the user's portfolio (represented by a
        :class:`~stockings.models.portfolio.PortfolioItem` object).

        Because this (expensive) step is already performed, furthermore it is
        checked, that the count to be sold is not greater than the available
        count.

        Django includes several layers of validation (e.g. implemented in
        ``Form`` classes or in ``Model`` classes). This validation is provided
        on ``Model`` level, to ensure database integrity. The idea is, that
        trade operations may be re-applied, thus, this validation has to be
        performed here.
        """
        # There are some restrictions for 'SELL' trades:
        # 1. The ``stock_item`` must have a corresponding ``PortfolioItem``
        #   object in ``portfolio``.
        # 2. You are not able to sell more items than available in your
        #   portfolio.
        if self.trade_type == "SELL":
            # Get the ``PortfolioItem``...
            try:
                portfolio_item = self.portfolio.portfolioitem_set.get(
                    stock_item=self.stock_item
                )
            except apps.get_model("stockings.PortfolioItem").DoesNotExist:
                raise ValidationError(
                    _(
                        "You are trying to sell stock, that is not present in your portfolio!"
                    ),
                    code="invalid",
                )

            # Trying to sell more items than available. Setting a maximum value
            # for this trade.
            # TODO: Add a notification of some sort... django messages?
            if self.item_count > portfolio_item.stock_count:
                self.item_count = portfolio_item.stock_count

    @property
    def trade_volume(self):  # noqa: D401
        """The total trade volume (:class:`~stockings.data.StockingsMoney`, read-only).

        *trade volume* is semantically defined as
        ``price per item * item count``. It does **not** include the trade's
        :attr:`costs`.

        Notes
        -----
        `trade_volume` is implemented as a :obj:`property`.

        The value is not stored as an attribute of the `Trade` class; instead,
        it is determined dynamically while fetching `Trade` instances from the
        database using :class:`~stockings.models.trade.TradeManager` (the
        app-specific implementation of :class:`django.db.models.Manager`) by
        :meth:`annotating <django.db.models.query.QuerySet.annotate>` the
        retrieved objects with ``_trade_volume_amount`` (see
        :meth:`stockings.models.trade.TradeQuerySet._annotate_trade_volume`).

        The returned instance of :class:`~stockings.data.StockingsMoney` is then
        built from the annotated `amount`, the instance's :attr:`currency` and
        the instance's :attr:`timestamp`.
        """
        try:
            return StockingsMoney(
                self._trade_volume_amount, self.currency, self.timestamp
            )
        except AttributeError:
            raise StockingsInterfaceError(
                "Could not return attribute. Probably the object was not fetched using "
                "the custom manager (stockings_manager)."
            )

    def _get_costs(self):
        """`getter` for :attr:`costs`.

        Returns
        --------
        :class:`~stockings.data.StockingsMoney`
            An instance of :class:`~stockings.data.StockingsMoney`, where
            :attr:`~stockings.data.StockingsMoney.amount` is
            :attr:`_costs_amount`,
            :attr:`~stockings.data.StockingsMoney.currency` is :attr:`currency`
            and :attr:`~stockings.data.StockingsMoney.timestamp` is
            :attr:`timestamp`.
        """
        return StockingsMoney(self._costs_amount, self.currency, self.timestamp)

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

    def _get_price(self):
        """`getter` for :attr:`price`.

        Returns
        --------
        :class:`~stockings.data.StockingsMoney`
            An instance of :class:`~stockings.data.StockingsMoney`, where
            :attr:`~stockings.data.StockingsMoney.amount` is
            :attr:`_price_amount`,
            :attr:`~stockings.data.StockingsMoney.currency` is :attr:`currency`
            and :attr:`~stockings.data.StockingsMoney.timestamp` is
            :attr:`timestamp`.

        Notes
        -------
        This returns the **price per item**. Thus, it has similarity to
        :class:`~stockings.models.stock.StockItemPrice`.

        The total price of the trade may be calculated like
        ``total_price = costs.add(price.multiply(item_count))``.
        """
        return StockingsMoney(self._price_amount, self.currency, self.timestamp)

    def _set_costs(self, value):
        raise NotImplementedError("to be done")

    def _set_currency(self, new_currency):
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
        """
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "The currency may only be set on `Portfolio` level."
        )

    def _set_price(self, value):
        raise NotImplementedError("to be done")

    costs = property(_get_costs, _set_costs)
    """The costs of this trade operation (:class:`~stockings.data.StockingsMoney`).

    In the context of this class, *costs* refer to whatever your broker is
    charging for the trade.

    Returns a :class:`~stockings.data.StockingsMoney` instance and accepts these
    objects as input.

    Notes
    -----
    This attribute is implemented as a `property`, you may refer to
    :meth:`_get_costs` and :meth:`_set_costs`.

    **get**

    Accessing the attribute returns a :class:`~stockings.data.StockingsMoney`
    object.

    - ``amount`` is stored in :attr:`_costs_amount` as :obj:`decimal.Decimal`.
    - ``currency`` is fetched from the object's :attr:`currency`.
    - ``timestamp`` is fetched from the object's :attr:`timestamp`.

    **set**

    *currently not implemented (yet)*

    **del**

    This is not implemented, thus an :exc:`AttributeError` will be raised.
    """

    currency = property(_get_currency, _set_currency)
    """The currency for `costs` and `price` (:obj:`str`, read-only).

    Notes
    -----
    This attribute is implemented as a `property`, and its value is actually
    fetched from the referenced :class:`~stockings.models.portfolio.Portfolio`
    object.

    Setting this attribute is not possible and will raise
    :exc:`~stockings.exceptions.StockingsInterfaceError`. Deleting the attribute
    will raise :exc:`AttributeError`.
    """

    price = property(_get_price, _set_price)
    """The price per item of the traded :class:`~stockings.models.stock.StockItem`
    (:class:`~stockings.data.StockingsMoney`).

    Returns a :class:`~stockings.data.StockingsMoney` instance and accepts these
    objects as input.

    Notes
    -----
    This attribute is implemented as a `property`, you may refer to
    :meth:`_get_price` and :meth:`_set_price`.

    **get**

    Accessing the attribute returns a `StockingsMoney` object.

    - ``amount`` is stored in :attr:`_price_amount` as :obj:`decimal.Decimal`.
    - ``currency`` is fetched from the object's :attr:`currency`.
    - ``timestamp`` is fetched from the object's :attr:`timestamp`.

    **set**

    *currently not implemented (yet)*

    **del**

    This is not implemented, thus an :exc:`AttributeError` will be raised.
    """
