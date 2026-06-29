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
from django.urls import reverse_lazy
from django.views import generic

# app imports
from stockings.models.depot import (
    DepotItem,
    DepotItemCashflow,
    DepotItemCashflowForm,
    DepotItemCashflowResult,
)

# get a module-level logger
logger = logging.getLogger(__name__)


@dataclass
class HistoricalValuePoint:
    """A single datapoint for the timeline of market values."""

    timestamp: datetime
    quantity: Decimal
    avg_buy_price: Decimal
    price_per_unit: Decimal

    @property
    def market_value(self):
        """The current market value.

        Market value is the product of the
        :attr:`~stockings.views.depot.HistoricalValuePoint.quantity` and
        :attr:`~stockings.views.depot.HistoricalValuePoint.price_per_unit`.
        """
        return self.quantity * self.price_per_unit

    @property
    def current_investment(self):
        """The currently invested money.

        Investment is the product of the
        :attr:`~stockings.views.depot.HistoricalValuePoint.quantity` and
        :attr:`~stockings.views.depot.HistoricalValuePoint.avg_buy_price`.
        """
        return self.quantity * self.avg_buy_price


class DepotItemDetailView(LoginRequiredMixin, generic.detail.DetailView):
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

        tracker = DepotItemCashflowResult(
            Decimal("0.00000000"),
            Decimal("0.000000"),
            Decimal("0.000000"),
            Decimal("0.000000"),
            Decimal("0.000000"),
            Decimal("0.000000"),
            Decimal("0.000000"),
            Decimal("0.000000"),
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
                timeline.append(
                    HistoricalValuePoint(
                        price._timestamp,
                        tracker.quantity,
                        tracker.avg_buy_price,
                        price._value,
                    )
                )

        context["historical_values"] = timeline
        return context


class DepotItemCashflowCreateView(LoginRequiredMixin, generic.CreateView):
    """CBV to create new instances of :class:`~stockings.models.depot.DepotItemCashflow`."""

    model = DepotItemCashflow
    form_class = DepotItemCashflowForm
    template_name_suffix = "_create"
    success_url = reverse_lazy("stockings:depotitem-detail")
