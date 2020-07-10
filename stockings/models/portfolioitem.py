"""Provides the :class:`~stockings.models.portfolioitem.PortfolioItem`."""

# Python imports
import logging

# Django imports
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
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
          :class:`stockings.models.portfolio.Portfolio` instance. This
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

    stockitem = models.ForeignKey(StockItem, on_delete=models.PROTECT)
    """Reference to a :class:`~stockings.models.stock.StockItem`.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.ForeignKey` to
    :class:`~stockings.models.stock.StockItem` with ``on_delete=PROTECT``,
    meaning that it is not possible to delete the
    :class:`~stockings.models.stock.StockItem` while it is referenced by a
    `PortfolioItem` object.
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        ordering = ["portfolio", "stockitem"]
        unique_together = ["portfolio", "stockitem"]
        verbose_name = _("Portoflio Item")
        verbose_name_plural = _("Portfolio Items")

    def __str__(self):  # noqa: D105
        return "{} - {}".format(self.portfolio, self.stockitem)  # pragma: nocover

    def _apply_new_currency(self, new_currency):
        raise NotImplementedError

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

    @cached_property
    def stock_value(self):  # noqa: D401
        """The current value of stocks in this `PortfolioItem`(:class:`~stockings.data.StockingsMoney`, read-only).

        Warnings
        --------
        Instances of `PortfolioItem` and
        :class:`~stockings.models.stockitemprice.StockItemPrice` do not
        necessarily share the same currency. While calculating the value of this
        attribute, coversion of currency is applied. Please note, that this is
        currently not implemented and will raise a :exc:`NotImplementedError`.

        Notes
        -----
        `stock_value` is implemented as
        :class:`django.utils.functional.cached_property`.

        The required values to populate the
        :class:`~stockings.data.StockingsMoney` instance are not directly stored
        as attributes of this `PortfolioItem` object. Instead, they are
        dynamically calculated by evaluating other models, most notable
        :class:`stockings.models.stockitemprice.StockItemPrice` (and, by using
        :attr:`~stockings.models.portfolioitem.PortfolioItem.stock_count`,
        :class:`stockings.models.trade.Trade`).
        """
        try:
            # TODO: ENSURE correct currency
            return (
                StockingsMoney(
                    self._price_per_item_amount,
                    self._price_per_item_currency,
                    self._price_per_item_timestamp,
                )
                .multiply(self.stock_count)
                .convert(self.currency)
            )
        except AttributeError:
            logger.info(
                "Missing value while accessing attribute 'stock_value'. "
                "Performing required database queries!"
            )
            logger.debug(
                "'stock_value' is accessed while required values are not available. "
                "Most likely, the 'PortfolioItem' was not fetched using "
                "'PortfolioItem.stockings_manager', so that the specific annotation "
                "is missing."
            )
            # TODO: ENSURE correct currency
            return self.stockitem.latest_price.multiply(self.stock_count).convert(
                self.currency
            )
