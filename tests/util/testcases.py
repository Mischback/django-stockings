"""Provides app-specific classes for test cases."""

# Django imports
from django.apps.registry import apps
from django.db.models.signals import post_save
from django.test import TestCase


class StockingsTestCaseBase(TestCase):
    """Base class for all app-specific tests."""

    @classmethod
    def _disconnect_signal_callbacks(cls):
        """Disconnect all signal callbacks for testing."""

        post_save.disconnect(
            apps.get_model("stockings.PortfolioItem").callback_trade_apply_trade,
            sender=apps.get_model("stockings.Trade"),
            dispatch_uid="STOCKINGS_portfolioitem_trade",
        )

        post_save.disconnect(
            apps.get_model(
                "stockings.PortfolioItem"
            ).callback_stockitemprice_update_stock_value,
            sender=apps.get_model("stockings.StockItemPrice"),
            dispatch_uid="STOCKINGS_portfolioitem_stock_value",
        )

    @classmethod
    def _reconnect_signal_callbacks(cls):
        """Reconnect all signal callbacks for testing."""

        post_save.connect(
            apps.get_model("stockings.PortfolioItem").callback_trade_apply_trade,
            sender=apps.get_model("stockings.Trade"),
            dispatch_uid="STOCKINGS_portfolioitem_trade",
        )

        post_save.connect(
            apps.get_model(
                "stockings.PortfolioItem"
            ).callback_stockitemprice_update_stock_value,
            sender=apps.get_model("stockings.StockItemPrice"),
            dispatch_uid="STOCKINGS_portfolioitem_stock_value",
        )


class StockingsTestCase(StockingsTestCaseBase):
    """This class supports testing without the app's signals."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls._disconnect_signal_callbacks()

    @classmethod
    def tearDownClass(cls):
        cls._reconnect_signal_callbacks()

        super().tearDownClass()
