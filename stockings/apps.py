"""Contains the application configuration, as required by Django."""

# Django imports
from django.apps import AppConfig
from django.db.models.signals import post_save  # noqa: F401


class StockingsConfig(AppConfig):
    """Application-specific configuration class, which is required by Django.

    This sub-class of Django's `AppConfig` provides application-specific information
    to be used in Django's application registry [1]_.

    This class provides required values by its attributes [2]_. App-specific configuration is
    done in its `ready()` method.

    Notes
    -------
    When adding `stockings` to your project, put the dotted path to this class into your settings'
    `INSTALLED_APPS`, e.g. `stockings.apps.StockingsConfig` [1]_.

    References
    ------------
    .. [1] https://docs.djangoproject.com/en/3.0/ref/applications/#configuring-applications
    .. [2] https://docs.djangoproject.com/en/3.0/ref/applications/#application-configuration
    """

    name = "stockings"
    verbose_name = "Stockings"

    def ready(self):
        """Connect required signal handlers.

        In `stockings`, `Trade` objects are tracked by the (logically) associated `PortfolioItem`.
        Changes in stock-related price information (`StockItemPrice`) are also tracked in the
        associated `PortfolioItem`.

        These logical connections are implemented using Django's signal feature.

        As of Django 1.8, it is considered *best-practice* to actually connect signal handlers
        in the app's `AppConfig.ready()` method [3]_, [4]_.

        See Also
        ---------
        stockings.models.portfolio.PortfolioItem.callback_trade_apply_trade
        stockings.models.portfolio.PortfolioItem.callback_stockitemprice_update_stock_value
        stockings.models.trade.Trade
        stockings.models.stock.StockItemPrice

        Notes
        ------
        Connecting the models makes use of Django's `post_save` signal [5]_ and is done using
        the explicit `connect()` method [6]_, including the use of `dispatch_uid`.

        The implementation of the `receiver` function is, unless stated otherwise, done as a
        `classmethod` in the model, that is interested in the signal. This does not follow the
        recommended best-practice of maintaining signal handlers in `app.signals.handlers`,
        but on the other hand follows the best-practice of having *fat models*. This combines
        [7]_ with [4]_ (and also note, that [4]_ was written about 4 years later!).

        References
        ------------
        .. [3] https://docs.djangoproject.com/en/1.8/topics/signals/#connecting-receiver-functions
        .. [4] https://stackoverflow.com/a/22924754
        .. [5] https://docs.djangoproject.com/en/3.0/ref/signals/#post-save
        .. [6] https://docs.djangoproject.com/en/3.0/topics/signals/#django.dispatch.Signal.connect
        .. [7] https://stackoverflow.com/a/2719664
        """
        # Connect PortfolioItem with Trade.
        # The callback applies the trade operation to the PortfolioItem by
        # updating various attributes to track cash flows and costs.
        # post_save.connect(
        #     self.get_model("PortfolioItem").callback_trade_apply_trade,
        #     sender=self.get_model("Trade"),
        #     dispatch_uid="STOCKINGS_portfolioitem_trade",
        # )

        # Connect PortfolioItem with StockItemPrice.
        # The callback updates `PortfolioItem`'s `stock_value` based on recent
        # price information.
        # post_save.connect(
        #     self.get_model("PortfolioItem").callback_stockitemprice_update_stock_value,
        #     sender=self.get_model("StockItemPrice"),
        #     dispatch_uid="STOCKINGS_portfolioitem_stock_value",
        # )
