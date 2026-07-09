# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""The ``Depot`` class represents one account to manage financial assets."""

# Python imports
import logging
from dataclasses import dataclass
from decimal import Decimal

# Django imports
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

# app imports
from stockings.exceptions import StockingsModelException
from stockings.models.portfolio import Portfolio
from stockings.models.stock import StockItem
from stockings.services.data import StockingsMoney
from stockings.services.roi import mwrr

# get a module-level logger
logger = logging.getLogger(__name__)


class DepotException(StockingsModelException):
    """Base class for all exceptions related to :class:`~stockings.models.depot.Depot`."""


class DepotItemException(StockingsModelException):
    """Base class for all exceptions related to :class:`~stockings.models.depot.DepotItem`."""


@dataclass
class DepotItemCashflowResult:
    """Datastructure to provide the results of a cashflow evaluation.

    The :meth:`~stockings.models.depot.DepotItem.evaluate_cashflow_sequence`
    iterates over a list of
    :class:`~stockings.models.cashflow.Cashflow` and summarizes the results of
    all transactions.
    """

    quantity: Decimal
    investment: StockingsMoney
    avg_buy_price: StockingsMoney
    realized_gains: StockingsMoney
    cashflow: StockingsMoney
    fees: StockingsMoney
    taxes: StockingsMoney
    dividends: StockingsMoney


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


class DepotItemManager(models.Manager):
    """Custom manager for :class:`~stockings.models.depot.DepotItem`."""

    def filter_by_user(self, user=None):
        """Filter instances of ``DepotItem`` by the specified user."""
        if user is None:
            raise DepotItemException("No user specified!")

        return self.get_queryset().filter(depot__portfolio__owner=user)


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

    objects = DepotItemManager()
    """Apply a custom manager.

    This should not interfere with Django's default inner mechanics. The custom
    manager does not replace any default functions, it just provides additional
    methods.
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
        :class:`~stockings.models.cashflow.Cashflow`. As of now, there are no
        sanity checks in place, so the returned value might be below zero,
        which does not make sense semantically.
        """
        return self.__quantity

    @cached_property
    def __quantity(self):
        try:
            return self._quantity
        except AttributeError:
            logger.debug(
                "Missing value while accessing attribute 'quantity'"
                "Evaluating Cashflow ('_evaluate_cashflows()')"
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
        :class:`~stockings.models.cashflow.Cashflow`. The actual
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
                "Evaluating Cashflow ('_evaluate_cashflows()')"
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
        :class:`~stockings.models.cashflow.Cashflow` objects, which is
        handled internally.
        """
        return self.avg_buy_price.multiply(self.quantity)

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
        :class:`~stockings.models.cashflow.Cashflow` objects and is the
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
                "Evaluating Cashflow ('_evaluate_cashflows()')"
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
        :class:`~stockings.models.cashflow.Cashflow` objects.
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
                "Evaluating Cashflow ('_evaluate_cashflows()')"
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
        :class:`~stockings.models.cashflow.Cashflow` objects.
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
                "Evaluating Cashflow ('_evaluate_cashflows()')"
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
            # FIXME: Huh, which currency should be applied here?!
            # FIXME: This is actually a rather critical bug! If a user creates
            #        a new StockItem by ISIN from the
            #        CashflowCreateFromDepotView(), there are not yet any
            #        StockItemPrice objects and at this point, we don't know
            #        about the currency of the Cashflow, that created the
            #        StockItem.
            #        Actually, the operation in question creates 3 objects in
            #        one transaction: a Cashflow, a StockItem and a DepotItem.
            #        If we add the ``currency`` field to the CashflowForm, we
            #        can push that value to all three objects.
            return StockingsMoney(0, "XXX")

        # return self.quantity * latest_price_obj._value
        # FIXME: This is just a temporary fix! When the actual StockItem and its
        #        StockItemPrice are converted to using StockingsMoney, this can
        #        safely and effortlessly (sic!) be modified!
        return StockingsMoney(
            latest_price_obj._value, "EUR", latest_price_obj._timestamp
        ).multiply(self.quantity)

    @property
    def total_value(self):
        """Provide the total value of the position.

        This is the sum of
        :attr:`~stockings.models.depot.DepotItem.total_cashflow` and
        :attr:`~stockings.models.depot.DepotItem.market_value`.
        """
        # return self.total_cashflow + self.market_value
        return self.total_cashflow.add(self.market_value)

    @property
    def total_dividends(self):
        """Provide the sum of all dividends.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined by evaluating the associated
        :class:`~stockings.models.cashflow.Cashflow` objects.
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
                "Evaluating Cashflow ('_evaluate_cashflows()')"
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
        :class:`~stockings.models.cashflow.Cashflow` objects.
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
                "Evaluating Cashflow ('_evaluate_cashflows()')"
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
        :class:`~stockings.models.cashflow.Cashflow` objects.
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
                "Evaluating Cashflow ('_evaluate_cashflows()')"
            )
            self._evaluate_cashflows()

            try:
                return self._total_taxes
            except AttributeError:
                # logger.error()
                return Decimal("0")

    @property
    def mwrr(self):
        """Provide money-weighted rate of return.

        Notes
        -----
        This attribute is not stored in the database. Instead, it's dynamically
        determined using :func:`~stockings.services.roi.mwrr` based on all
        :class:`~stockings.models.cashflow.Cashflow` objects and the current
        :attr:`~stockings.models.depot.DepotItem.market_value`.
        """
        return mwrr(self.cashflows.order_by("timestamp"), self.market_value)

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
        initial=None,
    ):
        """Evaluate :class:`~¨stockings.models.cashflow.Cashflow` instances."""
        if initial is None:
            initial_money = StockingsMoney(Decimal("0.000000"), cashflows[0].currency)

            initial = DepotItemCashflowResult(
                Decimal("0.00000000"),
                initial_money,
                initial_money,
                initial_money,
                initial_money,
                initial_money,
                initial_money,
                initial_money,
            )

        running_quantity = initial.quantity
        investment = initial.investment
        avg_buy_price = initial.avg_buy_price
        realized_gains = initial.realized_gains
        cashflow = initial.cashflow
        fees = initial.fees
        taxes = initial.taxes
        dividends = initial.dividends

        for flow in cashflows:
            cashflow = cashflow.add(flow.net_cashflow)
            fees = fees.subtract(flow.fees)
            taxes = taxes.subtract(flow.taxes)

            if flow.flow_type == "BUY":
                new_quantity = running_quantity + flow.quantity
                investment = investment.add(flow.net_cashflow)
                if new_quantity > 0:
                    # buy_costs = (running_quantity * avg_buy_price) + flow.net_cashflow
                    buy_costs = avg_buy_price.multiply(running_quantity).add(
                        flow.net_cashflow
                    )
                    # avg_buy_price = buy_costs / new_quantity
                    avg_buy_price = buy_costs.divide(new_quantity)

                running_quantity = new_quantity

            elif flow.flow_type == "SELL":
                # current_buy_cost = flow.quantity * avg_buy_price
                current_buy_cost = avg_buy_price.multiply(flow.quantity)
                # realized_gains += flow.net_cashflow + current_buy_cost
                realized_gains = realized_gains.add(flow.net_cashflow).add(
                    current_buy_cost
                )

                running_quantity -= flow.quantity

            elif flow.flow_type == "DIVIDEND":
                dividends = dividends.add(flow.net_cashflow)

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
