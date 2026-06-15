# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""The ``Depot`` class represents one account to manage financial assets."""

# Django imports
from django.db import models
from django.utils.translation import gettext_lazy as _

# app imports
from stockings.exceptions import StockingsModelException
from stockings.models.portfolio import Portfolio


class DepotException(StockingsModelException):
    """Base class for all exceptions related to :class:`~stockings.models.depot.Depot`."""


class Depot(models.Model):
    """An account to manage financial assets."""

    portfolio = models.ForeignKey(
        Portfolio, on_delete=models.CASCADE, related_name="depots"
    )
    """Reference to the parent :class:`~stockings.models.portfolio.Portfolio`.

    Notes
    -----
    This is implemented as a :class:`~django.db.models.ForeignKey` with
    ``on_delete=CASCADE``, meaning: if the referenced ``Portfolio`` object is
    deleted, the referencing ``Depot`` object is discarded aswell.
    """

    name = models.CharField(blank=True, max_length=63)
    """The user-defined name for this ``Depot`` object."""

    class Meta:  # noqa: D106
        app_label = "stockings"
        verbose_name = _("Depot")
        verbose_name_plural = _("Depots")
        unique_together = ("portfolio", "name")

    def __str__(self):  # noqa: D105
        if self.name != "":
            return "[Depot] {}".format(self.name)
        else:
            return "[Depot] Generic {}".format(self.id)
