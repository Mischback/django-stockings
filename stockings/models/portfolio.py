"""This module provides the :class:`~stockings.models.portfolio.Portfolio` model."""

# Django imports
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.settings import STOCKINGS_DEFAULT_CURRENCY


class Portfolio(models.Model):
    """Represents a portolio of stocks.

    Warnings
    ----------
    The class documentation only includes code, that is actually shipped by the
    `stockings` app. Inherited attributes/methods (provided by Django's
    :class:`~django.db.models.Model`) are not documented here.
    """

    name = models.CharField(max_length=50,)
    """The name of this `Portfolio` instance (:py:obj:`str`).

    Notes
    -----
    The attribute is implemented as :class:`~django.db.models.CharField`.

    The name **must be** unique for the associated :attr:`user`.
    """

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="+"
    )
    """Reference to a Django `User`.

    Notes
    -----
    This is implemented as a :class:`~django.db.models.ForeignKey` with
    ``on_delete=CASCADE``, meaning if the referenced
    `User` object is deleted, all referencing `Portfolio` objects are discarded
    aswell.

    The backwards relation (see
    :attr:`ForeignKey.related_name<django.db.models.ForeignKey.related_name>`)
    is disabled.

    To keep this application as pluggable as possible, the referenced class is
    dependent on :setting:`AUTH_USER_MODEL`. With this method, the project may
    substitute the :class:`~django.contrib.auth.models.User` model provided by
    Django without breaking any functionality in `stockings` (see
    :djangodoc:`Reusable Apps and AUTH_USER_MODEL <topics/auth/customizing/#reusable-apps-and-auth-user-model>`).
    """

    _currency = models.CharField(default=STOCKINGS_DEFAULT_CURRENCY, max_length=3)
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

    class Meta:  # noqa: D106
        app_label = "stockings"
        ordering = ["user", "name"]
        unique_together = ["name", "user"]
        verbose_name = _("Portfolio")
        verbose_name_plural = _("Portfolios")

    def __str__(self):  # noqa: D401
        """The string representation of the `Portfolio`.

        Returns
        -------
        str
            The returned string has the form "[portfolioname] ([username])"

        Warnings
        --------
        The returned string includes the Django user (as provided by
        :attr:`~stockings.models.portfolio.Portfolio.user`), so using this
        magic method may result in another database query.
        """
        return "{} ({})".format(self.name, self.user)  # pragma: nocover

    @property
    def currency(self):  # noqa: D401
        """The currency for all money-related attributes (:obj:`str`).

        This attribute also determines the currency for all associated instances
        of :class:`stockings.models.portfolioitem.PortfolioItem` and all
        instances of :class:`stockings.models.trade.Trade`, that are created
        for this `Portfolio`.

        Warnings
        --------
        **setting** `currency` will update all related instances of
        :class:`stockings.models.portfolioitem.PortfolioItem` and
        :class:`stockings.models.trade.Trade` and will
        automatically call this object's ``save()`` method to ensure the
        integrity of data.

        Notes
        -----
        This attribute is implemented as a :obj:`property`.

        The **getter** simply returns the
        :attr:`~stockings.models.portfolio.Portfolio._currency`.

        The **setter** applies the ``new_currency`` to all related instances of
        :class:`stockings.models.portfolioitem.PortfolioItem` and
        :class:`stockings.models.trade.Trade` and then updates
        :attr:`~stockings.models.portfolio.Portfolio._currency`.
        """
        return self._currency

    @currency.setter
    def currency(self, new_currency):
        # Update all relevant `PortfolioItem` objects.
        for item in self.portfolioitem_set.iterator():
            item._apply_new_currency(new_currency)
            item.save()

        # actually update the object's attribute
        self._currency = new_currency
        self.save()
