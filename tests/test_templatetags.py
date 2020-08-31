"""Tests for package `stockings.templatetags`."""

# Python imports
import sys
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
from stockings.templatetags.stockings_extra import (
    _internal_fallback_format_currency,
    money,
    money_locale,
)

# app imports
from .util.testcases import StockingsTestCase


@tag("templatetags")
class StockingsExtraTest(StockingsTestCase):
    """Provides the tests for templatetag library `stockings_extra`."""

    def test_internal_fallback_format_currency(self):
        """The format string is correctly applied."""
        self.assertEqual("EUR 13.37", _internal_fallback_format_currency(13.37, "EUR"))

        # is the amount correctly rounded?
        self.assertEqual(
            "EUR 13.37", _internal_fallback_format_currency(13.37498, "EUR")
        )

        # some more rounding
        self.assertEqual("EUR 13.37", _internal_fallback_format_currency(13.368, "EUR"))

    def test_money_simple(self):
        """The parameter is provided as context.

        This test does not actually do something relevant, because it only
        directly targets the templatetags code. The real magic however is
        happening in the background by Django, meaning the rendering and
        inclusion of the template.
        """
        self.assertEqual(money("foo"), {"money": "foo"})

    @skip("not yet implemented")
    def test_money_full(self):
        """The tag includes the template and renders it using the provided context."""
        pass

    @mock.patch("stockings.i18n.get_current_locale")
    @mock.patch("babel.numbers.format_currency")
    def test_money_locale_with_babel(
        self, mock_format_currency, mock_get_current_locale
    ):
        """Formatting relies on Babel's `format_currency()`."""
        mock_money = mock.MagicMock()

        # is Babel's `format_currency()` actually used?
        self.assertEqual(mock_format_currency.return_value, money_locale(mock_money))

        # is the function called correctly?
        mock_format_currency.assert_called_with(
            mock_money.amount,
            mock_money.currency,
            locale=mock_get_current_locale.return_value,
        )

    @mock.patch.dict(sys.modules, {"babel.numbers": None})
    @mock.patch(
        "stockings.templatetags.stockings_extra._internal_fallback_format_currency"
    )
    def test_money_locale_without_babel(self, mock_format_currency):
        """Formatting is done with the internal fallback function."""
        mock_money = mock.MagicMock()

        # the internal fallback is used
        self.assertEqual(mock_format_currency.return_value, money_locale(mock_money))
        mock_format_currency.assert_called_with(mock_money.amount, mock_money.currency)
