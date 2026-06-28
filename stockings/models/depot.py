# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""The ``Depot`` class represents one account to manage financial assets."""

# Python imports
import logging
from dataclasses import dataclass
from decimal import Decimal

# Django imports
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

# app imports
from stockings.exceptions import StockingsModelException
from stockings.models.portfolio import Portfolio
from stockings.models.stock import StockItem

# get a module-level logger
logger = logging.getLogger(__name__)


class DepotException(StockingsModelException):
    """Base class for all exceptions related to :class:`~stockings.models.depot.Depot`."""


@dataclass
class DepotItemCashflowResult:
    """Datastructure to provide the results of a cashflow evaluation.

    The :meth:`~stockings.models.depot.DepotItem.evaluate_cashflow_sequence`
    iterates over a list of
    :class:`~stockings.models.depot.DepotItemCashflow` and summarizes the
    results of all transactions.
    """

    quantity: Decimal
    investment: Decimal
    avg_buy_price: Decimal
    realized_gains: Decimal
    cashflow: Decimal
    fees: Decimal
    taxes: Decimal
    dividends: Decimal


_initial_cashflow = DepotItemCashflowResult(
    Decimal("0.00000000"),
    Decimal("0.000000"),
    Decimal("0.000000"),
    Decimal("0.000000"),
    Decimal("0.000000"),
    Decimal("0.000000"),
    Decimal("0.000000"),
    Decimal("0.000000"),
)


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
        return self.__quantity

    @cached_property
    def __quantity(self):
        try:
            return self._quantity
        except AttributeError:
            logger.debug(
                "Missing value while accessing attribute 'quantity'"
                "Evaluating DepotItemCashflow ('_evaluate_cashflows()')"
            )
            self._evaluate_cashflows()

            try:
                return self._quantity
            except AttributeError:
                # logger.error()
                return Decimal("0")

    @property
    def avg_buy_price(self):
        """Provide the average buy price per share.

        Every cashflow with ``flowtype="BUY"`` changes this value.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined by evaluating the associated instances of
        :class:`~stockings.models.depot.DepotItemCashflow`. The actual
        calculation is done in
        :meth:`~stockings.models.DepotItem._evaluate_cashflows`.
        """
        return self.__avg_buy_price

    @cached_property
    def __avg_buy_price(self):
        try:
            return self._avg_buy_price
        except AttributeError:
            logger.debug(
                "Missing value while accessing attribute 'avg_buy_price'"
                "Evaluating DepotItemCashflow ('_evaluate_cashflows()')"
            )
            self._evaluate_cashflows()

            try:
                return self._avg_buy_price
            except AttributeError:
                # logger.error()
                return Decimal("0")

    @property
    def active_investment(self):
        """Provide the active investment of this position.

        *Active Investment* is meant to be the money bound by the current
        position and is calculated by the current
        :attr:`~stockings.models.depot.DepotItem.quantity` multiplied by the
        :attr:`~stockings.models.depot.DepotItem.avg_buy_price`.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined and requires evalation of the associated
        :class:`~stockings.models.depot.DepotItemCashflow` objects, which is
        handled internally.
        """
        return self.quantity * self.avg_buy_price

    @property
    def total_investment(self):
        """Provide the total investment of this position.

        This includes all buy transactions (including their fees and taxes) over
        the whole lifespan of the position, while
        :attr:`~stockings.models.depot.DepotItem.active_investment` only
        provides the currently bound money. If there never was any sell
        transaction, both values *should* be identical.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined by evaluating the associated
        :class:`~stockings.models.depot.DepotItemCashflow` objects and is the
        sum of all ``flowtype="BUY"`` instances. It does include *fees* and
        *taxes* of those buy operations, however, it **does not include** other
        fees and/or taxes.
        The actual calculation is done in
        :meth:`~stockings.models.DepotItem._evaluate_cashflows`.
        """
        return self.__total_investment

    @cached_property
    def __total_investment(self):
        try:
            return self._total_investment
        except AttributeError:
            logger.debug(
                "Missing value while accessing attribute 'total_investment'"
                "Evaluating DepotItemCashflow ('_evaluate_cashflows()')"
            )
            self._evaluate_cashflows()

            try:
                return self._total_investment
            except AttributeError:
                # logger.error()
                return Decimal("0")

    @property
    def total_cashflow(self):
        """Provide the total cashflow.

        The total cashflow is the sum over all transactions/cashflows.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined by evaluating the associated
        :class:`~stockings.models.depot.DepotItemCashflow` objects.
        The actual calculation is done in
        :meth:`~stockings.models.DepotItem._evaluate_cashflows`.
        """
        return self.__total_cashflow

    @cached_property
    def __total_cashflow(self):
        try:
            return self._total_cashflow
        except AttributeError:
            logger.debug(
                "Missing value while accessing attribute 'total_cashflow'"
                "Evaluating DepotItemCashflow ('_evaluate_cashflows()')"
            )
            self._evaluate_cashflows()

            try:
                return self._total_cashflow
            except AttributeError:
                # logger.error()
                return Decimal("0")

    @property
    def realized_gains(self):
        """Provide the sum of all realized gains.

        Realized gains happen by (partially) selling stocks.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined by evaluating the associated
        :class:`~stockings.models.depot.DepotItemCashflow` objects.
        The actual calculation is done in
        :meth:`~stockings.models.DepotItem._evaluate_cashflows`.
        """
        return self.__realized_gains

    @cached_property
    def __realized_gains(self):
        try:
            return self._realized_gains
        except AttributeError:
            logger.debug(
                "Missing value while accessing attribute 'realized_gains'"
                "Evaluating DepotItemCashflow ('_evaluate_cashflows()')"
            )
            self._evaluate_cashflows()

            try:
                return self._realized_gains
            except AttributeError:
                # logger.error()
                return Decimal("0")

    @property
    def market_value(self):
        """Provide the current value ``(number of stocks * price per stock)``."""
        return self.__market_value

    @cached_property
    def __market_value(self):
        latest_price_obj = self.stock_item.prices.first()

        if not latest_price_obj or self.quantity <= 0:
            return Decimal("0.000000")

        return self.quantity * latest_price_obj._value

    @property
    def total_value(self):
        """Provide the total value of the position.

        This is the sum of
        :attr:`~stockings.models.depot.DepotItem.total_cashflow` and
        :attr:`~stockings.models.depot.DepotItem.market_value`.
        """
        return self.total_cashflow + self.market_value

    @property
    def total_dividends(self):
        """Provide the sum of all dividends.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined by evaluating the associated
        :class:`~stockings.models.depot.DepotItemCashflow` objects.
        The actual calculation is done in
        :meth:`~stockings.models.DepotItem._evaluate_cashflows`.
        """
        return self.__total_dividends

    @cached_property
    def __total_dividends(self):
        try:
            return self._total_dividends
        except AttributeError:
            logger.debug(
                "Missing value while accessing attribute 'total_dividends'"
                "Evaluating DepotItemCashflow ('_evaluate_cashflows()')"
            )
            self._evaluate_cashflows()

            try:
                return self._total_dividends
            except AttributeError:
                # logger.error()
                return Decimal("0")

    @property
    def total_fees(self):
        """Provide the sum of all fees.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined by evaluating the associated
        :class:`~stockings.models.depot.DepotItemCashflow` objects.
        The actual calculation is done in
        :meth:`~stockings.models.DepotItem._evaluate_cashflows`.
        """
        return self.__total_fees

    @cached_property
    def __total_fees(self):
        try:
            return self._total_fees
        except AttributeError:
            logger.debug(
                "Missing value while accessing attribute 'total_fees'"
                "Evaluating DepotItemCashflow ('_evaluate_cashflows()')"
            )
            self._evaluate_cashflows()

            try:
                return self._total_fees
            except AttributeError:
                # logger.error()
                return Decimal("0")

    @property
    def total_taxes(self):
        """Provide the sum of all taxes.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined by evaluating the associated
        :class:`~stockings.models.depot.DepotItemCashflow` objects.
        The actual calculation is done in
        :meth:`~stockings.models.DepotItem._evaluate_cashflows`.
        """
        return self.__total_taxes

    @cached_property
    def __total_taxes(self):
        try:
            return self._total_taxes
        except AttributeError:
            logger.debug(
                "Missing value while accessing attribute 'total_taxes'"
                "Evaluating DepotItemCashflow ('_evaluate_cashflows()')"
            )
            self._evaluate_cashflows()

            try:
                return self._total_taxes
            except AttributeError:
                # logger.error()
                return Decimal("0")

    def _evaluate_cashflows(self):
        cashflows = self.cashflows.order_by("timestamp")

        result = self.evaluate_cashflow_sequence(cashflows)

        self._quantity = result.quantity
        self._total_investment = result.investment
        self._avg_buy_price = result.avg_buy_price
        self._realized_gains = result.realized_gains
        self._total_cashflow = result.cashflow
        self._total_fees = result.fees
        self._total_taxes = result.taxes
        self._total_dividends = result.dividends

    @staticmethod
    def evaluate_cashflow_sequence(
        cashflows,
        initial=_initial_cashflow,
    ):
        """Evaluate :class:`~¨stockings.models.depot.DepotItemCashflow` instances."""
        running_quantity = initial.quantity
        investment = initial.investment
        avg_buy_price = initial.avg_buy_price
        realized_gains = initial.realized_gains
        cashflow = initial.cashflow
        fees = initial.fees
        taxes = initial.taxes
        dividends = initial.dividends

        for flow in cashflows:

            cashflow += flow.net_cashflow
            fees -= flow.fees
            taxes -= flow.taxes

            if flow.flow_type == "BUY":
                new_quantity = running_quantity + flow.quantity
                investment += flow.net_cashflow
                if new_quantity > 0:
                    buy_costs = (running_quantity * avg_buy_price) + flow.net_cashflow
                    avg_buy_price = buy_costs / new_quantity

                running_quantity = new_quantity

            elif flow.flow_type == "SELL":
                current_buy_cost = flow.quantity * avg_buy_price
                realized_gains += flow.net_cashflow + current_buy_cost

                running_quantity -= flow.quantity

            elif flow.flow_type == "DIVIDEND":
                dividends += flow.net_cashflow

        result = DepotItemCashflowResult(
            running_quantity,
            investment,
            avg_buy_price,
            realized_gains,
            cashflow,
            fees,
            taxes,
            dividends,
        )

        return result


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
