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
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

# app imports
from stockings.forms.fields import DepotItemChoiceField
from stockings.models.depot import (
    CashflowForm,
    CashflowFromDepotForm,
    Depot,
    DepotItem,
    DepotItemCashflow,
    DepotItemCashflowResult,
)
from stockings.models.stock import StockItem
from stockings.views.mixins import RestrictToUserMixin

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


class CashflowCreateView(LoginRequiredMixin, RestrictToUserMixin, generic.CreateView):
    """CBV to create new instances of :class:`~stockings.models.depot.DepotItemCashflow`."""

    model = DepotItemCashflow
    form_class = CashflowForm
    template_name_suffix = "_create"
    success_url = reverse_lazy("stockings:depotitem-detail")

    def get_form(self, form_class=None):
        """Limit the choices of the ``item`` field.

        Obviously, a user should only be able to add cashflows for
        :class:`~stockings.models.depot.DepotItem` instances of his own
        depot. This uses the
        :meth:`~stockings.model.depot.DepotItemManager.filter_by_user` of the
        custom ``ModelManager``.

        This only affects the rendering of the form. Hacker Bob can still
        inject another ``item`` into the request. This is handled in
        :meth:`~stockings.views.depot.DepotITemCashflowCreateView.form_valid`.
        """
        form = super().get_form(form_class)

        form.fields["item"] = DepotItemChoiceField(
            queryset=DepotItem.objects.filter_by_user(self.request.user),
            # label=_("Please select a Depot Item...")
        )

        return form

    def form_valid(self, form):
        """Ensure that the ``item`` actually belongs to the user."""
        item = form.cleaned_data.get("item")

        if item and item.depot.portfolio.owner != self.request.user:
            form.add_error("item", _("This is not part of your portfolio!"))
            return self.form_invalid(form)

        return super().form_valid(form)


class CashflowCreateFromDepotView(LoginRequiredMixin, generic.FormView):
    """CBV to create a ``DepotItemCashflow`` instance from a ``Depot`` context."""

    form_class = CashflowFromDepotForm
    template_name = "stockings/depotitemcashflow_create.html"

    def get_depot(self):
        """Provide the currently active :class:`~stockings.models.depot.Depot`."""
        if not hasattr(self, "_cached_depot"):
            self._cached_depot = get_object_or_404(
                Depot,
                id=self.kwargs["depot_id"],
                portfolio__owner=self.request.user,
            )

        return self._cached_depot

    def get_context_data(self, **kwargs):
        """Add the currently active ``Depot`` to the rendering context."""
        context = super().get_context_data(**kwargs)

        context["depot"] = self.get_depot()

        return context

    def get_form(self, form_class=None):
        """Modify the initialisation of the ``form`` instance.

        The :class:`~stockings.models.depot.CashflowFromDepotForm` provides the
        feature the add cashflows for *existing* ``DepotItem`` instances and
        create completely new ``DepotItem`` instances (and possible the required
        ``StockItem`` instance, too). In order to make this possible, the
        form's ``item`` field has to be made optional (``required=False``).
        """
        form = super().get_form(form_class)

        # TODO: Can this be put into CashflowForm? It should basically be
        #       applied to any form dealing with cashflows. In this function,
        #       the really relevant thing is to make it **not required**.
        form.fields["item"] = DepotItemChoiceField(
            queryset=DepotItem.objects.filter(depot=self.get_depot()),
            required=False,
        )

        return form

    def form_valid(self, form):
        """Create the new :class:`~stockings.models.depot.DepotItemCashflow` instance.

        This is the actual magic. This method will handle all relevant object
        creations, which can be either a new
        :class:`~stockings.models.depot.DepotItemCashflow` instance or a new
        :class:`~stockings.models.depot.DepotItem` including its first
        ``Cashflow`` or even a completely new
        :class:`~stockings.models.stock.StockItem`, ``DepotItem and the initial
        ``Cashflow``.
        """
        depot = self.get_depot()
        item = form.cleaned_data.get("item")
        new_isin = form.cleaned_data.get("new_isin")

        with transaction.atomic():
            if new_isin:
                isin = new_isin.strip().upper()

                stock_item, _ = StockItem.objects.get_or_create(
                    isin=isin,
                    defaults={"name": isin},
                )

                item, _ = DepotItem.objects.get_or_create(
                    depot=depot,
                    stock_item=stock_item,
                )

                form.cleaned_data["item"] = item

            else:
                if item.depot != depot:
                    form.add_error("item", _("This is not part of your portfolio!"))
                    return self.form_invalid(form)

            self.object = DepotItemCashflow.objects.create(
                item=item,
                flow_type=form.cleaned_data.get("flow_type"),
                timestamp=form.cleaned_data.get("timestamp"),
                quantity=form.cleaned_data.get("quantity"),
                price_per_unit=form.cleaned_data.get("price_per_unit"),
                fees=form.cleaned_data.get("fees"),
                taxes=form.cleaned_data.get("taxes"),
            )

            return super().form_valid(form)

    def get_success_url(self):
        """Return to the ``DepotItem`` overview page after success."""
        depotitem_id = self.object.item.id

        return reverse_lazy(
            "stockings:depotitem-detail", kwargs={"depotitem_id": depotitem_id}
        )
