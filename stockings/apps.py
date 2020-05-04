# Django imports
from django.apps import AppConfig
from django.db.models.signals import post_save


class StockingsConfig(AppConfig):
    """App-specific configuration class."""

    name = 'stockings'
    verbose_name = 'Stockings'

    def ready(self):
        """Executed when application loading is completed."""

        post_save.connect(
            self.get_model('PortfolioItem').callback_perform_trade,
            sender=self.get_model('Trade'),
            dispatch_uid='STOCKINGS_portfolioitem_trade',
        )

        # Connect PortfolioItem with StockItem.
        # The callback updates `PortfolioItem`'s `stock_value` based on recent
        # price information.
        post_save.connect(
            self.get_model('PortfolioItem').callback_stockitem_update_stock_value,
            sender=self.get_model('StockItem'),
            dispatch_uid='STOCKINGS_portfolioitem_stock_value',
        )
