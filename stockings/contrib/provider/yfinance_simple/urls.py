# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""URLs for yfinance_simple.

This has to be added to the project's URL configuration, just like for every
other app.
"""

# Django imports
from django.urls import path

# local imports
from . import views

urlpatterns = [
    path("mapping/", views.mapping_overview, name="yfinance_mapping_overview"),
    path(
        "mapping/<str:isin>/select/", views.select_ticker, name="yfinance_select_ticker"
    ),
]
