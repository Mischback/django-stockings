"""Tests for module `stockings.data`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.conf import settings
from django.core.checks import Error
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
    def test_e001_invalid_none(self):
        """``None`` is treated as ``False``."""
        self.assertEqual(
            check_use_django_auth_permissions(None),
            [
                Error(
                    "STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS has to be a boolean value!",
                    hint="STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS has to be either True or "
                    "False.",
                    id="stockings.e001",
                )
            ],
        )
        self.assertFalse(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS)

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS="foo")
    def test_e001_invalid_string(self):
        """Non-empty string is treated as ``True``."""
        self.assertEqual(
            check_use_django_auth_permissions(None),
            [
                Error(
                    "STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS has to be a boolean value!",
                    hint="STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS has to be either True or "
                    "False.",
                    id="stockings.e001",
                )
            ],
        )
        self.assertTrue(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS)

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=1)
    def test_e001_invalid_number(self):
        """Non-zero number is treated as ``True``."""
        self.assertEqual(
            check_use_django_auth_permissions(None),
            [
                Error(
                    "STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS has to be a boolean value!",
                    hint="STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS has to be either True or "
                    "False.",
                    id="stockings.e001",
                )
            ],
        )
        self.assertTrue(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS)

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=0)
    def test_e001_invalid_zero(self):
        """Numerical zero is treated as ``False``."""
        self.assertEqual(
            check_use_django_auth_permissions(None),
            [
                Error(
                    "STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS has to be a boolean value!",
                    hint="STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS has to be either True or "
                    "False.",
                    id="stockings.e001",
                )
            ],
        )
        self.assertFalse(settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS)

    @override_settings(
        STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=True,
        INSTALLED_APPS=["django.contrib.auth"],
    )
    def test_e002_requirement_satisfied(self):
        """This is the valid combination.

        Note: Overriding setting STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS is
        **not** working as expected. This has no effect in this test setup,
        because ``True`` is the default value.
        However, overriding INSTALLED_APPS **is** working, so this is a valid
        test case.
        """
        self.assertEqual(
            check_use_django_auth_permissions_requires_django_contrib_auth(None), []
        )

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=True, INSTALLED_APPS=[])
    def test_e002_requirement_not_satisfied(self):
        """Correctly raise the corresponding error.

        Note: Overriding setting STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS is
        **not** working as expected. This has no effect in this test setup,
        because ``True`` is the default value.
        However, overriding INSTALLED_APPS **is** working, so this is a valid
        test case.
        """
        self.assertEqual(
            check_use_django_auth_permissions_requires_django_contrib_auth(None),
            [
                Error(
                    "'django.contrib.auth' must be installed!",
                    hint="STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS is True and thus "
                    "requires 'django.contrib.auth' to be present in "
                    "INSTALLED_APPS.",
                    id="stockings.e002",
                )
            ],
        )

    @override_settings(
        STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=False,
        INSTALLED_APPS=["django.contrib.auth"],
    )
    def test_e002_deactivated_but_satisfied(self):
        """Deactivated permissions check does not require 'django.contrib.auth'.

        Note: Overriding setting STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS is
        **not** working as expected. This makes this test impossible, thus it is
        skipped.
        """
        self.assertEqual(
            check_use_django_auth_permissions_requires_django_contrib_auth(None), []
        )

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=False, INSTALLED_APPS=[])
    def test_e002_deactivated_not_satisfied(self):
        """Deactivated permissions check does not require 'django.contrib.auth'.

        Note: Overriding setting STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS is
        **not** working as expected. This makes this test impossible, thus it is
        skipped.
        """
        self.assertEqual(
            check_use_django_auth_permissions_requires_django_contrib_auth(None), []
        )
