"""Tests for package `stockings.templatetags`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.templatetags.stockings_extra import (  # noqa: isort
    _internal_fallback_format_currency,
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
