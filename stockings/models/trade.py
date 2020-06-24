"""Provides the :class:`~stockings.models.trade.Trade` and its related classes.

This includes the Django model :class:`~stockings.models.trade.Trade`, the
app-/model-specific `Manager` :class:`~stockings.models.trade.TradeManager` and
the `QuerySet` :class:`~stockings.models.trade.TradeQuerySet`.

Instances of :class:`~stockings.models.trade.Trade` are the main mean to
model cash flows into the :class:`~stockings.models.portfolio.Portfolio` (by
buying stock) or out of the `Portfolio` (by selling stock).
"""

# Python imports
import logging

# Django imports
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models.functions import Coalesce
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.models.portfolioitem import PortfolioItem

logger = logging.getLogger(__file__)


class TradeQuerySet(models.QuerySet):
    """App-specific implementation of :class:`django.db.models.QuerySet`.

    Notes
    -----
    This :class:`~django.db.models.QuerySet` implementation provides
    app-specific augmentations.

    The provided methods augment/extend the retrieved
    :class:`stockings.models.trade.Trade` instances by annotating them with
    additional information.
    """

    def default(self):
        """Return a queryset with all class-specific annotations.

        *Class-specific* does mean, the provided annotations are only relying on
        actual fields of the :class:`~stockings.models.trade.Trade` model, but
        do not reach out to other models. For this feature see
        :meth:`~stockings.models.trade.TradeQuerySet.full`.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The queryset annotated with :meth:`_annotate_math_count` and
            :meth:`_annotate_trade_volume`.

        Notes
        -----
        The following annotations are applied:

        - :meth:`_annotate_math_count`
          converts :attr:`~stockings.models.trade.Trade.item_count` into a
          negative number, if :attr:`~stockings.models.trade.Trade.trade_type`
          equals :attr:`~stockings.models.trade.Trade.TRADE_TYPE_SELL`.
        - :meth:`_annotate_trade_volume`
          adds the *trade volume*, which is defined as product of
          :attr:`~stockings.models.trade.Trade.item_count` and
          :attr:`~stockings.models.trade.Trade._price_amount`.

        This method is applied by
        :meth:`stockings.models.trade.TradeManager.get_queryset`, meaning these
        annotations are provided by default when using the class-specific
        manager.
        """
        return self._annotate_math_count()._annotate_trade_volume()

    def full(self):
        """Return a fully annotated queryset.

        *Fully annotated* does mean that, beside the class-specific annotations
        provided by :meth:`~stockings.models.trade.TradeQuerySet.default`,
        related objects are selected using
        :meth:`django.db.models.query.QuerySet.select_related`.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            A queryset, providing the related
            :class:`stockings.models.portfolio.Portfolio`,
            :class:`stockings.models.portfolioitem.PortfolioItem` and
            :class:`stockings.models.stockitem.StockItem` objects.

        Warnings
        --------
        :meth:`~stockings.models.trade.TradeQuerySet._annotate_currency` is
        **not** applied. This may result in a log message while accessing
        :attr:`Trade.currency <stockings.models.trade.Trade.currency`, stating
        that the attribute is retrieved from the parent
        :class:`~stockings.models.portfolioItem.PortfolioItem` instance.
        However, this will *not* result in another database query, because the
        required object (in fact of type
        :class:`~stockings.models.portfolio.Portfolio`) is already retrieved.
        """
        return self.select_related(
            "portfolioitem__portfolio", "portfolioitem__stock_item"
        )

    def _annotate_currency(self):
        """Annotate each object with `_currency`.

        The `currency` for instances of :class:`~stockings.models.trade.Trade`
        is actually stored at :class:`stockings.models.portfolio.Portfolio`.

        The annotation uses Django's feature to access related objects to fetch
        the `currency`.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The annotated queryset.
        """
        return self.annotate(_currency=models.F("portfolioitem__portfolio___currency"))

    def _annotate_math_count(self):
        """Annotate each object with `_math_count`.

        `_math_count` describes the *mathematical count*, which basically means,
        that the different :attr:`~stockings.models.trade.Trade.trade_type` are
        used to determine, if the
        :attr:`~stockings.models.trade.Trade.item_count` should be considered
        ``positive`` or ``negative``.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The annotated queryset.
        """
        return self.annotate(
            _math_count=models.Case(
                models.When(
                    trade_type=Trade.TRADE_TYPE_SELL,
                    then=models.Value("-1") * models.F("item_count"),
                ),
                default=models.F("item_count"),
                output_field=models.IntegerField(),
            )
        )

    def _annotate_trade_volume(self):
        """Annotate each object with `_trade_volume_amount`.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The annotated queryset.
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
        return TradeQuerySet(self.model, using=self._db).default()

    def trade_summary(self, portfolioitem=None):
        """Aggregate trade information by `PortfolioItem` and provide them as annotation.

        The method produces a summary of all
        :class:`~stockings.models.trade.Trade` instances, grouped by
        `portfolioitem`.

        Returns
        -------
        :class:`django.models.db.QuerySet`
        """
        _qs = self.get_queryset()

        if portfolioitem is not None:
            _qs = _qs.filter(portfolioitem=portfolioitem)

        return (
            _qs.order_by()
            .values("portfolioitem")
            .annotate(
                # trading costs can simply be summed
                costs_amount=Coalesce(models.Sum("_costs_amount"), models.Value(0)),
                # the most recent `timestamp` is provided
                costs_latest_timestamp=models.Max("timestamp"),
                # the current stock count
                current_stock_count=models.Sum("_math_count"),
                # money spent to PURCHASE stock
                purchase_amount=Coalesce(
                    models.Sum(
                        "_trade_volume_amount", filter=models.Q(trade_type="BUY")
                    ),
                    models.Value(0),
                ),
                # the `timestamp` of the most recent PURCHASE
                purchase_latest_timestamp=models.Max(
                    "timestamp", filter=models.Q(trade_type="BUY")
                ),
                # money earned by SELLING stock
                sale_amount=Coalesce(
                    models.Sum(
                        "_trade_volume_amount", filter=models.Q(trade_type="SELL")
                    ),
                    models.Value(0),
                ),
                # the `timestamp` of the most recent SALE
                # FIXME: There might be no sale; Is a default value (via COALESCE) required?
                sale_latest_timestamp=models.Max(
                    "timestamp", filter=models.Q(trade_type="SELL")
                ),
            )
        )


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
    """

    # Define the choices for `type` field.
    # TODO: Django 3.0 introduces another way for this!
    # See: https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
    # Don't use this, if it is the only 3.0 feature to keep backwards compatibility,
    # but DO use this, if there are other 3.0 features, that *must* be used!
    TRADE_TYPE_BUY = "BUY"
    TRADE_TYPE_SELL = "SELL"
    TRADE_TYPES = [
        (TRADE_TYPE_BUY, _("Buy")),
        (TRADE_TYPE_SELL, _("Sell")),
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

    portfolioitem = models.ForeignKey(
        PortfolioItem, on_delete=models.CASCADE, related_name="trades"
    )
    """Reference to a :class:`~stockings.models.portfolioitem.PortfolioItem`.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.ForeignKey` to
    :class:`~stockings.models.portfolioitem.PortfolioItem` with
    ``on_delete=CASCADE``, meaning that, if the
    :class:`~stockings.models.portfolio.Portfolio` object is deleted, all
    referencing `Trade` objects will be discarded aswell.
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
        ordering = ["-timestamp"]
        verbose_name = _("Trade")
        verbose_name_plural = _("Trades")

    def __str__(self):  # noqa: D105
        return "[{}] {} - {} ({})".format(
            self.trade_type,
            self.portfolioitem.portfolio,
            self.portfolioitem.stock_item,
            self.timestamp,
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
            # Trying to sell more items than available. Setting a maximum value
            # for this trade.
            # TODO: Add a notification of some sort... django messages?
            if self.item_count > self.portfolioitem.stock_count:
                self.item_count = self.portfolioitem.stock_count

    @cached_property
    def costs(self):  # noqa: D401
        """The costs of this trade operation (:class:`~stockings.data.StockingsMoney`, read-only).

        In the context of this class, *costs* refer to whatever your broker is
        charging for the trade.

        Notes
        -----
        `costs` is implemented as
        :class:`django.utils.functional.cached_property`.
        """
        return StockingsMoney(self._costs_amount, self.currency, self.timestamp)

    @cached_property
    def currency(self):  # noqa: D401
        """The currency for `costs` and `price` (:obj:`str`, read-only).

        The *currency* is actually determined by accessing the associated
        :class:`stockings.models.portfolioitem.PortfolioItem` (which, accesses
        the parent :class:`stockings.models.portfolio.Portfolio`)

        Notes
        -----
        `currency` is implemented as
        :class:`django.utils.functional.cached_property`
        """
        try:
            return self._currency
        except AttributeError:
            logger.debug("Fetching 'currency' from parent 'portfolioitem' instance.")
            return self.portfolioitem.currency

    @cached_property
    def price(self):  # noqa: D401
        """The price per item (:class:`~stockings.data.StockingsMoney`, read-only).

        Notes
        -----
        `price` is implemented as
        :class:`django.utils.functional.cached_property`.
        """
        return StockingsMoney(self._price_amount, self.currency, self.timestamp)

    @cached_property
    def trade_volume(self):  # noqa: D401
        """The total trade volume (:class:`~stockings.data.StockingsMoney`, read-only).

        *trade volume* is semantically defined as
        ``price per item * item count``. It does **not** include the trade's
        :attr:`costs`.

        Notes
        -----
        `trade_volume` is implemented as
        :class:`django.utils.functional.cached_property`.
        """
        try:
            return StockingsMoney(
                self._trade_volume_amount, self.currency, self.timestamp
            )
        except AttributeError:
            return StockingsMoney(
                self.item_count * self._price_amount, self.currency, self.timestamp
            )
