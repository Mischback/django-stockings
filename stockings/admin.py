# Django imports
from django.contrib import admin

# app imports
from .models.stock import StockItem


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    pass
