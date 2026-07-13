# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Views related to the user's depot."""

# Python imports
import logging
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

# Django imports
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

# app imports
from stockings.models.depot import (
    DepotItem,
    DepotItemCashflowResult,
)
from stockings.services.data import StockingsMoney
from stockings.services.roi import mwrr, simple_roi
from stockings.views.mixins import RestrictToUserMixin

# get a module-level logger
logger = logging.getLogger(__name__)


@dataclass
class HistoricalValuePoint:
    """A single datapoint for the timeline of market values."""

    timestamp: datetime
    quantity: Decimal
    avg_buy_price: StockingsMoney
    price_per_unit: StockingsMoney
    mwrr: float

    @property
    def market_value(self):
        """The current market value.

        Market value is the product of the
        :attr:`~stockings.views.depot.HistoricalValuePoint.quantity` and
        :attr:`~stockings.views.depot.HistoricalValuePoint.price_per_unit`.
        """
        return self.price_per_unit.multiply(self.quantity)

    @property
    def current_investment(self):
        """The currently invested money.

        Investment is the product of the
        :attr:`~stockings.views.depot.HistoricalValuePoint.quantity` and
        :attr:`~stockings.views.depot.HistoricalValuePoint.avg_buy_price`.
        """
        return self.avg_buy_price.multiply(self.quantity)

    @property
    def simple_roi(self):
        """Provide a simpe return on invest.

        This is basically only the quotient of the active investment and the
        current value.
        """
        return simple_roi(self.market_value, self.current_investment)


class DepotItemDetailView(
    LoginRequiredMixin, RestrictToUserMixin, generic.detail.DetailView
):
    """Provide the details of one single position in the depot."""

    model = DepotItem

    pk_url_kwarg = "depotitem_id"

    context_object_name = "depotitem"

    template_name_suffix = "_detail"

    def get_context_data(self, **kwargs):
        """Add additional things to be displayed in this view.

        As of now, this adds the historical values for the market value of the
        :model:`~stockings.models.depot.DepotItem` depending on the tracked
        market prices (per share), provided by
        :model:`~stockings.models.stock.StockItemPrice`. The implementation
        relies on
        :meth:`~stockings.models.depot.DepotItem.evaluate_cashflow_sequence`.
        """
        context = super().get_context_data(**kwargs)

        depot_item = context["depotitem"]

        prices = depot_item.stock_item.prices.order_by("_timestamp")
        all_cashflows = list(depot_item.cashflows.order_by("timestamp"))

        initial_money = StockingsMoney(Decimal("0.000000"), all_cashflows[0].currency)
        tracker = DepotItemCashflowResult(
            Decimal("0.00000000"),
            initial_money,
            initial_money,
            initial_money,
            initial_money,
            initial_money,
            initial_money,
            initial_money,
        )

        timeline = []

        cashflow_index = 0
        cashflow_length = len(all_cashflows)

        for price in prices:
            current_timestamp = price._timestamp

            new_cashflows = []
            while (
                cashflow_index < cashflow_length
                and all_cashflows[cashflow_index].timestamp <= current_timestamp
            ):
                new_cashflows.append(all_cashflows[cashflow_index])
                cashflow_index += 1

            if new_cashflows:
                tracker = DepotItem.evaluate_cashflow_sequence(
                    new_cashflows, initial=tracker
                )

            if tracker.quantity > 0:
                # determine the MWRR until now
                past_cashflows = all_cashflows[:cashflow_index]
                tmp_current_value = price.price.multiply(tracker.quantity)
                tmp_current_value.timestamp = price._timestamp

                mwrr_value = mwrr(past_cashflows, current_value=tmp_current_value)

                # provide the actual datapoint
                timeline.append(
                    HistoricalValuePoint(
                        price._timestamp,
                        tracker.quantity,
                        tracker.avg_buy_price,
                        price.price,
                        mwrr_value,
                    )
                )

        context["historical_values"] = timeline
        return context
