"""Provides classes that represent stock items."""

# Django imports
from django.db import models
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.stockitem import StockItem


class StockItemPriceManager(models.Manager):
    """Custom manager for :class:`~stockings.models.stock.StockItemPrice`.

    This manager provides some methods, specific for
    :class:`~stockings.models.stock.StockItemPrice` objects. It is applied as
    the default manager (see
    :attr:`StockItemPrice.objects <stockings.models.stock.StockItemPrice.objects>`)

    Warnings
    --------
    The class documentation only includes code, that is actually shipped by the
    `stockings` app. Inherited attributes/methods (provided by Django's
    :class:`~django.db.models.Manager`) are not documented here.
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
        """Provide the base queryset, annotated with a `date` field.

        The :class:`~stockings.models.stock.StockItemPrice` provides date
        information in its
        :attr:`~stockings.models.stock.StockItemPrice._price_timestamp`
        attribute, which provides a :obj:`datetime.datetime` object.

        The provided annotation abstracts/truncates this timestamp and reduces
        it to the date, using :obj:`~django.db.models.functions.TruncDate`.

        Returns
        -------
        :class:`~django.db.models.query.QuerySet`
            The annotated base queryset.
        """
        return super().get_queryset().annotate(date=TruncDate("_price_timestamp"))


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

    objects = StockItemPriceManager()
    """The default manager for these objects."""

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

    def _get_currency(self):
        """`getter` for :attr:`currency`.

        Returns
        -------
        :obj:`str`
            The :attr:`currency` of the object.

        Notes
        -----
        The `currency` is actually fetched from the associated
        :class:`~stockings.models.stock.StockItem` object.
        """
        return self.stock_item.currency

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
        """
        return StockingsMoney(self._price_amount, self.currency, self._price_timestamp,)

    def _set_currency(self, value):
        """`setter` for :attr:`currency`.

        This attribute can not be set directly. The :attr:`currency` is
        actually fetched from the associated
        :class:`stockings.models.stock.StockItem` object.

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
            "The currency may only be set on `StockItem` level."
        )

    def _set_price(self, value):
        """`setter` for :attr:`price`.

        Parameters
        ----------
        value : :class:`~stockings.data.StockingsMoney`
            A `StockingsMoney` instance with the new price information.
        """
        # only update the price, if the provided value is more recent
        if self._price_timestamp >= value.timestamp:
            return

        if self.currency != value.currency:
            value.amount = value.convert(self.currency)
            # value.currency = self._price_currency

        self._price_amount = value.amount
        # self._price_currency = value.currency
        self._price_timestamp = value.timestamp

    currency = property(_get_currency, _set_currency)
    """The currency for `price` (:obj:`str`, read-only).

    Notes
    -----
    This attribute is implemented as a `property`, and its value is actually
    fetched from the referenced :class:`~stockings.models.stock.StockItem`
    object.

    Setting this attribute is not possible and will raise
    :exc:`~stockings.exceptions.StockingsInterfaceError`. Deleting the attribute
    will raise :exc:`AttributeError`.
    """

    price = property(_get_price, _set_price)
    """The actual price information (:class:`~stockings.data.StockingsMoney`).

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
    - ``timestamp`` is fetched from the object's :attr:`_price_timestamp`.

    **set**

    Set the `price` by providing a :class:`~stockings.data.StockingsMoney`
    instance.

    **del**

    This is not implemented, thus an :exc:`AttributeError` will be raised.
    """
