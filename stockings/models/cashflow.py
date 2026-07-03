# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""The ``Cashflow`` class represents any transaction throughout the application."""

# Python imports
import logging
from decimal import Decimal

# Django imports
from django import forms
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsModelException
from stockings.models.depot import DepotItem
from stockings.settings import _read_default_currency

logger = logging.getLogger(__name__)


class CashflowException(StockingsModelException):
    """Base class for all exceptions related to :class:`~stockings.models.cashflow.Cashflow`."""


class Cashflow(models.Model):
    """Used to track cashflow into or out of a :class:`~stockings.models.depot.DepotItem`."""

    FLOW_TYPES = [
        ("BUY", _("Buy")),
        ("SELL", _("Sell")),
        ("DIVIDEND", _("Dividend")),
        ("TAX", _("Tax")),
        ("FEE", _("Fee")),
    ]

    item = models.ForeignKey(
        DepotItem, on_delete=models.CASCADE, related_name="cashflows"
    )
    """Reference to the parent :class:`~stockings.models.depot.DepotItem`.

    Notes
    -----
    This is implemented as a :class:`~django.db.models.ForeignKey` with
    ``on_delete=CASCADE``, meaning: if the referenced ``DepotItem`` object is
    deleted, the referencing ``Cashflow`` object is discarded aswell.
    """

    flow_type = models.CharField(max_length=10, choices=FLOW_TYPES)
    """Provides a semantic meaning to the cashflow.

    There are different types of cashflows, and they have to be tracked in
    dedicated ways to allow for better analysis.
    """

    currency = models.CharField(default=_read_default_currency, max_length=3)
    """The actual database representation of :attr:`currency`.

    Notes
    -----
    This is implemented as :class:`~django.db.models.CharField` with
    ``max_length=3``. The currency is stored as its
    :wiki:`currency code as described by ISO 4217 <ISO_4217>`.

    The provided default value can be configured using
    :attr:`~stockings.settings.STOCKINGS_DEFAULT_CURRENCY` in the project's
    settings.
    """

    timestamp = models.DateTimeField(default=timezone.now)
    """When did this flow happen?

    This is implemented as a full :class:`~django.db.models.DateTimeField`, so
    it even allows to track the exact time of a cashflow, in case there are
    multiple operations during one day.
    """

    quantity = models.DecimalField(
        decimal_places=8,
        max_digits=18,
        default=Decimal("0.00000000"),
        validators=[MinValueValidator(Decimal("0.00000000"))],
    )
    """Specify the quantity of the operation.

    For the ``BUY``, ``SELL`` and ``DIVIDEND`` types, this specifies the actual
    number of stocks that are the base for the cashflow, e.g. *buying 10 shares
    of foo* or *receiving dividends for 235 shares of bar*.

    ``TAX`` and ``FEE`` should be specified with a ``quantity`` of ``0``.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 8 decimal places. As of now, this is
    *state-of-the-art* with most brokers and crypto exchanges.
    """

    _price_per_unit = models.DecimalField(
        decimal_places=6,
        max_digits=15,
        default=Decimal("0.000000"),
        validators=[MinValueValidator(Decimal("0.000000"))],
    )
    """The price per unit of this cashflow.

    For the ``BUY`` and ``SELL`` types, this is the price at the time of the
    actual transaction. For the ``DIVIDEND`` type, it's the dividend per share.

    ``TAX`` and ``FEE`` should be specified with a ``price_per_unit`` of ``0``.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 6 decimal places. This should cover enough precision
    for tracking of asset values aswell as future currency-related conversions.
    """

    _fees = models.DecimalField(
        decimal_places=6,
        max_digits=15,
        default=Decimal("0.000000"),
        validators=[MinValueValidator(Decimal("0.000000"))],
    )
    """Fees related to this cashflow.

    Typically, buying and selling of shares comes with a broker-specific fee.
    This is included directly in the actual transaction.

    Please note: There is also a type ``FEE``, which is meant to track
    additional fees, that are not directly related to another transaction.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 6 decimal places. This should cover enough precision
    for tracking of asset values aswell as future currency-related conversions.
    """

    _taxes = models.DecimalField(
        decimal_places=6,
        max_digits=15,
        default=Decimal("0.000000"),
        validators=[MinValueValidator(Decimal("0.000000"))],
    )
    """Taxes related to this cashflow.

    Selling of shares or dividends typically have taxes applied to them. Those
    are included directly in the actual transaction.

    Please note: There is also a type ``TAX``, which is meant to track
    additional taxes, that are not directly related to another transaction.

    Notes
    -----
    This attribute is implemented as :class:`~django.db.models.DecimalField`
    with a precision of 6 decimal places. This should cover enough precision
    for tracking of asset values aswell as future currency-related conversions.
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        ordering = ["-timestamp"]
        verbose_name = _("Cashflow")
        verbose_name_plural = _("Cashflows")

    def __str__(self):  # noqa: D105
        return "[{}] {} - {} ({})".format(
            self.timestamp, self.flow_type, self.item, self.net_cashflow
        )

    @property
    def net_cashflow(self):  # noqa: D102
        base_value = self.price_per_unit.multiply(self.quantity)
        costs = self.fees.add(self.taxes)

        if self.flow_type == "BUY":
            return base_value.multiply(-1).subtract(costs)
        elif self.flow_type == "SELL":
            return base_value.subtract(costs)
        elif self.flow_type == "DIVIDEND":
            return base_value.subtract(costs)
        else:
            return costs.multiply(-1)

    @property
    def price_per_unit(self):  # noqa: D102
        return StockingsMoney(self._price_per_unit, self.currency, self.timestamp)

    @property
    def fees(self):  # noqa: D102
        return StockingsMoney(self._fees, self.currency, self.timestamp)

    @property
    def taxes(self):  # noqa: D102
        return StockingsMoney(self._taxes, self.currency, self.timestamp)


class CashflowForm(forms.ModelForm):
    """The most-complete form for :class:`~stockings.models.cashflow.Cashflow`.

    This form includes all available fields.
    """

    class Meta:  # noqa: D106
        model = Cashflow

        fields = [
            "item",
            "flow_type",
            "timestamp",
            "quantity",
            "currency",
            "_price_per_unit",
            "_fees",
            "_taxes",
        ]


class CashflowFromDepotItemForm(CashflowForm):
    """Custom form to creeate :class:`~stockings.models.cashflow.Cashflow` from a depot item.

    Notes
    -----
    This class is derived from :class:`~stockings.models.depot.CashflowForm`,
    which is a default :class:`~django.forms.ModelForm`. The
    :attr:`~stockings.models.cashflow.Cashflow.item` is removed from the
    form, as it will be derived from URL parameters by the corresponding
    :class:`~stockings.views.depot.CashflowCreateFromDepotItemView`.
    """

    class Meta:  # noqa: D106
        model = Cashflow

        fields = [
            "flow_type",
            "timestamp",
            "quantity",
            "currency",
            "_price_per_unit",
            "_fees",
            "_taxes",
        ]


class CashflowFromDepotForm(CashflowForm):
    """Custom form to create :class:`~stockings.models.cashflow.Cashflow` from a depot.

    This form adds the feature to create a completely new
    :class:`~stockings.models.depot.DepotItem` instance in a given
    :class:`~stockings.models.depot.Depot`. Even cooler, if the
    :class:`~stockings.models.stock.StockItem` does not yet exist, it will be
    created automatically, too.

    Notes
    -----
    This class is derived from :class:`~stockings.models.depot.CashflowForm`,
    which is a default :class:`~django.forms.ModelForm`. The
    :meth:`~stockings.models.depot.CashflowFromDepotForm.clean` method is
    modified to handle either a selected item (default mode, adding a cashflow
    to an existing ``DepotItem``) or a (new) ISIN (extended mode, adding
    the required instances of ``DepotItem`` and possibly ``StockItem``).
    However, to make this work, the form's ``item`` field has to be modified in
    order to make it optional. This code is included in
    :meth:`~stockings.views.depot.CashflowCreateFromDepotView.get_form`.
    """

    new_isin = forms.CharField(
        max_length=12,
        required=False,
        label=_("new ISIN"),
    )

    def clean(self):  # noqa: D102
        cleaned_data = super().clean()
        item = cleaned_data.get("item")
        new_isin = cleaned_data.get("new_isin")

        if not item and not new_isin:
            raise forms.ValidationError(
                _("You have to choose either an existing item or provide a new ISIN")
            )

        return cleaned_data
