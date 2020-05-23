# Django imports
from django.contrib import admin

# app imports
from stockings.models.portfolio import Portfolio, PortfolioItem
from stockings.models.stock import StockItem, StockItemPrice
from stockings.models.trade import Trade


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    pass


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    pass


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    pass


@admin.register(StockItemPrice)
class StockItemPriceAdmin(admin.ModelAdmin):
    pass


@admin.register(Trade)
class TradeAdmin(admin.ModelAdmin):
    pass
