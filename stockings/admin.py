"""Integrates the app's models into Django's admin interface."""

# Django imports
from django.contrib import admin

# app imports
from stockings.models.portfolio import Portfolio
from stockings.models.portfolioitem import PortfolioItem
from stockings.models.stock import StockItem, StockItemPrice
from stockings.models.trade import Trade


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):  # noqa: D101
    pass


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):  # noqa: D101
    pass


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):  # noqa: D101
    pass


@admin.register(StockItemPrice)
class StockItemPriceAdmin(admin.ModelAdmin):  # noqa: D101
    pass


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):  # noqa: D101
    pass
