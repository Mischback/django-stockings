"""Tests for module `stockings.cache.keygen`."""

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
from stockings.cache.keygen import portfolioitem_list as keygen_portfolioitem_list

# app imports
from ..util.testcases import StockingsTestCase


@tag("cache")
class StockingsCacheTest(StockingsTestCase):
    """Provides tests for module `stockings.cache.keygen`."""

    @mock.patch("stockings.cache.keygen.make_template_fragment_key")
    def test_keygen_portfolioitem_list(self, mock_make_fragment_key):
        """Key generation relies on Django's built-in function."""
        self.assertEqual(
            mock_make_fragment_key.return_value, keygen_portfolioitem_list("active", 1)
        )
        mock_make_fragment_key.assert_called_with(
            "portfolio.portfolioitem_list.active", [1]
        )

        mock_make_fragment_key.mock_reset()

        self.assertEqual(
            mock_make_fragment_key.return_value,
            keygen_portfolioitem_list("inactive", 1),
        )
        mock_make_fragment_key.assert_called_with(
            "portfolio.portfolioitem_list.inactive", [1]
        )
