"""Provides the `Trade` class."""

# Django imports
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import ugettext_lazy as _

# app imports
from stockings.data import StockingsMoney
from stockings.exceptions import StockingsInterfaceError
from stockings.models.portfolio import Portfolio, PortfolioItem
from stockings.models.stock import StockItem


class Trade(models.Model):
    """Represents a single trade operation, i.e. the purchase or sale of stock.

    Objects of this class are the central mean to modify the portfolio of a
    user. By performing a purchase (object with ``trade_type="BUY"``), the
    given stock (specified by ``stock_item``) is added to the portfolio, by
    updating or creating a ``PortfolioItem`` with the provided ``item_count``.

    Selling stock (object with ``trade_type="SELL"``) decreases the count of
    stock in ``PortfolioItem``, ultimately to zero.

    While performing trade operations, the ``PortfolioItem`` is updated to
    track the cash flows and stock counts.

    See Also
    ---------
    stockings.models.portfolio.PortfolioItem.callback_trade_apply_trade :
        callback to update `PortfolioItem` objects.
    stockings.models.portfolio.Portfolio :
        `Portfolio` object, that in fact provides the `currency` attribute.
    stockings.models.stock.StockItem :
        The associated object, that represents a stock.

    Warnings
    ----------
    The class documentation only includes code, that is actually shipped by the
    `stockings` app. Inherited attributes/methods (provided by Django's `Model`
    class) are not documented here.
    """

    # Define the choices for `type` field.
    # TODO: Django 3.0 introduces another way for this!
    # See: https://docs.djangoproject.com/en/3.0/ref/models/fields/#enumeration-types
    # Don't use this, if it is the only 3.0 feature to keep backwards compatibility,
    # but DO use this, if there are other 3.0 features, that *must* be used!
    TRADE_TYPES = [
        ("BUY", _("Buy")),
        ("SELL", _("Sell")),
    ]

    item_count = models.PositiveIntegerField(
        default=0, validators=[MinValueValidator(1)]
    )
    """The count of traded stock (`int`).

    The count has to be positive, because purchase/sell are distinguished by
    ``trade_type``.

    See Also
    --------
    django.db.models.PositiveIntegerField
    django.core.validators.MinValueValidator

    Notes
    -----
    This attribute is implemented as `PositiveIntegerField` with an
    `MinValueValidator(1)` attached.
    """

    portfolio = models.ForeignKey(Portfolio, on_delete=models.CASCADE)
    """Reference to a `Portfolio`.

    See Also
    --------
    stockings.models.portfolio.Portfolio
    django.db.models.ForeignKey

    Notes
    -----
    This attribute is implemented as `ForeignKey` to `Portfolio` with
    ``on_delete=CASCADE``, meaning that, if the `Portfolio` object is deleted,
    all referencing `Trade` objects will be discarded aswell.
    """

    stock_item = models.ForeignKey(
        StockItem, on_delete=models.PROTECT, related_name="+"
    )
    """Reference to a `StockItem`.

    See Also
    --------
    stockings.models.stock.StockItem
    django.db.models.ForeignKey

    Notes
    -----
    This attribute is implemented as `ForeignKey` to `StockItem` with
    ``on_delete=PROTECT``, meaning that it is not possible to delete the
    `StockItem` while it is referenced by a `Trade` object.

    The backwards relation (see [1]_) is disabled.

    References
    ----------
    .. [1] https://docs.djangoproject.com/en/3.0/ref/models/fields/#django.db.models.ForeignKey.related_name
    """

    timestamp = models.DateTimeField(default=now)
    """The point of time of the trade operation (`datetime.datetime`).

    There is only one `timestamp` per object and this is used for ``costs``
    aswell as ``price``.

    See Also
    --------
    django.db.models.DateTimeField

    Notes
    -----
    This attribute is implemented as `DateTimeField`, providing ``now()`` as
    its default value. ``now`` is provided by `django.utils.timezone`.
    """

    trade_type = models.CharField(choices=TRADE_TYPES, max_length=4)
    """Determines if this is a purchase or a sale (`str`).

    Values are limited to ``"BUY"`` and ``"SELL"``, as provided by the class'
    ``TRADE_TYPES`` (undocumented).

    See Also
    --------
    django.db.models.CharField

    Notes
    -----
    This attribute is implemented as `CharField`, limiting the accepted values
    to ``choices=TRADE_TYPE``.
    """

    # Costs for this trade, e.g. whatever the bank charges
    _costs_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)

    # Price **per item** for this trade.
    _price_amount = models.DecimalField(decimal_places=4, default=0, max_digits=19)

    class Meta:  # noqa: D106
        app_label = "stockings"
        verbose_name = _("Trade")
        verbose_name_plural = _("Trades")

    def __str__(self):  # noqa: D105
        return "[{}] {} - {} ({})".format(
            self.trade_type, self.portfolio, self.stock_item, self.timestamp
        )  # pragma: nocover

    def clean(self):
        """Provide some validation, before actually *performing* the trade.

        These validations are not strictly tied to one specific field. In
        particular, they require data from other models.

        Raises
        ------
        django.core.exceptions.ValidationError
            Raised if a sale should be performed, while the stock to be traded
            is currently not in the portfolio.

        See also
        --------
        stockings.models.portfolio.Portfolio
        stockings.models.portfolio.PortfolioItem
        django.core.exceptions.ValidationError

        Notes
        -----
        This a rather expensive validation step, because the database is hit to
        verify, that the `StockItem` to be sold is actually available in the
        user's portfolio (represented by a `PortfolioItem`).

        Because this (expensive) step is already performed, furthermore it is
        checked, that the count to be sold is not greater than the available
        count.

        Django includes several layers of validation (e.g. implemented in
        ``Form`` classes or in ``Model`` classes). This validation is provided
        on ``Model`` level, to ensure database integrity. The idea is, that
        trade operations may be re-applied, thus, this validation has to be
        performed here.
        """
        # There are some restrictions for 'SELL' trades:
        # 1. The ``stock_item`` must have a corresponding ``PortfolioItem``
        #   object in ``portfolio``.
        # 2. You are not able to sell more items than available in your
        #   portfolio.
        if self.trade_type == "SELL":
            # Get the ``PortfolioItem``...
            try:
                portfolio_item = self.portfolio.portfolioitem_set.get(
                    stock_item=self.stock_item
                )
            except PortfolioItem.DoesNotExist:
                raise ValidationError(
                    _(
                        "You are trying to sell stock, that is not present in your portfolio!"
                    ),
                    code="invalid",
                )

            # Trying to sell more items than available. Setting a maximum value
            # for this trade.
            # TODO: Add a notification of some sort... django messages?
            if self.item_count > portfolio_item.stock_count:
                self.item_count = portfolio_item.stock_count

    def _get_costs(self):
        """Return the ``costs`` as `StockingsMoney` object.

        Returns
        --------
        StockingsMoney
            An instance of `StockingsMoney`, where `amount` is `self._costs_amount`,
            `currency` is `self.currency` (meaning: `self.portfolio.currency`) and
            `timestamp` is `self.timestamp`.

        See Also
        ---------
        stockings.models.trade.Trade.costs
        stockings.data.StockingsMoney
        stockings.models.portfolio.Portfolio
        """
        return StockingsMoney(self._costs_amount, self.currency, self.timestamp)

    def _get_currency(self):
        return self.portfolio.currency

    def _get_price(self):  # noqa: D301
        """Return the ``price`` per item as `StockingsMoney` object.

        Returns
        --------
        StockingsMoney
            An instance of `StockingsMoney`, where `amount` is
            `self._price_amount`, `currency` is `self.currency` (meaning:
            `self.portfolio.currency`) and `timestamp` is `self.timestamp`.

        See Also
        ---------
        stockings.models.trade.Trade.price
        stockings.data.StockingsMoney
        stockings.models.stock.StockItem
        stockings.models.stock.StockItemPrice

        Notes
        -------
        This returns the *price* **per item**. Thus, it has similarity to
        `StockItemPrice`. The total price of the trade may be calculated like
        `total_price = costs.add(price.multiply(item_count))`.
        """
        return StockingsMoney(self._price_amount, self.currency, self.timestamp)

    def _set_costs(self, value):
        raise NotImplementedError("to be done")

    def _set_currency(self, new_currency):
        raise StockingsInterfaceError(
            "This attribute may not be set directly! "
            "The currency may only be set on `Portfolio` level."
        )

    def _set_price(self, value):
        raise NotImplementedError("to be done")

    costs = property(_get_costs, _set_costs)
    """The costs of this trade operation (`StockingsMoney`).

    In the context of this class, *costs* refer to whatever your broker is
    charging for the trade.

    Returns a `StockingsMoney` instance and accepts these objects as input.

    See Also
    --------
    stockings.data.StockingsMoney

    Notes
    -----
    This attribute is implemented as a `property`, you may refer to
    ``_get_costs`` and ``_set_costs``.

    **get**

    Accessing the attribute returns a `StockingsMoney` object.

    - ``amount`` is stored in ``_costs_amount`` as `decimal.Decimal`.
    - ``currency`` is fetched from the object's ``currency``.
    - ``timestamp`` is fetched from the object's ``timestamp``.

    **set**

    *currently not implemented (yet)*

    **del**

    This is not implemented, thus an ``AttributeError`` will be raised.
    """

    currency = property(_get_currency, _set_currency)
    """The currency for `costs` and `price` (`str`, read-only).

    See Also
    --------
    stockings.models.portfolio.Portfolio

    Notes
    -----
    This attribute is implemented as a `property`, and its value is actually
    fetched from the referenced `Portfolio` (see ``portfolio``).

    Setting this attribute is not possible and will raise
    `StockingsInterfaceError`. Deleting the attribute will raise
    `AttributeError`.
    """

    price = property(_get_price, _set_price)
    """The price per item of the traded `StockItem` (`StockingsMoney`).

    Returns a `StockingsMoney` instance and accepts these objects as input.

    See Also
    --------
    stockings.data.StockingsMoney

    Notes
    -----
    This attribute is implemented as a `property`, you may refer to
    ``_get_price`` and ``_set_price``.

    **get**

    Accessing the attribute returns a `StockingsMoney` object.

    - ``amount`` is stored in ``_price_amount`` as `decimal.Decimal`.
    - ``currency`` is fetched from the object's ``currency``.
    - ``timestamp`` is fetched from the object's ``timestamp``.

    **set**

    *currently not implemented (yet)*

    **del**

    This is not implemented, thus an ``AttributeError`` will be raised.
    """
