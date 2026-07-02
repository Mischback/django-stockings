# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""App-specific URL configuration."""

# Django imports
from django.urls import path

# app imports
from stockings.views import cashflow, depot

app_name = "stockings"

urlpatterns = [
    path(
        "depot/<int:depot_id>/cashflow/create/",
        cashflow.CashflowCreateFromDepotView.as_view(),
        name="cashflow-create-from-depot",
    ),
    path(
        "position/<int:depotitem_id>/",
        depot.DepotItemDetailView.as_view(),
        name="depotitem-detail",
    ),
    path(
        "position/<int:depotitem_id>/cashflow/create/",
        cashflow.CashflowCreateFromDepotItemView.as_view(),
        name="cashflow-create-from-depotitem",
    ),
    # This is the most generic version of CashflowCreateView. It might not even
    # be included/reachable in a final configuration.
    path(
        "cashflow/create/",
        cashflow.CashflowCreateView.as_view(),
        name="cashflow-create",
    ),
]
