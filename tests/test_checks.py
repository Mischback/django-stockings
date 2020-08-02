"""Tests for module `stockings.data`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.conf import settings
from django.test import override_settings, tag  # noqa

# app imports
from stockings.checks import (  # noqa: F401
    check_use_django_auth_permissions,
    check_use_django_auth_permissions_requires_django_contrib_auth,
)

# app imports
from .util.testcases import StockingsTestCase


@tag("checks")
class StockingsChecksTest(StockingsTestCase):
    """Provides tests for module `stockings.checks`."""

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=True)
    def test_e001_valid_true(self):
        """Boolean ``True`` is correctly recognized."""
        self.assertEqual(check_use_django_auth_permissions(None), [])
        self.assertTrue(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS)

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=False)
    def test_e001_valid_false(self):
        """Boolean ``False`` is correctly recognized."""
        self.assertEqual(check_use_django_auth_permissions(None), [])
        self.assertFalse(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS)

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=None)
    def test_e001_none_is_false(self):
        """``None`` is treated as ``False``."""
        self.assertEqual(check_use_django_auth_permissions(None), [])
        self.assertFalse(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS)

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS="foo")
    def test_e001_string_is_true(self):
        """Non-empty string is treated as ``True``."""
        self.assertEqual(check_use_django_auth_permissions(None), [])
        self.assertTrue(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS)

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=1)
    def test_e001_number_is_true(self):
        """Non-zero number is treated as ``True``."""
        self.assertEqual(check_use_django_auth_permissions(None), [])
        self.assertTrue(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS)

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=0)
    def test_e001_zero_is_false(self):
        """Numerical zero is treated as ``False``."""
        self.assertEqual(check_use_django_auth_permissions(None), [])
        self.assertFalse(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS)
