# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""The ``Portfolio`` class is the overall wrapper in this app.

It is tied to a Django project user account.
"""

# Django imports
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# app imports
from stockings.exceptions import StockingsModelException


class PortfolioModelException(StockingsModelException):
    """Base class for all exceptions related to :class:`~stockings.models.portfolio.Portfolio`."""


class Portfolio(models.Model):
    """The overall portfolio for a given user."""

    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, verbose_name=_("Owner")
    )
    """Reference to a Django ``User``.

    Notes
    -----
    This is implemented as a :class:`~django.db.models.OneToOneField` with
    ``on_delete=CASCADE``, meaning: if the referenced ``User`` object is deleted,
    the referencing ``Portfolio`` object is discarded aswell.

    To keep this application as pluggable as possible, the referenced class is
    dependent on :setting:`AUTH_USER_MODEL`. With this implementation, the
    project may substitute the :class:`~django.contrib.auth.models.User` model
    provided by Django without breaking the internal functionality of this app
    (see :djangodoc:`Reusable Apps and AUTH_USER_MODEL <topics/auth/customizing/#reusable-apps-and-auth-user-model>`).
    """

    class Meta:  # noqa: D106
        app_label = "stockings"
        verbose_name = _("Portfolio")
        verbose_name_plural = _("Portfolios")

    def __str__(self):  # noqa: D105
        return "[Portfolio] {}".format(self.owner)
