# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""The ``Depot`` class represents one account to manage financial assets."""

# Python imports
from decimal import Decimal

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
        buys = self.cashflows.filter(flow_type="BUY").aggregate(models.Sum("quantity"))[
            "quantity__sum"
        ] or Decimal("0")
        sells = self.cashflows.filter(flow_type="SELL").aggregate(
            models.Sum("quantity")
        )["quantity__sum"] or Decimal("0")

        return buys - sells

    @property
    def market_value(self):
        """Provide the current value ``(number of stocks * price per stock)``."""
        return "NOT YET IMPLEMENTED!"

    @property
    def buy_price(self):
        """Provide the average price of purchases.

        This is the sum of all ``BUY`` transactions and their respective ``FEE``
        transactions.
        """
        buy_cashflows = self.cashflows.filter(flow_type="BUY")

        total_cost = Decimal("0")
        total_quantity = Decimal("0")

        for cf in buy_cashflows:
            total_cost += (cf.quantity * cf.price_per_unit) + cf.fees + cf.taxes
            total_quantity += cf.quantity

        if total_quantity > 0:
            return (total_cost, total_cost / total_quantity)

        return (total_cost, Decimal("0"))

    @property
    def total_dividends(self):
        """Provide the sum of all dividends."""
        dividend_cashflows = self.cashflows.filter(flow_type="DIVIDEND")

        result = dividend_cashflows.aggregate(
            total=models.Sum(
                (models.F("quantity") * models.F("price_per_unit"))
                - models.F("taxes")
                - models.F("fees")
            )
        )

        return result["total"] or Decimal("0")

    @property
    def total_fees(self):
        """Provide the sum of all fees."""
        return self.cashflows.aggregate(total=models.Sum("fees"))["total"] or Decimal(
            "0"
        )

    @property
    def total_taxes(self):
        """Provide the sum of all taxes."""
        return self.cashflows.aggregate(total=models.Sum("taxes"))["total"] or Decimal(
            "0"
        )


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
    dedicated ways to allow for better analysis.
    """

    timestamp = models.DateTimeField(default=timezone.now)
    """When did this flow happen?

    This is implemented as a full :class:`~django.db.models.DateTimeField`, so
    it even allows to track the exact time of a cashflow, in case there are
    multiple operations during one day.
    """

    quantity = models.DecimalField(
        decimal_places=8, max_digits=18, validators=[MinValueValidator(0.00000000)]
    )
    """Specify the quantity of the operation.

    For the ``BUY``, ``SELL`` and ``DIVIDEND`` types, this specifies the actual
    number of stocks that are the base for the cashflow, e.g. *buying 10 shares
    of foo* or *receiving dividends for 235 shares of bar*.

    ``TAX`` and ``FEE`` should be specified with a ``quantity`` of ``0``.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 8 decimal places. As of now, this is
    *state-of-the-art* with most brokers and crypto exchanges.
    """

    price_per_unit = models.DecimalField(
        decimal_places=6,
        max_digits=15,
        default=0.0,
        validators=[MinValueValidator(0.000000)],
    )
    """The price per unit of this cashflow.

    For the ``BUY`` and ``SELL`` types, this is the price at the time of the
    actual transaction. For the ``DIVIDEND`` type, it's the dividend per share.

    ``TAX`` and ``FEE`` should be specified with a ``price_per_unit`` of ``0``.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 6 decimal places. This should cover enough precision
    for tracking of asset values aswell as future currency-related conversions.
    """

    fees = models.DecimalField(
        decimal_places=6,
        max_digits=15,
        default=0.0,
        validators=[MinValueValidator(0.000000)],
    )
    """Fees related to this cashflow.

    Typically, buying and selling of shares comes with a broker-specific fee.
    This is included directly in the actual transaction.

    Please note: There is also a type ``FEE``, which is meant to track
    additional fees, that are not directly related to another transaction.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 6 decimal places. This should cover enough precision
    for tracking of asset values aswell as future currency-related conversions.
    """

    taxes = models.DecimalField(
        decimal_places=6,
        max_digits=15,
        default=0.0,
        validators=[MinValueValidator(0.000000)],
    )
    """Taxes related to this cashflow.

    Selling of shares or dividends typically have taxes applied to them. Those
    are included directly in the actual transaction.

    Please note: There is also a type ``TAX``, which is meant to track
    additional taxes, that are not directly related to another transaction.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 6 decimal places. This should cover enough precision
    for tracking of asset values aswell as future currency-related conversions.
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        ordering = ["-timestamp"]
        verbose_name = _("DepotItemCashflow")
        verbose_name_plural = _("DepotItemCashflows")

    def __str__(self):  # noqa: D105
        return "[{}] {} - {} ({})".format(
            self.timestamp, self.flow_type, self.item, self.net_cashflow
        )

    @property
    def net_cashflow(self):  # noqa: D102
        base_value = self.quantity * self.price_per_unit
        costs = self.fees + self.taxes

        if self.flow_type == "BUY":
            return -base_value - costs
        elif self.flow_type == "SELL":
            return base_value - costs
        elif self.flow_type == "DIVIDEND":
            return base_value - costs
        else:
            return -costs
