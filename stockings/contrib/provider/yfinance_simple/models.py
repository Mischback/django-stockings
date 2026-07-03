# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Models for the application."""

# Django imports
from django.db import models
from django.utils.translation import gettext_lazy as _


class YFinanceMapping(models.Model):
    """Provide the mapping between ``stockings`` and this application.

    ``stockings`` and its :class:`~stockings.models.stock.StockItem` uses the
    ISIN to identify stocks, ``yfinance`` uses a ticker id. This class provides
    the mapping between them.
    """

    stock_item = models.OneToOneField(
        "stockings.StockItem",
        on_delete=models.CASCADE,
        related_name="yfinance_mapping",
    )

    ticker = models.CharField(
        max_length=20,
        unique=True,
    )

    class Meta:  # noqa: D106
        verbose_name = _("YFinance Mapping")
        verbose_name_plural = _("YFinance Mappings")

    def __str__(self):  # noqa: D105
        return "{}: {}".format(self.stock_item, self.ticker)
