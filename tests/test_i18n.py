"""Tests for module `stockings.i18n`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.test import override_settings, tag  # noqa

# app imports
from stockings.i18n import get_current_locale

# app imports
from .util.testcases import StockingsTestCase


@tag("i18n")
class StockingsI18NTest(StockingsTestCase):
    """Provides tests for module `stockings.i18n`."""

    @mock.patch("stockings.i18n.to_locale")
    @mock.patch("stockings.i18n.get_language")
    def test_get_current_locale(self, mock_get_language, mock_to_locale):
        """Returns the locale based on Django's `get_language()`."""
        self.assertEqual(get_current_locale(), mock_to_locale.return_value)
        self.assertTrue(mock_get_language.called)
        mock_to_locale.assert_called_with(mock_get_language.return_value)

    @override_settings(LANGUAGE_CODE="foo")
    @mock.patch("stockings.i18n.to_locale")
    @mock.patch("stockings.i18n.get_language")
    def test_get_current_locale_fallback_to_settings(
        self, mock_get_language, mock_to_locale
    ):
        """Returns the locale based on Django's setting `LANGUAGE_CODE`."""
        # setup the mock
        mock_get_language.return_value = None
        self.assertEqual(get_current_locale(), mock_to_locale.return_value)
        self.assertTrue(mock_get_language.called)

        # assert, that the function is called with the overridden setting
        mock_to_locale.assert_called_with("foo")
