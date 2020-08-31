"""Tests for package `stockings.templatetags`."""

# Python imports
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
from stockings.templatetags.stockings_extra import (
    _internal_fallback_format_currency,
    money,
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

    def test_money_full(self):
        """The tag includes the template and renders it using the provided context."""
        dummy_template = Template("{% load stockings_extra %}" "{% money foo %}")
        context = Context({"foo": "foo"})

        with self.assertRaises(AttributeError):
            self.assertTemplateUsed(
                dummy_template.render(context), "stockings/money_instance.html"
            )
