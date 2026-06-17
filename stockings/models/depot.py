# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""The ``Depot`` class represents one account to manage financial assets."""

# Django imports
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# app imports
from stockings.exceptions import StockingsModelException
from stockings.models.portfolio import Portfolio
from stockings.models.stock import StockItem


class DepotException(StockingsModelException):
    """Base class for all exceptions related to :class:`~stockings.models.depot.Depot`."""


class Depot(models.Model):
    """An account to manage financial assets."""

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="depots"
    )
    """Reference to the parent :class:`~stockings.models.portfolio.Portfolio`.

    Notes
    -----
    This is implemented as a :class:`~django.db.models.ForeignKey` with
    ``on_delete=CASCADE``, meaning: if the referenced ``Portfolio`` object is
    deleted, the referencing ``Depot`` object is discarded aswell.
    """

    name = models.CharField(blank=True, max_length=63)
    """The user-defined name for this ``Depot`` object."""

    class Meta:  # noqa: D106
        app_label = "stockings"
        verbose_name = _("Depot")
        verbose_name_plural = _("Depots")
        unique_together = ("portfolio", "name")

    def __str__(self):  # noqa: D105
        if self.name != "":
            return "[Depot] {}".format(self.name)
        else:
            return "[Depot] Generic {}".format(self.id)


class DepotItem(models.Model):
    """One single position inside of a :class:`~stockings.models.depot.Depot`."""

    depot = models.ForeignKey(
        Depot, on_delete=models.CASCADE, related_name="depotitems"
    )
    """Reference to the parent :class:`~stockings.models.depot.Depot`.

    Notes
    -----
    This is implemented as a :class:`~django.db.models.ForeignKey` with
    ``on_delete=CASCADE``, meaning: if the referenced ``Depot`` object is
    deleted, the referencing ``DepotItem`` object is discarded aswell.
    """

    stock_item = models.ForeignKey(StockItem, on_delete=models.PROTECT)
    """Reference to the :class:`~stockings.models.stock.StockItem` object.

    Notes
    -----
    This is implemented as a :class:`~django.db.models.ForeignKey` with
    ``on_delete=PROTECT``, meaning: as long as the ``StockItem`` is still
    referenced from any object of this class, it may not be deleted.
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        verbose_name = _("DepotItem")
        verbose_name_plural = _("DepotItems")

    def __str__(self):  # noqa: D105
        return "{}: {} ({})".format(self.depot, self.quantity, self.stock_item)

    @property
    def quantity(self):
        """Tracks *how many* shares of the :attr:`stock_item` are currently hold.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined by evaluating the associated instances of
        :class:`~stockings.models.depot.DepotItemCashflow`. As of now, there
        are no sanity checks in place, so the returned value might be below
        zero, which does not make sense semantically.
        """
        buys = (
            self.cashflows.filter(flow_type="BUY").aggregate(models.Sum("quantity"))[
                "quantity__sum"
            ]
            or 0
        )
        sells = (
            self.cashflows.filter(flow_type="SELL").aggregate(models.Sum("quantity"))[
                "quantity__sum"
            ]
            or 0
        )

        return buys - sells


class DepotItemCashflow(models.Model):
    """Used to track cashflow into or out of a :class:`~stockings.models.depot.DepotItem`."""

    FLOW_TYPES = [
        ("BUY", _("Buy")),
        ("SELL", _("Sell")),
        ("DIVIDEND", _("Dividend")),
        ("TAX", _("Tax")),
        ("FEE", _("Fee")),
    ]

    item = models.ForeignKey(
        DepotItem, on_delete=models.CASCADE, related_name="cashflows"
    )
    """Reference to the parent :class:`~stockings.models.depot.DepotItem`.

    Notes
    -----
    This is implemented as a :class:`~django.db.models.ForeignKey` with
    ``on_delete=CASCADE``, meaning: if the referenced ``DepotItem`` object is
    deleted, the referencing ``DepotItemCashflow`` object is discarded aswell.
    """

    flow_type = models.CharField(max_length=10, choices=FLOW_TYPES)
    """Provides a semantic meaning to the cashflow.

    There are different types of cashflows, and they have to be tracked in
    dedicated ways to allow for better analysis. However, while the types
    provide semantic meaning, they don't directly influence the *direction of
    the cashflow*.
    """

    timestamp = models.DateTimeField(default=timezone.now)
    """When did this flow happen?

    This is implemented as a full :class:`~django.db.models.DateTimeField`, so
    it even allows to track the exact time of a cashflow, in case there are
    multiple operations during one day.
    """

    quantity = models.DecimalField(
        decimal_places=8, max_digits=18, validators=[MinValueValidator(0.00000001)]
    )
    """Specify the quantity of the operation.

    For the ``BUY``, ``SELL`` and ``DIVIDEND`` types, this specifies the actual
    number of stocks that are the base for the cashflow, e.g. *buying 10 shares
    of foo* or *receiving dividends for 235 shares of bar*.

    ``TAX`` and ``FEE`` should be specified with a ``quantity`` of ``1`` and
    a matching :attr:``price_per_unit``

    The ``quantity`` is always positive and is not used to provide the direction
    of the cashflow (see :attr:`price_per_unit`).

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 8 decimal places. As of now, this is
    *state-of-the-art* with most brokers and crypto exchanges.
    """

    price_per_unit = models.DecimalField(decimal_places=6, max_digits=15)
    """The price per unit of this cashflow.

    This attribute also controls the direction of the cashflow: for ``BUY``,
    ``TAX`` and ``FEE`` types, ``price_per_unit`` is negative, while ``SELL``
    and ``DIVIDEND`` are positive.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 6 decimal places. This should cover enough precision
    for tracking of asset values aswell as future currency-related conversions.
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        ordering = ["-timestamp", "item", "flow_type"]
        verbose_name = _("DepotItemCashflow")
        verbose_name_plural = _("DepotItemCashflows")

    def __str__(self):  # noqa: D105
        return "[{}] {} - {} ({})".format(
            self.timestamp, self.flow_type, self.item, self.price_total
        )

    @property
    def price_total(self):  # noqa: D102
        return self.price_per_unit * self.quantity
