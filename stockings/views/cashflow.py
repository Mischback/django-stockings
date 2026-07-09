# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Views related to the :class:`~stockings.models.cashflow.Cashflow`."""

# Python imports
import logging

# Django imports
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views import generic

# app imports
from stockings.forms.fields import DepotItemChoiceField
from stockings.models.cashflow import (
    Cashflow,
    CashflowForm,
    CashflowFromDepotForm,
    CashflowFromDepotItemForm,
)
from stockings.models.depot import Depot, DepotItem
from stockings.models.stock import StockItem, StockItemPrice
from stockings.views.mixins import RestrictToUserMixin

logger = logging.getLogger(__name__)


class CashflowCreateView(LoginRequiredMixin, RestrictToUserMixin, generic.CreateView):
    """CBV to create new instances of :class:`~stockings.models.cashflow.Cashflow`."""

    model = Cashflow
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
        :meth:`~stockings.views.depot.CashflowCreateView.form_valid`.
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
    """CBV to create a ``Cashflow`` instance from a ``Depot`` context."""

    form_class = CashflowFromDepotForm
    template_name = "stockings/cashflow_depot_create.html"

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
        """Create the new :class:`~stockings.models.cashflow.Cashflow` instance.

        This is the actual magic. This method will handle all relevant object
        creations, which can be either a new
        :class:`~stockings.models.cashflow.Cashflow` instance or a new
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
                # FIXME: The very first cashflow HAS TO BE a BUY operation
                # flow_type = form.cleaned_data.get("flow_type")
                # if flow_type != Cashflow.FLOW_TYPES.BUY[0]:
                # form.add_error(None, _("The first operation has to be BUY"))
                # return self.form_invalid(form)

                isin = new_isin.strip().upper()

                # TODO: There is no validation/verification of the provided
                #       ISIN. This is just skipped for now. In a later step,
                #       this should be included. See
                #       https://github.com/Mischback/django-stockings/issues/7
                #       for the corresponding issue.
                stock_item, stockitem_created = StockItem.objects.get_or_create(
                    isin=isin,
                    defaults={"name": isin},
                )

                if stockitem_created:
                    stock_item_price = (  # noqa: F841
                        StockItemPrice.objects.get_or_create(
                            stock_item=stock_item,
                            _value=form.cleaned_data.get("_price_per_unit"),
                        )
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

            self.object = Cashflow.objects.create(
                item=item,
                flow_type=form.cleaned_data.get("flow_type"),
                timestamp=form.cleaned_data.get("timestamp"),
                quantity=form.cleaned_data.get("quantity"),
                _price_per_unit=form.cleaned_data.get("_price_per_unit"),
                _fees=form.cleaned_data.get("_fees"),
                _taxes=form.cleaned_data.get("_taxes"),
            )

            return super().form_valid(form)

    def get_success_url(self):
        """Return to the ``DepotItem`` overview page after success."""
        depotitem_id = self.object.item.id

        return reverse_lazy(
            "stockings:depotitem-detail", kwargs={"depotitem_id": depotitem_id}
        )


class CashflowCreateFromDepotItemView(LoginRequiredMixin, generic.FormView):
    """CBV to create a ``Cashflow`` instance from a ``DepotItem`` context."""

    form_class = CashflowFromDepotItemForm
    template_name = "stockings/cashflow_depotitem_create.html"

    def get_depot_item(self):
        """Provide the currently active :class:`~stockings.models.depot.DepotItem`."""
        if not hasattr(self, "_cached_depotitem"):
            self._cached_depotitem = get_object_or_404(
                DepotItem,
                id=self.kwargs["depotitem_id"],
                depot__portfolio__owner=self.request.user,
            )

        return self._cached_depotitem

    def get_context_data(self, **kwargs):
        """Add the currently active ``DepotItem`` to the rendering context."""
        context = super().get_context_data(**kwargs)

        context["depotitem"] = self.get_depot_item()
        context["depot"] = self.get_depot_item().depot

        return context

    def form_valid(self, form):
        """Create the new :class:`~stockings.models.cashflow.Cashflow` instance."""
        depot_item = self.get_depot_item()

        self.object = Cashflow.objects.create(
            item=depot_item,
            flow_type=form.cleaned_data.get("flow_type"),
            timestamp=form.cleaned_data.get("timestamp"),
            quantity=form.cleaned_data.get("quantity"),
            _price_per_unit=form.cleaned_data.get("_price_per_unit"),
            _fees=form.cleaned_data.get("_fees"),
            _taxes=form.cleaned_data.get("_taxes"),
        )

        return super().form_valid(form)

    def get_success_url(self):
        """Return to the ``DepotItem`` overview page after success."""
        depotitem_id = self.object.item.id

        return reverse_lazy(
            "stockings:depotitem-detail", kwargs={"depotitem_id": depotitem_id}
        )
