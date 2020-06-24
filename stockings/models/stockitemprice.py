"""Provides classes that represent stock items."""

# Python imports
import logging

# Django imports
from django.db import models
from django.db.models.functions import TruncDate
from django.utils.functional import cached_property
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.models.stockitem import StockItem

# get a module-level logger
logger = logging.getLogger(__name__)


class StockItemPriceQuerySet(models.QuerySet):
    """App-specific implementation of :class:`django.db.modesl.QuerySet`.

    Notes
    -----
    This :class:`~django.db.models.QuerySet` implementation provides
    app-specific augmentations.

    The provided methods augment/extend the retrieved
    :class:`stockings.models.stockitemprice.StockItemPrice` instances by
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
          :model:`stockings.models.stockitem.StockItem` instance. This
          annotation is provided by default, because instances of
          :class:`~stockings.models.stockitemprice.StockItemPrice` expose several
          money-related attributes. The implementation of
          :attr:`StockItemPrice.currency <stockings.models.stockitemprice.StockItemPrice.currency`
          ensures, that a database lookup is only performed once, but even this
          database hit may be mitigated by this annotation.
        - :meth:`_annotate_date`
          The date-part of
          :attr:`StockItemPrice._price_timestamp <stockings.models.stockitemprice.StockItemPrice._price_timestamp>`.
        """
        return self._annotate_date()._annotate_currency()

    def _annotate_currency(self):
        """Annotate each object with `_currency`.

        The `currency` for instances of :class:`~stockings.models.stockitemprice.StockItemPrice`
        is actually stored at :class:`stockings.models.stockitem.StockItem`.
        The annotation uses Django's feature to access related objects to fetch
        the `currency`.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The annotated queryset.
        """
        return self.annotate(_currency=models.F("stock_item___currency"))

    def _annotate_date(self):
        """Annotate each object with `date`.

        `date` is the abstracted/truncated
        :attr:`StockItemPrice._price_timestamp <stockings.models.stockitemprice.StockItemPrice._price_timestamp>`
        that is reduced by :obj:`~django.db.models.functions.TruncDate`.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The annotated queryset.
        """
        return self.annotate(date=TruncDate("_price_timestamp"))


class StockItemPriceManager(models.Manager):
    """App-/model-specific implementation of :class:`django.db.models.Manager`.

    Notes
    -----
    This :class:`~django.db.models.Manager` implementation is used as an
    additional manager of
    :class:`~stockings.models.stockitemprice.StockItemPrice` (see
    :attr:`stockings.models.stockitemprice.StockItemPrice.stockings_manager`.

    This implementation inherits its functionality from
    :class:`django.db.models.Manager` and provides identical funtionality.
    Furthermore, it augments the retrieved objects with additional attributes,
    using the custom :class:`~django.db.models.QuerySet` implementation
    :class:`~stockings.models.stockitemprice.StockItemPriceQuerySet`.
    """

    def get_latest_price_object(self, stock_item):
        """Return the most recent `StockItemPrice` object.

        The most recent object is defined as the one with the most recent
        :attr:`~stockings.models.stock.StockItemPrice._timestamp`.

        Parameters
        ----------
        stock_item : :class:`~stockings.models.stock.StockItem`
            The `StockItem` for which the latest price information should be
            retrieved.

        Returns
        -------
        :class:`~stockings.models.stock.StockItemPrice`
            The most recent `StockItemPrice` object.
        """
        return (
            self.get_queryset().filter(stock_item=stock_item).latest("_price_timestamp")
        )

    def get_queryset(self):
        """Use the app-/model-specific :class:`~stockings.models.stockitemprice.StockItemPriceQuerySet` by default.

        Returns
        -------
        :class:`django.models.db.QuerySet`
            This queryset is provided by
            :class:`stockings.models.stockitemprice.StockItemPriceQuerySet` and
            applies its
            :meth:`~stockings.models.stockitemprice.StockItemPriceQuerySet.default`
            method. The retrieved objects will be annotated with additional
            attributes.
        """
        return StockItemPriceQuerySet(self.model, using=self._db).default()


