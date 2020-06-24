"""Provides the :class:`~stockings.models.portfolioitem.PortfolioItem`."""

# Python imports
import logging

# Django imports
from django.db import models
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.portfolio import Portfolio
from stockings.models.stockitem import StockItem

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
        """Return a queryset with annotations.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The annotated queryset.

        Notes
        -----
        The following annotations are provided:

        - :meth:`_annotate_currency`
          The currency as provided by the parent
          :model:`stockings.models.portfolio.Portfolio` instance. This
          annotation is provided by default, because instances of
          :class:`~stockings.models.portfolioitem.PortfolioItem` expose several
          money-related attributes. The implementation of
          :attr:`PortfolioItem.currency <stockings.models.portfolioitem.PortfolioItem.currency`
          ensures, that a database lookup is only performed once, but even this
          database hit may be mitigated by this annotation.
        """
        return self._annotate_currency()

    def _annotate_currency(self):
        """Annotate each object with `_currency`.

        The `currency` for instances of
        :class:`~stockings.models.portfolioitem.PortfolioItem` is actually
        stored at :class:`stockings.models.portfolio.Portfolio`. The annotation
        uses Django's feature to access related objects to fetch the `currency`.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The annotated queryset.
        """
        return self.annotate(_currency=models.F("portfolio___currency"))


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

        Notes
        -----
        `cash_in` is implemented as
        :class:`django.utils.functional.cached_property`.

        The required values to populate the
        :class:`~stockings.data.StockingsMoney` instance are not directly stored
        as attributes of this `PortfolioItem` object. Instead, they are
        dynamically calculated by evaluating other models, most notably
        :class:`stockings.models.trade.Trade`.
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
            trade_information = list(
                self.trades(manager="stockings_manager").trade_summary(
                    portfolioitem=self
                )
            )[0]

            return StockingsMoney(
                trade_information["purchase_amount"],
                self.currency,
                trade_information["purchase_latest_timestamp"],
            )

    @cached_property
    def cash_out(self):  # noqa: D401
        """The cash flow out of this `PortfolioItem` (:class:~stockings.data.StockingsMoney`, read-only).

        Notes
        -----
        `cash_out` is implemented as
        :class:`django.utils.functional.cached_property`.

        The required values to populate the
        :class:`~stockings.data.StockingsMoney` instance are not directly stored
        as attributes of this `PortfolioItem` object. Instead, they are
        dynamically calculated by evaluating other models, most notably
        :class:`stockings.models.trade.Trade`.
        """
        try:
            return StockingsMoney(
                self._cash_out_amount, self.currency, self._cash_out_timestamp
            )
        except AttributeError:
            logger.info(
                "Missing values while accessing attribute 'cash_out'. "
                "Performing required database queries!"
            )
            logger.debug(
                "'cash_out' is accessed while required values are not available. Most "
                "likely, the 'PortfolioItem' was not fetched using "
                "'PortfolioItem.stockings_manager', so that the specific annotations "
                "are missing."
            )

            # collect the required information
            trade_information = list(
                self.trades(manager="stockings_manager").trade_summary(
                    portfolioitem=self
                )
            )[0]

            return StockingsMoney(
                trade_information["sale_amount"],
                self.currency,
                trade_information["sale_latest_timestamp"],
            )

    @cached_property
    def costs(self):  # noqa: D401
        """The costs associated with this `PortfolioItem` (:class:~stockings.data.StockingsMoney`, read-only).

        Notes
        -----
        `costs` is implemented as
        :class:`django.utils.functional.cached_property`.

        The required values to populate the
        :class:`~stockings.data.StockingsMoney` instance are not directly stored
        as attributes of this `PortfolioItem` object. Instead, they are
        dynamically calculated by evaluating other models, most notably
        :class:`stockings.models.trade.Trade`.
        """
        try:
            return StockingsMoney(
                self._cash_out_amount, self.currency, self._cash_out_timestamp
            )
        except AttributeError:
            logger.info(
                "Missing values while accessing attribute 'costs'. "
                "Performing required database queries!"
            )
            logger.debug(
                "'costs' is accessed while required values are not available. Most "
                "likely, the 'PortfolioItem' was not fetched using "
                "'PortfolioItem.stockings_manager', so that the specific annotations "
                "are missing."
            )

            # collect the required information
            trade_information = list(
                self.trades(manager="stockings_manager").trade_summary(
                    portfolioitem=self
                )
            )[0]

            return StockingsMoney(
                trade_information["costs_amount"],
                self.currency,
                trade_information["costs_latest_timestamp"],
            )

    @cached_property
    def currency(self):  # noqa: D401
        """The currency for all money-related fields (:obj:`str`, read-only).

        The *currency* is actually determined by accessing the parent
        :class:`stockings.models.portfolio.Portfolio`

        Notes
        -----
        `currency` is implemented as
        :class:`django.utils.functional.cached_property`
        """
        try:
            return self._currency
        except AttributeError:
            logger.debug("Fetching 'currency' from parent 'portfolio' instance.")
            return self.portfolio.currency

    @cached_property
    def stock_count(self):  # noqa: D401
        """The count of stocks in this `PortfolioItem` (:obj:int`, read-only).

        Notes
        -----
        `stock_count` is implemented as
        :class:`django.utils.functional.cached_property`.

        The required values to populate the
        :class:`~stockings.data.StockingsMoney` instance are not directly stored
        as attributes of this `PortfolioItem` object. Instead, they are
        dynamically calculated by evaluating other models, most notably
        :class:`stockings.models.trade.Trade`.
        """
        try:
            return self._stock_count
        except AttributeError:
            logger.info(
                "Missing value while accessing attribute 'stock_count'. "
                "Performing required database queries!"
            )
            logger.debug(
                "'stock_count' is accessed while required values are not available. Most "
                "likely, the 'PortfolioItem' was not fetched using "
                "'PortfolioItem.stockings_manager', so that the specific annotation "
                "is missing."
            )

            # collect the required information
            trade_information = list(
                self.trades(manager="stockings_manager").trade_summary(
                    portfolioitem=self
                )
            )[0]

            return trade_information["current_stock_count"]

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
