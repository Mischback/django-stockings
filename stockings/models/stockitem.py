"""Provides the :class:`~stockings.models.stockitem.StockItem`.

Instances of :class:`~stockings.models.stockitem.StockItem` represent the
actual stocks, providing general data about the items.
"""

# Python imports
import logging

# Django imports
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.settings import STOCKINGS_DEFAULT_CURRENCY

# get a module-level logger
logger = logging.getLogger(__name__)


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

    @property
    def currency(self):  # noqa: D401
        """The currency for money-related fields (:obj:`str`).

        While `StockItem` does not store money-related information, in
        particular no *amounts*, all related instances of
        :class:`stockings.models.stockitemprice.StockItemPrice` are to share the
        same currency, thus, it is provided in the parent element, which is a
        `StockItem` instance.

        Warnings
        --------
        **setting** `currency` will update all related instances of
        :class:`stockings.models.stockitemprice.StockItemPrice` and will
        automatically call this object's ``save()`` method to ensure the
        integrity of data.

        Notes
        -----
        This attribute is implemented as a :obj:`property`.

        The **getter** simply returns the
        :attr:`~stockings.models.stockitem.StockItem._currency`.

        The **setter** applies the ``new_currency`` to all related instances of
        :class:`stockings.models.stockitemprice.StockItemPrice` and then updates
        :attr:`~stockings.models.stockitem.StockItem._currency`.
        """
        return self._currency

    @currency.setter
    def currency(self, new_currency):
        """Setter for `currency`."""
        for item in self.stockitemprice_set.iterator():
            item._apply_new_currency(new_currency)
            item.save()

        self._currency = new_currency
        self.save()

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

    @property
    def latest_price(self):
        """TODO."""
        return self.__cached_latest_price

    @latest_price.setter
    def latest_price(self, new_value):

        retval = self.prices(manager="stockings_manager").set_latest_price(
            self, new_value
        )

        if retval:
            try:
                logger.debug("'latest_price' was updated, invalidating cached value!")
                del self.__cached_latest_price
            except AttributeError:
                # AttributeError is raised, if the cached property was not
                # accessed before it gets deleted
                pass
        else:
            logger.debug(
                "The provided value was older than the stored one. No update performed!"
            )

    @cached_property
    def __cached_latest_price(self):
        try:
            return StockingsMoney(
                self._latest_price_amount, self.currency, self._latest_price_timestamp
            )
        except AttributeError:
            logger.info(
                "Missing values while accessing attribute 'latest_price'. "
                "Performing required database queries!"
            )
            logger.debug(
                "'latest_price' is accessed while required values are not available. Most "
                "likely, the 'StockItem' was not fetched using "
                "'StockItem.stockings_manager', so that the specific annotations "
                "are missing."
            )
            latest_price_obj = self.prices(
                manager="stockings_manager"
            ).get_latest_price_object(stockitem=self)

            return StockingsMoney(
                latest_price_obj.price.amount,
                self.currency,
                latest_price_obj.price.timestamp,
            )

    def _is_active(self):
        """`getter` for :attr:`is_active`.

        Returns
        -------
        :obj:`bool`
            The :attr:`is_active` of the object.
        """
        return self.portfolioitem_set.filter(is_active=True).count() > 0

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
