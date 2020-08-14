"""Provides tests for module `stockings.models.portfolio`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.contrib.auth import get_user_model
from django.test import override_settings, tag  # noqa

# app imports
from stockings.models.portfolio import Portfolio

# app imports
from ..util.testcases import StockingsORMTestCase, StockingsTestCase


@tag("models", "portfolio", "unittest")
class PortfolioTest(StockingsTestCase):
    """Provide tests for `Portfolio` class."""

    def test_currency_get(self):
        """Property's getter simply returns the stored attribute."""
        # get a Portfolio object
        a = Portfolio()

        self.assertEqual(a._currency, a.currency)

    @mock.patch("stockings.models.portfolio.Portfolio.save")
    @mock.patch("stockings.models.portfolio.Portfolio.portfolioitem_set")
    def test_currency_set(self, mock_portfolioitem_set, mock_save):
        """Property's setter updates associated `PortfolioItem` objects."""
        # set up the mock
        mock_item = mock.MagicMock()
        mock_portfolioitem_set.iterator.return_value.__iter__.return_value = iter(
            [mock_item]
        )

        # get a Portfolio object
        a = Portfolio()

        a.currency = "FOO"

        mock_item._apply_new_currency.assert_called_with("FOO")
        self.assertTrue(mock_item.save.called)

        self.assertEqual(a._currency, "FOO")
        self.assertTrue(mock_save.called)

    def test_currency_del(self):
        """Property can not be deleted."""
        # get a Portfolio object
        a = Portfolio()

        with self.assertRaises(AttributeError):
            del a.currency


@tag("integrationtest", "models", "portfolio")
class PortfolioORMTest(StockingsORMTestCase):
    """Provide tests with fixture data."""

    @skip("depends on currency conversion")
    def test_currency_set(self):
        """Property's setter also updates `PortfolioItem` instances.

        As of now, `PortfolioItem._apply_new_currency()` is not implemented.
        This method will have to be updated, once applying new currencies is
        included (and will fail at this point)!
        """
        a = Portfolio.objects.get(name="PortfolioA")

        with self.assertRaises(NotImplementedError):
            a.currency = "FOO"


@tag("integrationtest", "portfolio", "portfolioqueryset", "queryset")
class PortfolioQuerySetORMTest(StockingsORMTestCase):
    """Provide tests with fixture data."""

    @tag("current")
    def test_filter_by_user(self):
        """Returned queryset returns only items belonging to the provided user."""
        user_a = get_user_model().objects.get(username="Alice")
        user_b = get_user_model().objects.get(username="Bob")
        portfolios_a = Portfolio.objects.filter(user=user_a)
        portfolios_b = Portfolio.objects.filter(user=user_b)

        self.assertEqual(
            list(portfolios_a),
            list(Portfolio.stockings_manager.get_queryset().filter_by_user(user_a)),
        )
        self.assertEqual(
            list(portfolios_b),
            list(Portfolio.stockings_manager.get_queryset().filter_by_user(user_b)),
        )
