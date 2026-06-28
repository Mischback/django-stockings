# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Provide the main functionality of this app: fetching price information."""

# Python imports
import logging
from datetime import datetime

# Django imports
from django.db.models.functions import TruncDate
from django.utils import timezone

# external imports
import pandas as pd
import yfinance as yf

# app imports
from stockings.models import StockItemPrice

# local imports
from .exceptions import YFinanceSimpleServiceException
from .models import YFinanceMapping

# get a module-level logger
logger = logging.getLogger(__name__)


def fetch_prices(period="5d"):
    """Fetch price information from Yahoo Finance in a bulk operation.

    The function relies on the ``yfinance`` library and will try to fetch
    all required price informations in one operation.

    It does not directly work on the instances of
    :class:`~stockings.models.stock.StockItem`, but only on those that have an
    active mapping with a matching
    :class:`~stockings.contrib.provider.yfinance_simple.models.YFinanceMapping`
    instance. Make sure there is a mapping for each ``StockItem`` present!
    """
    # prepare data for the request
    mappings = YFinanceMapping.objects.all()
    if not mappings.exists():
        logger.warning("No active mappings. Aborting.")
        raise YFinanceSimpleServiceException("No active mappings")

    ticker_to_isin = {m.ticker: m.stock_item_id for m in mappings}
    ticker_list = list(ticker_to_isin.keys())

    logger.info("Starting batch request to Yahoo Finance")

    # perform the actual request
    # group_by='ticker' ist essenziell für die Strukturierung
    try:
        df_all = yf.download(
            tickers=ticker_list,
            period=period,
            interval="1d",
            group_by="ticker",
            progress=False,
        )
    except Exception as e:
        logger.exception("API request failed!")
        raise YFinanceSimpleServiceException("Batch request failed") from e

    logger.info("Batch request completed")

    if df_all.empty:
        logger.warning("No data received (ticker invalid or offline)")
        return {"imported": 0, "failed": ticker_list}

    # 3. Datenbank-Preload: Existierende Kurse kompakt abfragen (Vermeidet Duplikate)
    existing_records = set(
        StockItemPrice.objects.filter(stock_item_id__in=ticker_to_isin.values())
        .annotate(date_only=TruncDate("_timestamp"))
        .values_list("stock_item_id", "date_only")
    )

    prices_to_create = []
    failed_tickers = []

    # The function is able to work on a single ticker or multiple of them at a
    # time. However, the returned result is structured differently, so the
    # parsing logic has to be changed.
    # This variable is the required indicator
    is_multi_index = isinstance(df_all.columns, pd.MultiIndex)

    for ticker in ticker_list:
        isin = ticker_to_isin.get(ticker)

        try:
            # Operating on a result of multiple tickers, so we have to find the
            # right one for the update/insert operation
            if is_multi_index:
                # Find the ticker in all results. If it is not present (for
                # whatever reason), continue operation
                if ticker not in df_all.columns.levels[0]:
                    failed_tickers.append(ticker)
                    logger.error("Failed to get result for '{}'".format(ticker))
                    continue
                df_ticker = df_all[ticker]
            # Operating on a single ticker, so ``df_all`` is already a single
            # ticker
            else:
                df_ticker = df_all

            if df_ticker.empty or "Close" not in df_ticker.columns:
                failed_tickers.append(ticker)
                logger.error("No price information in result for '{}'".format(ticker))
                continue

            # Zeilenweise Auswertung der Tage
            for index, row in df_ticker.iterrows():
                price_date = index.date()

                if (isin, price_date) in existing_records:
                    logger.debug(
                        "Price information for ticker '{}' for '{}' already present. Skipping.".format(
                            ticker, price_date
                        )
                    )
                    continue

                close_price = row.get("Close")

                # There might be various reasons for an invalid close price,
                # including weekends, vacations, delisting of the stock, ...
                # Let's keep a log, but otherwise just skip it
                if close_price is None or pd.isna(close_price):
                    logger.debug("Could not determine Close price")
                    continue

                # Create an actual full timestamp from the ``price_date``. As
                # for the ``time`` component of that timestamp, statically
                # replace it with 18:00, that should be the close of trading on
                # most stock exchanges.
                # TODO: This might be better configurable!
                naive_datetime = datetime.combine(
                    price_date, datetime.min.time().replace(hour=18)
                )
                localized_timestamp = timezone.make_aware(naive_datetime)

                prices_to_create.append(
                    StockItemPrice(
                        stock_item_id=isin,
                        _value=close_price,
                        _timestamp=localized_timestamp,
                    )
                )

        except Exception:
            failed_tickers.append(ticker)
            logger.exception(
                "Unexpected error while processing ticker '{}'".format(ticker)
            )
            logger.warn("Trying to resume normal operation")
            continue

    imported_count = len(prices_to_create)
    if prices_to_create:
        StockItemPrice.objects.bulk_create(prices_to_create)
        logger.info(
            "Success. Created {} new price information objects".format(imported_count)
        )
    else:
        logger.info("Success. No new price information created")

    return {"imported": imported_count, "failed": failed_tickers}
