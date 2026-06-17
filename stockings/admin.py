# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Integrates the app's models into Django's admin interface."""

# Django imports
from django.contrib import admin

# app imports
from stockings.models.depot import Depot, DepotItem
from stockings.models.portfolio import Portfolio
from stockings.models.stock import StockItem, StockItemPrice


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):  # noqa: D101
    pass


@admin.register(Depot)
class DepotAdmin(admin.ModelAdmin):  # noqa: D101
    pass


@admin.register(DepotItem)
class DepotItemAdmin(admin.ModelAdmin):  # noqa: D101
    pass


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):  # noqa: D101
    pass


@admin.register(StockItemPrice)
class StockItemPriceAdmin(admin.ModelAdmin):  # noqa: D101
    pass
