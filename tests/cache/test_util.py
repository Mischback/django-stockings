"""Tests for module `stockings.cache.util`."""

# Python imports
from unittest import (  # noqa
    mock,
    skip,
)

# Django imports
from django.test import (  # noqa
    override_settings,
    tag,
)

# app imports
from stockings.cache.util import find_portfolioitem_list_caches
from stockings.models.stockitemprice import StockItemPrice

# app imports
from ..util.testcases import StockingsTestCase


@tag("cache")
class StockingsCacheTest(StockingsTestCase):
    """Provides tests for module `stockings.cache.util`."""

    @mock.patch("stockings.cache.util.Portfolio")
    @mock.patch("stockings.cache.util.keygen_portfolioitem_list")
    def test_find_portfolioitem_list_caches_by_stockitem(
        self, mock_keygen, mock_portfolio
    ):
        """Find cache keys depending on a StockItemPrice object."""
        # setup the mocks
        mock_stockitemprice = mock.MagicMock(spec=StockItemPrice)
        mock_portfolio_id = 1337
        mock_portfolio.objects.filter.return_value.values_list.return_value.distinct.return_value.iterator.return_value.__iter__.return_value = iter(  # noqa: E501
            [mock_portfolio_id]
        )

        self.assertEqual(
            [mock_keygen.return_value],
            find_portfolioitem_list_caches(mock_stockitemprice),
        )
        mock_keygen.assert_called_with("active", mock_portfolio_id)

    def test_find_portfolioitem_list_caches_incompatible_instance(self):
        """An incompatible instance leads to empty result list."""
        self.assertEqual([], find_portfolioitem_list_caches(None))
