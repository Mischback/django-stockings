# Django imports
from django.contrib import admin

# app imports
from stockings.models.portfolio import Portfolio, PortfolioItem
from stockings.models.stock import StockItem


@admin.register(Portfolio)
class PortfolioAdmin(admin.ModelAdmin):
    pass


@admin.register(PortfolioItem)
class PortfolioItemAdmin(admin.ModelAdmin):
    pass


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    pass
