# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""These classes represent financial assets."""

# Django imports
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# app imports
from stockings.exceptions import StockingsModelException


class StockItemException(StockingsModelException):
    """Base class for all exceptions related to :class:`~stockings.models.stock.StockItem`."""


class StockItemPriceException(StockingsModelException):
    """Base class for all exceptions realted to :class:`~stockings.models.stock.StockItemPrice`."""


class StockItem(models.Model):
    """Represents a financial asset.

    Financial assets include everything that is tradeable, like stocks, ETFs
    and stuff like that.

    This class provide the means to track tradeable items in the application. It
    stores the required meta information, including a (editable)
    :attr:`full_name` and - as a unique identifier - the item's :attr:`isin`.

    However, the class does not include price information. These are provided
    in :class:`~stockings.models.stock.StockItemPrice`.

    See Also
    --------
    stockings.models.depot.DepotItem :
        This class is the relation between a given ``StockItem`` with a user's
        :class:`~stockings.models.depot.Depot`.

    Notes
    -----
    To ensure database integrity, all :class:`django.db.models.ForeignKey`
    relations **to** this class are implemented with ``on_delete=PROTECT``,
    ``StockItem`` objects may not be deleted, if they are still referenced by
    either :class:`~stockings.models.depot.DepotItem`. Otherwise, if a
    ``StockItem`` object is deleted, all of its price information objects
    (:class:`~stockings.models.stock.StockItemPrice`) are deleted aswell.
    """

    # TODO: Add a custom validator!
    isin = models.CharField(db_index=True, max_length=12, primary_key=True, unique=True)
    """The ISIN of the object.

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

    name = models.CharField(blank=True, max_length=255)
    """A short and handy name for the item.

    Notes
    -----
    The attribute is implemented as :class:`~django.db.models.CharField`.

    This has to be provided *manually* and should be *unique enough* to allow
    identification of the stock, but 'uniqueness' is not enforced in any way.

    If provided, the object's :meth:`__str__()` method will include this
    attribute in the object's representation.
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        verbose_name = _("StockItem")
        verbose_name_plural = _("StockItems")

    def __str__(self):  # noqa: D105
        if self.name != "":
            return "[StockItem] {} ({})".format(self.name, self.isin)
        else:
            return "[StockItem] {}".format(self.isin)


class StockItemPrice(models.Model):
    """Tracks the price / value of a given :class:`~stockings.models.stock.StockItem`."""

    stock_item = models.ForeignKey(
        StockItem,
        on_delete=models.CASCADE,
        related_name="prices",
        unique_for_date="_timestamp",
    )
    """Reference to a :class:`~stockings.models.stock.StockItem`.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.ForeignKey` to
    :class:`~stockings.models.stock.StockItem` with ``on_delete=CASCADE``,
    meaning that, if the ``StockItem`` object is deleted, all referencing
    ``StockItemPrice`` objects will be discardeda aswell.

    As an additional constraint, there might be only one ``StockItemPrice``
    instance for any given date per ``StockItem``.

    The name of the backward relation (``related_name``) is set to ``"prices"``.
    """

    _value = models.DecimalField(
        decimal_places=6, max_digits=15, validators=[MinValueValidator(0.000001)]
    )
    """The actual value of the :attr:`price` attribute.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 6 decimal places. This should cover enough precision
    for tracking of asset values aswell as future currency-related conversions.
    """

    _timestamp = models.DateTimeField(default=timezone.now)
    """The ``date`` part of the :attr:`price` attribute."""

    class Meta:  # noqa: D106
        app_label = "stockings"
        get_latest_by = "_timestamp"
        ordering = ["-_timestamp", "stock_item"]
        verbose_name = _("StockItemPrice")
        verbose_name_plural = _("StockItemPrices")

    def __str__(self):  # noqa: D105
        return "{} - {} {} ({})".format(
            self.stock_item, "foo", self._value, self._timestamp
        )
