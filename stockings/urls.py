# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""App-specific URL configuration."""

# Django imports
from django.urls import path

# app imports
from stockings.views import depot

app_name = "stockings"

urlpatterns = [
    path(
        "position/<int:depotitem_id>/",
        depot.DepotItemDetailView.as_view(),
        name="depotitem-detail",
    ),
    path(
        "cashflow/create/",
        depot.DepotItemCashflowCreateView.as_view(),
        name="depotitemcashflow-create",
    ),
]