class StockItemPrice(models.Model):
    """Tracks the price of a given :class:`~stockings.models.stock.StockItem`.

    Warnings
    --------
    The class documentation only includes code, that is actually shipped by the
    `stockings` app. Inherited attributes/methods (provided by Django's
    :class:`~django.db.models.Model`) are not documented here.

    Notes
    -----
    Instances of this class are used to track price information of the
    referenced :class:`~stockings.models.stock.StockItem` objects.

    In combination with its
    :class:`~stockings.models.stock.StockItemPriceManager`, the most recent
    `StockItemPrice` instance can be retrieved and updated.

    These objects are not meant to be accessed directly by an user of the app,
    they should always be interfaced using the provided methods of an
    :class:`~stockings.models.stock.StockItem`, e.g. using its
    :attr:`StockItem.latest_price <stockings.models.stock.StockItem.latest_price>`
    attribute.
    """

    objects = models.Manager()
    """The model's default manager.

    The default manager is set to :class:`django.db.models.Manager`, which is
    the default value. In order to add the custom :attr:`stockings_manager` as
    an *additional* manager, the default manager has to be provided explicitly
    (see :djangodoc:`topics/db/managers/#default-managers`).
    """

    stockings_manager = StockItemPriceManager()
    """App-/model-specific manager, that provides additional functionality.

    This manager is set to
    :class:`stockings.models.stockitemprice.StockItemPriceManager`. Its
    implementation provides augmentations of `Trade` objects, by annotating them
    on database level.

    For a list of (virtual) attributes, that are solely provided as annotations,
    refer to :class:`stockings.models.stockitemprice.StockItemPriceQuerySet`.
    """

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, unique_for_date="_price_timestamp",
    )
    """Reference to a :class:`~stockings.models.stock.StockItem`.

    Notes
    -------
    This is implemented as a :class:`~django.db.models.ForeignKey` with
    ``on_delete=CASCADE``, meaning if the referenced
    :class:`~stockings.models.stock.StockItem` object is deleted, all
    referencing `StockItemPrice` objects are discarded aswell.

    Additionally, ``unique_for_date=_price_timestamp`` is applied. This
    constraint ensures, that there exists only one `StockItemPrice` object for
    any given :class:`~stockings.models.stock.StockItem` per day / date.
    Technically, :attr:`_price_timestamp` stores a :obj:`datetime.datetime`.
    """

    _price_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    """The `amount` part of :attr:`price`.

    Notes
    -------
    This is implemented as a :class:`~django.db.models.DecimalField`.
    """

    _price_timestamp = models.DateTimeField(default=now)
    """The `timestamp` part of the :attr:`price` attribute.

    Notes
    -------
    This is implemented as a :class:`~django.db.models.DateTimeField` with
    ``default=now``, effectively provided by :func:`django.utils.timezone.now`.
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        verbose_name = _("Stock Item Price")
        verbose_name_plural = _("Stock Item Prices")

    def __str__(self):  # noqa: D105
        return "{} - {} {} ({})".format(
            self.stock_item, self.currency, self._price_amount, self._price_timestamp,
        )  # pragma: nocover

    @cached_property
    def currency(self):  # noqa: D401
        """The currency for money-related fields (:obj:`str`, read-only).

        The *currency* is actually determined by accessing the parent
        :class:`stockings.models.stockitem.StockItem`.

        Notes
        -----
        `currency` is implemented as
        :class:`django.utils.functional.cached_property`
        """
        try:
            return self._currency
        except AttributeError:
            logger.debug("Fetching 'currency' from parent 'stockitem' instance.")
            return self.stock_item.currency

    @cached_property
    def price(self):  # noqa: D401
        """The price per item (:class:`~stockings.data.StockingsMoney`, read-only).

        Notes
        -----
        `price` is implemented as
        :class:`django.utils.functional.cached_property`.
        """
        return StockingsMoney(self._price_amount, self.currency, self._price_timestamp)

    @classmethod
    def get_latest_price(cls, stock_item):
        """Return the most recent price information.

        Parameters
        ----------
        stock_item : :class:`~stockings.models.stock.StockItem`
            The `StockItem` for which the latest price information should be
            retrieved.

        Returns
        -------
        :class:`~stockings.data.StockingsMoney`
            The :attr:`price` of the most recent `StockItemPrice` object.

        See Also
        --------
        stockings.models.stock.StockItemPriceManager.get_latest_price_object
        """
        return cls.objects.get_latest_price_object(stock_item=stock_item).price

    @classmethod
    def set_latest_price(cls, stock_item, value):
        """Set latest price information.

        Parameters
        ----------
        stock_item : :class:`~stockings.models.stock.StockItem`
            The `StockItem` for which the latest price information should be
            updated.
        value : :class:`~stockings.data.StockingsMoney`
            A `StockingsMoney` instance with the new price information.

        Notes
        -----
        The method evaluates ``value.timestamp`` to determine if either:

            - an existing `StockItemPrice` object can be updated
            - a new `StockItemPrice` object has to be created
            - no action is required

        If new price information is applied, the object is saved.
        """
        # get the latest available object
        latest_obj = cls.objects.get_latest_price_object(stock_item=stock_item)

        # `latest_obj` is more recent than the provided value -> do nothing
        if latest_obj._price_timestamp >= value.timestamp:
            return None

        # provided value is actually on a new day/date
        if latest_obj._price_timestamp.date() < value.timestamp.date():
            latest_obj = cls.objects.create(
                stock_item=stock_item, _price_timestamp=value.timestamp
            )

        # actually set the new price
        latest_obj._set_price(value)
        latest_obj.save()

    def _apply_new_currency(self, new_currency):
        """Convert the :attr:`price` to a new currency.

        Parameters
        ----------
        new_currency : :obj:`str`
            The currency to convert to.

        See Also
        --------
        stockings.models.stock.StockItem._set_currency

        Notes
        -----
        The object's attributes are updated, but the object **is not saved**.
        This is the caller's responsibility.
        """
        new_value = self.price.convert(new_currency)
        self._price_amount = new_value.amount
        self._price_timestamp = new_value.timestamp
