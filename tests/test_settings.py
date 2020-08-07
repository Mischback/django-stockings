"""Tests for module `stockings.settings`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.settings import _read_default_currency

# app imports
from .util.testcases import StockingsTestCase


@tag("settings")
class StockingsSettingsTest(StockingsTestCase):
    """Provide tests for module `stockings.settings`.

    The actual settings are not tested here, but the utility functions.
    """

    @tag("current")
    @override_settings(STOCKINGS_DEFAULT_CURRENCY="FOO")
    def test_read_default_currency(self):
        """Return the setting as specified in the project's settings module."""
        self.assertEqual(_read_default_currency(), "FOO")
