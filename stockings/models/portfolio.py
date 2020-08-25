"""This module provides the :class:`~stockings.models.portfolio.Portfolio` model."""

# Django imports
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.settings import _read_default_currency


class PortfolioQuerySet(models.QuerySet):
    """App-specific implementation of :class:`django.db.models.QuerySet`.

    Notes
    -----
    This :class:`~django.db.models.QuerySet` implementation provides
    app-specific augmentations.

    The provided methods augment/extend the retrieved
    :class:`stockings.models.portfolioitem.PortfolioItem` instances by
    annotating them with additional information and allows specific filtering.
    """

    def default(self):
        """Return a queryset with annotations.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The annotated queryset.

        Warnings
        --------
        Currently, this method does nothing on its own, but is kept to keep the
        app's specific QuerySets consistent.
        """
        return self

    def filter_by_user(self, user):
        """Return a queryset filtered by the :attr:`Portfolio.user <stockings.models.portfolio.Portfolio.user>` attribute.

        Parameters
        ----------
        user :
            An instance of the project's user model, as specified by
            :setting:`AUTH_USER_MODEL`.

        Returns
        -------
        :class:`django.db.models.QuerySet`
            The filtered queryset.

        Notes
        -----
        Effectively, this method is used to ensure, that any user may only
        access :class:`~stockings.models.portfolio.Portfolio` objects, that
        he `owns`. This is the app's way of ensuring `row-level permissions`,
        because only owners are allowed to view (and modify) their portfolio.
        """
        return self.filter(user=user)


class PortfolioManager(models.Manager):
    """App-/model-specific implementation of :class:`django.db.models.Manager`.

    Notes
    -----
    This :class:`~django.db.models.Manager` implementation is used as an
    additional manager of :class:`~stockings.models.portfolio.Portfolio` (see
    :attr:`stockings.models.portfolio.Portfolio.stockings_manager`).

    This implementation inherits its functionality from
    :class:`django.db.models.Manager` and provides identical funtionality.
    Furthermore, it augments the retrieved objects with additional attributes,
    using the custom :class:`~django.db.models.QuerySet` implementation
    :class:`~stockings.models.portfolio.PortfolioQuerySet`.
    """

    def get_queryset(self):
        """Use the app-/model-specific :class:`~stockings.models.portfolio.PortfolioQuerySet` by default.

        Returns
        -------
        :class:`django.models.db.QuerySet`
            This queryset is provided by
            :class:`stockings.models.portfolio.PortfolioQuerySet` and
            applies its
            :meth:`~stockings.models.portfolio.PortfolioQuerySet.default`
            method. The retrieved objects will be annotated with additional
            attributes.
        """
        return PortfolioQuerySet(self.model, using=self._db).default()


class Portfolio(models.Model):
    """Represents a portolio of stocks.

    Warnings
    ----------
    The class documentation only includes code, that is actually shipped by the
    `stockings` app. Inherited attributes/methods (provided by Django's
    :class:`~django.db.models.Model`) are not documented here.
    """

    objects = models.Manager()
    """The model's default manager.

    The default manager is set to :class:`django.db.models.Manager`, which is
    the default value. In order to add the custom :attr:`stockings_manager` as
    an *additional* manager, the default manager has to be provided explicitly
    (see :djangodoc:`topics/db/managers/#default-managers`).
    """

    stockings_manager = PortfolioManager()
    """App-/model-specific manager, that provides additional functionality.

    This manager is set to
    :class:`stockings.models.portfolio.PortfolioManager`. Its
    implementation provides augmentations of `Portfolio` objects, by
    annotating them on database level. This will reduce the number of required
    database queries, if attributes of the object are accessed.

    The manager has to be used explicitly.
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

    _currency = models.CharField(default=_read_default_currency, max_length=3)
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
        for item in self.portfolioitems.iterator():
            item._apply_new_currency(new_currency)
            item.save()

        # actually update the object's attribute
        self._currency = new_currency
        self.save()

    def get_absolute_url(self):
        """Return the absolute URL for instances of this model.

        Returns
        -------
        str
            The absolute URL for instances of this model.
        """
        return reverse("portfolio-detail", args=[self.id])  # pragma: nocover
