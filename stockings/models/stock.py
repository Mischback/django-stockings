"""Provides classes that represent stock items."""

# Django imports
from django.db import models
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.settings import STOCKINGS_DEFAULT_CURRENCY


class StockItem(models.Model):
    """Represents one distinct tradeable item, most likely a stock.

    This class provide the mean to track tradeable items in the application. It
    stores the required meta information, including a (editable)
    :attr:`full_name` and - as a unique identifier - the item's :attr:`isin`.

    However, the class does not include price information. These are provided in
    :class:`~stockings.models.stock.StockItemPrice`; this class acts as the
    interface to the price information (see :attr:`latest_price`).

    See Also
    --------
    stockings.models.portfolio.PortfolioItem :
        This class actually connects a given `StockItem` with a user's
        :class:`~stockings.models.portfolio.Portfolio`.
    stockings.models.trade.Trade :
        This class is (logically) tightly connected with `StockItem` objects;
        obviously trade operations are performed for 'tradeable items'.

    Warnings
    --------
    The class documentation only includes code, that is actually shipped by the
    `stockings` app. Inherited attributes/methods (provided by Django's
    :class:`~django.db.models.Model`) are not documented here.

    Notes
    -----
    To ensure database integrity, all :class:`django.db.models.ForeignKey`
    relations to this class are implemented with ``on_delete=PROTECT``, so
    `StockItem` objects may be not deleted, if they are still referenced by
    either :class:`~stockings.models.portfolio.PortfolioItem` or
    :class:`~stockings.models.trade.Trade` objects. Otherwise, if a `StockItem`
    object is deleted, all of its price information objects
    (:class:`~stockings.models.stock.StockItemPrice`) are deleted aswell.
    """

    # TODO: Can this be determined automatically, if the ISIN is given? See
    # ``get_fullname_by_isin()``.
    full_name = models.CharField(blank=True, max_length=255)
    """The full name of the item (:obj:`str`).

    This *should* be set to the item's official name.

    See Also
    --------
    stockings.models.stock.StockItem.name

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.CharField`.

    As of now, this has to be provided *manually* during creation of the
    :class:`~stockings.models.stock.StockItem` object.

    This attribute is not used for identification of
    :class:`~stockings.models.stock.StockItem` objects, so 'uniqueness' **is
    not** enforced on database-level. For a unique identification of
    :class:`~stockings.models.stock.StockItem` objects, use
    :attr:`~stockings.models.stock.StockItem.isin` instead.
    """

    # TODO: Add a custom validator!
    isin = models.CharField(db_index=True, max_length=12, primary_key=True, unique=True)
    """The ISIN of the object (:obj:`str`).

    The International Securities Identification Number (ISIN) is used as the
    primary identifier of any :class:`~stockings.models.stock.StockItem`.
    Because of its
    :wiki:`definition <International_Securities_Identification_Number>`, it is
    taken for granted, that this is ``unique``.

    Notes
    -----
    The attribute is implemented as :class:`~django.db.models.CharField` with
    ``max_length=12``, ``primary_key=True`` and ``unique=True``. This enforces
    the semantic characteristics of an ISIN in Django's ORM.

    As of now, no (custom) validation is done on this attribute. In a future
    release, a custom validator
    should be implemented, to verify, that the given *ISIN* is in fact
    referencing some tradeable stock. This will require some sort of
    implementation of a lookup engine.
    """

    name = models.CharField(blank=True, max_length=100)
    """A short and handy name for the item  (:py:obj:`str`).

    While :attr:`~stockings.models.stock.StockItem.full_name` should be used to
    store the official name of the tracked stock, this is a shorter and more
    handy version of the name.

    Notes
    -----
    The attribute is implemented as :class:`~django.db.models.CharField`.

    This has to be provided *manually* and should be *unique enough* to allow
    identification of the stock, but 'uniqueness' is not enforced in any way.

    If provided, the object's :meth:`__str__()` method will include this
    attribute in the object's representation.
    """

    # The currency for all money-related fields.
    # See the property ``currency`` and the methods ``_get_currency()`` / ``_set_currency()`` .
    _currency = models.CharField(default=STOCKINGS_DEFAULT_CURRENCY, max_length=3)
    """The actual database representation of :attr:`currency`.

    Notes
    -----
    This is implemented as :class:`~django.db.models.CharField` with
    ``max_length=3``. The currency is stored as its
    :wiki:`currency code as described by ISO 4217 <ISO_4217>`.

    The provided default value can be configured using
    :attr:`~stockings.settings.STOCKINGS_DEFAULT_CURRENCY` in the project's
    settings.
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        verbose_name = _("Stock Item")
        verbose_name_plural = _("Stock Items")

    def __str__(self):  # noqa: D105
        if self.name != "":
            return "{} ({})".format(self.name, self.isin,)
        else:
            return "{}".format(self.isin,)

    def get_fullname_by_isin(self):
        """Fetch and update the ``full_name`` of an item.

        Raises
        -------
        NotImplementedError
            This is currently not implemented and dependent on the
            implementation of a data provider.
        """
        raise NotImplementedError(
            "Needs an implementation of automatic data providers"
        )  # pragma: nocover

    @classmethod
    def get_sentinel_item(cls):  # pragma: nocover
        """Return a sentinel / placeholder object to maintain database integrity.

        Notes
        ------
        Currently, this is not actively used, because all ForeignKey relations
        to StockItem are set to ``PROTECTED``. Anyway, this might be useful, if
        deletion of :class:`~stockings.models.stock.StockItem` objects should be
        enabled in future releases.
        """
        # ``get_or_create`` returns a tuple, consisting of the (fetched or
        # created) object and a boolean flag (indicating, if the object was
        # created *freshly*). Only the first item of that tuple (the object)
        # is returned.
        return cls.object.get_or_create(
            isin="XX0000000000",
            defaults={
                "full_name": "The referenced item got deleted!",
                "name": "Deleted Item",
            },
        )[0]

    def _is_active(self):
        """`getter` for :attr:`is_active`.

        Returns
        -------
        :obj:`bool`
            The :attr:`is_active` of the object.
        """
        return self.portfolioitem_set.filter(is_active=True).count() > 0

    def _get_currency(self):
        """`getter` for :attr:`currency`.

        Returns
        -------
        :obj:`str`
            The :attr:`currency` of the object.
        """
        return self._currency

    def _get_latest_price(self):
        """`getter` for :attr:`latest_price`.

        Returns
        -------
        :class:`~stockings.data.StockingsMoney`
            The :attr:`latest_price` of the object, as provided by an
            associated :class:`~stockings.models.stock.StockItemPrice` object.
        """
        return StockItemPrice.get_latest_price(self)

    def _set_currency(self, new_currency):
        """`setter` for :attr:`currency`.

        Set the currency for all associated
        :class:`~stockings.models.stock.StockItemPrice` objects.

        Parameters
        ----------
        new_currency : :obj:`str`
            The new currency to be applied.
        """
        for item in self.stockitemprice_set.iterator():
            item._apply_new_currency(new_currency)
            item.save()

        self._currency = new_currency

    def _set_latest_price(self, value):
        """`setter`for :attr:`latest_price`.

        Parameters
        ----------
        value : :class:`~stockings.data.StockingsMoney`
            The new price information to be set.
        """
        StockItemPrice.set_latest_price(self, value)

    currency = property(_get_currency, _set_currency)
    """The currency for the item's price information (:obj:`str`).

    The actual price information is not stored with
    :class:`~stockings.models.stock.StockItem` objects but rather with
    :class:`~stockings.models.stock.StockItemPrice` objects. These, however,
    rely on this attribute for currency information.

    This implementation ensures, that all price information share the same
    value for their currency and enables (meaningful) statistical evaluation.

    Notes
    -------
    This attribute is implemented as a `property`. You may refer to
    :meth:`_get_currency` and :meth:`_set_currency`
    for implementation details.

    **get**

    Accessing the attribute returns a :obj:`str` with the current currency.

    **set**

    Setting this attribute will update all related instances of
    :class:`~stockings.models.stock.StockItemPrice` by calling their
    :meth:`~stockings.models.stock.StockItemPrice._apply_new_currency` method.
    Finally, this object's :attr:`~stockings.models.stock.StockItem._currency`
    is updated.

    **del**
    This is not implemented, thus an ``AttributeError`` will be raised.
    """

    is_active = property(_is_active)
    """Flag to indicate, if this item is active (:obj:`bool`, read-only).

    A `StockItem` is considered active, if it is referenced by at least one
    :class:`~stockings.models.portfolio.PortfolioItem` object, that is active
    itsself.

    See Also
    ---------
    stockings.models.portfolio.PortfolioItemManager.get_queryset :
        The corresponding
        :attr:`~stockings.models.portfolio.PortfolioItem.is_active` is provided
        as an annotation to :class:`~stockings.models.portfolio.PortfolioItem`
        by its associated
        :class:`Manager implementation <stockings.models.portfolio.PortfolioItemManager>`.
    """

    latest_price = property(_get_latest_price, _set_latest_price)
    """The most recent price information for this item
    (:class:`~stockings.data.StockingsMoney`).

    The actual price information is not stored with :class:`StockItem` objects
    but rather with :class:`~stockings.models.stock.StockItemPrice` objects.

    This implementation allows statistical evaluation of price information,
    because the app can keep historical prices aswell.

    Notes
    -------
    This attribute is implemented as a `property`. You may refer to
    :meth:`_get_latest_price` and :meth:`_set_latest_price` for implementation
    details.

    **get**

    Accessing the attribute returns a :class:`~stockings.data.StockingsMoney`
    instance with the most recent price information. This relies on
    :meth:`stockings.models.stock.StockItemPrice.get_latest_price`.

    **set**

    Setting the attribute requires an instance of
    :class:`~stockings.data.StockingsMoney` and relies on
    :meth:`stockings.models.stock.StockItemPrice.set_latest_price`.

    **del**
    This is not implemented, thus an ``AttributeError`` will be raised.
    """


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
    """Tracks the price of a given `StockItem`."""

    objects = StockItemPriceManager()

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.CASCADE, unique_for_date="_price_timestamp"
    )

    # The latest price information for the item.
    _price_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)
    _price_timestamp = models.DateTimeField(default=now)

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
        """Return `StockingsMoney` instance with the most recent price information."""
        return cls.objects.get_latest_price_object(stock_item=stock_item).price

    @classmethod
    def set_latest_price(cls, stock_item, value):
        """Set latest price information for a given `stock_item`.

        The method evaluates `value.timestamp` to determine if either:
            - an existing `StockItemPrice` object can be updated
            - a new `StockItemPrice` object has to be created
            - no action is required
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

        latest_obj._set_price(value)
        latest_obj.save()

    def _apply_new_currency(self, new_currency):
        """Set a new currency for the object and convert price information."""
        new_value = self.price.convert(new_currency)
        self._price_amount = new_value.amount
        self._price_timestamp = new_value.timestamp

    def _get_currency(self):
        return self.stock_item.currency

    def _get_price(self):
        return StockingsMoney(self._price_amount, self.currency, self._price_timestamp,)

    def _set_currency(self, value):
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "The currency may only be set on `StockItem` level."
        )

    def _set_price(self, value):

        # only update the price, if the provided value is more recent
        if self._price_timestamp >= value.timestamp:
            return

        if self.currency != value.currency:
            value.amount = value.convert(self.currency)
            # value.currency = self._price_currency

        self._price_amount = value.amount
        # self._price_currency = value.currency
        self._price_timestamp = value.timestamp

    currency = property(_get_currency, _set_currency, doc="TODO: Add docstring here!")

    price = property(_get_price, _set_price, doc="TODO: Add docstring here!")
