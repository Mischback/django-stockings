# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""The administrative views for yfinance_simple."""

# Django imports
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

# external imports
import yfinance as yf

# app imports
from stockings.models import StockItem

# local imports
from .models import YFinanceMapping


@staff_member_required
def mapping_overview(request):
    """Provide an overview of all assets and their mapping.

    The view fetches all :class:`~stockings.models.stock.StockItem` instances
    and shows them, with their respective mapping to a YFinance ticker, in
    a list.
    """
    stock_items = StockItem.objects.all().select_related("yfinance_mapping")
    return render(
        request, "yfinance_simple/overview.html", {"stock_items": stock_items}
    )


@staff_member_required
def select_ticker(request, isin):
    """Make the ticker to be used selectable.

    The view uses ``yfinance`` to retrieve all available ticker for a given
    :class:`~stockings.models.stock.StockItem` instance and lets the user
    select one.
    """
    stock_item = get_object_or_404(StockItem, isin=isin)

    # get the currently selected ticker
    current_mapping = YFinanceMapping.objects.filter(stock_item=stock_item).first()
    current_ticker = current_mapping.ticker if current_mapping else None

    ticker_options = []
    error_message = None

    # fetch all available tickers from Yahoo using yfinance
    if request.method == "GET":
        try:
            search_results = yf.Search(stock_item.isin, max_results=10).quotes
            for quote in search_results:
                ticker_options.append(
                    {
                        "ticker": quote.get("symbol"),
                        "name": quote.get("longname") or quote.get("shortname"),
                        "exchange": quote.get("exchange"),
                    }
                )
        except Exception as e:
            error_message = f"Fehler bei der Kommunikation mit Yahoo Finance: {str(e)}"

    # select a ticker and store it in the database
    elif request.method == "POST":
        selected_ticker = request.POST.get("selected_ticker")
        if selected_ticker:
            YFinanceMapping.objects.update_or_create(
                stock_item=stock_item, defaults={"ticker": selected_ticker}
            )
            return redirect("yfinance_mapping_overview")

    context = {
        "stock_item": stock_item,
        "ticker_options": ticker_options,
        "current_ticker": current_ticker,
        "error": error_message,
    }
    return render(request, "yfinance_simple/select_ticker.html", context)
