# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Integrates the app's models into Django's admin interface."""

# Django imports
from django.contrib import admin

# app imports
from stockings.models.depot import Depot
from stockings.models.portfolio import Portfolio


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):  # noqa: D101
    pass


@admin.register(Depot)
class DepotAdmin(admin.ModelAdmin):  # noqa: D101
    pass
