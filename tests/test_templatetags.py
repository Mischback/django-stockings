"""Tests for package `stockings.templatetags`."""

# Python imports
import sys
from unittest import (  # noqa
    mock,
    skip,
)

# Django imports
from django.template import (
    Context,
    Template,
)
from django.test import (  # noqa
    override_settings,
    tag,
)

# app imports
from stockings.exceptions import StockingsTemplateError
from stockings.templatetags.stockings_extra import (
    _internal_fallback_format_currency,
    _internal_fallback_format_percent,
    list_portfolioitems_as_table,
    money,
    money_locale,
    to_percent,
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

    def test_internal_fallback_format_percent(self):
        """The format string is correctly applied."""
        self.assertEqual("13.37", _internal_fallback_format_percent(0.13373))

    @mock.patch("stockings.templatetags.stockings_extra.render_portfolioitems_as_table")
    @mock.patch("stockings.templatetags.stockings_extra.make_template_fragment_key")
    @mock.patch("stockings.templatetags.stockings_extra.get_template_fragment")
    def test_list_portfolioitems_as_table(
        self,
        mock_get_template_fragment,
        mock_make_template_fragment_key,
        mock_render_func,
    ):
        """Verify normal operation."""
        mock_portfolio = mock.MagicMock()

        self.assertEqual(
            mock_get_template_fragment.return_value,
            list_portfolioitems_as_table(
                {"portfolio": mock_portfolio}, "portfolioitems"
            ),
        )

        mock_get_template_fragment.assert_called_with(
            mock_make_template_fragment_key.return_value,
            True,
            mock_render_func,
            *("portfolioitems", "active")
        )

    @mock.patch("stockings.templatetags.stockings_extra.make_template_fragment_key")
    @mock.patch("stockings.templatetags.stockings_extra.get_template_fragment")
    def test_list_portfolioitems_as_table_missing_context(
        self, mock_get_template_fragment, mock_make_template_fragment_key
    ):
        """Missing `portfolio` will raise `StockingsTemplateError`."""
        with self.assertRaises(StockingsTemplateError):
            self.assertEqual(
                mock_get_template_fragment.return_value,
                list_portfolioitems_as_table({}, "portfolioitems"),
            )

    def test_money_simple(self):
        """The parameter is provided as context.

        This test does not actually do something relevant, because it only
        directly targets the templatetags code. The real magic however is
        happening in the background by Django, meaning the rendering and
        inclusion of the template.
        """
        self.assertEqual(money("foo"), {"money": "foo"})

    def test_money_full(self):
        """The tag includes the template and renders it using the provided context."""
        mock_template = Template("{% load stockings_extra %} {% money foo %}")

        with self.assertTemplateUsed("stockings/money_instance.html"):
            mock_template.render(Context({"foo": mock.MagicMock()}))

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

    @mock.patch("stockings.i18n.get_current_locale")
    @mock.patch("babel.numbers.format_percent")
    def test_to_percent_with_babel(self, mock_format_percent, mock_get_current_locale):
        """Formatting relies on Babel's `format_percent()`."""
        mock_value = 0.13373

        self.assertEqual(mock_format_percent.return_value, to_percent(mock_value))

        mock_format_percent.assert_called_with(
            round(mock_value, 4),
            locale=mock_get_current_locale.return_value,
            decimal_quantization=False,
        )

    @mock.patch.dict(sys.modules, {"babel.numbers": None})
    @mock.patch(
        "stockings.templatetags.stockings_extra._internal_fallback_format_percent"
    )
    def test_to_percent_without_babel(self, mock_format_percent):
        """Formatting is done with the internal fallback function."""
        mock_value = 0.13373

        self.assertEqual(mock_format_percent.return_value, to_percent(mock_value))
        mock_format_percent.assert_called_with(mock_value)
