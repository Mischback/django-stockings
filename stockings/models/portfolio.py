"""These classes represent a portfolio and its items."""

# Django imports
from django.apps import apps
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.models.portfolioitem import PortfolioItem
from stockings.settings import STOCKINGS_DEFAULT_CURRENCY


class Portfolio(models.Model):
    """Represents a portolio of stocks.

    Warnings
    ----------
    The class documentation only includes code, that is actually shipped by the
    `stockings` app. Inherited attributes/methods (provided by Django's
    :class:`~django.db.models.Model`) are not documented here.
    """

    # A human-readable name of the ``Portolio`` object.
    name = models.CharField(max_length=50,)
    """The name of this `Portfolio` instance (:py:obj:`str`).

    Notes
    -----
    The attribute is implemented as :class:`~django.db.models.CharField`.

    The name **must be** unique for the associated :attr:`user`.
    """

    # Reference to Django's ``User`` object.
    # In fact, the project may have substituted Django's default user object,
    # so this is as pluggable as possible.
    # Please note, that Django's ``User`` object (or its substitute) will not
    # have a backwards relation to this object.
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
        unique_together = ["name", "user"]
        verbose_name = _("Portfolio")
        verbose_name_plural = _("Portfolios")

    def __str__(self):  # noqa: D105
        return "{} ({})".format(self.name, self.user)  # pragma: nocover

    def _get_currency(self):
        """`getter` for :attr:`currency`.

        Returns
        -------
        :obj:`str`
            The :attr:`currency` of the object.
        """
        return self._currency

    def _set_currency(self, new_currency):
        """`setter` for :attr:`currency`.

        Set the currency for all associated instances of
        :class:`~stockings.models.portfolio.PortfolioItem` and
        :class:`~stockings.models.trade.Trade`.

        Parameters
        ----------
        new_currency : :obj:`str`
            The new currency to be applied.
        """
        # Fetch all `PortfolioItem` objects, that are referencing this object
        # FIXME: This should not be necessary, because Django provides an automatic backwards relation!
        portfolio_item_set = PortfolioItem.objects.filter(portfolio=self)

        # Update all relevant `PortfolioItem` objects.
        for item in portfolio_item_set.iterator():
            item._apply_new_currency(new_currency)
            item.save()

        # Fetch all `Trade` objects, that are referencing this object
        # FIXME: This should not be necessary, because Django provides an automatic backwards relation!
        trade_set = apps.get_model("stockings.Trade").objects.filter(portfolio=self)

        # Update all relevant `Trade` objects.
        for item in trade_set.iterator():
            item._apply_new_currency(new_currency)
            item.save()

        # actually update the object's attribute
        self._currency = new_currency

    currency = property(_get_currency, _set_currency)
    """The currency for all money-related attributes (:obj:`str`).

    The value of `currency` is also used for logically related objects,
    including instances of :class:`~stockings.models.portfolio.PortfolioItem`
    and :class:`~stockings.models.trade.Trade`.

    Notes
    -------
    This attribute is implemented as a `property`. You may refer to
    :meth:`_get_currency` and :meth:`_set_currency`
    for implementation details.

    **get**

    Accessing the attribute returns a :obj:`str` with the current currency.

    **set**

    Setting this attribute will update all related instances of
    :class:`~stockings.models.portfolio.PortfolioItem` and
    :class:`~stockings.models.trade.Trade` by calling their
    :meth:`PortfolioItem._apply_new_currency <~stockings.models.portfolio.PortfolioItem._apply_new_currency>`
    and
    :meth:`Trade._apply_new_currency <~stockings.models.trade.Trade._apply_new_currency>` methods.

    Finally, this object's :attr:`_currency` is updated.

    **del**

    This is not implemented, thus an :exc:`AttributeError` will be raised.
    """
