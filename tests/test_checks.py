"""Tests for module `stockings.checks`."""

# Python imports
from unittest import (  # noqa
    mock,
    skip,
)

# Django imports
from django.conf import settings
from django.core.checks import Error
from django.test import (  # noqa
    override_settings,
    tag,
)

# app imports
from stockings.checks import (  # noqa: F401
    check_to_percent_precision_is_int,
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
        """This is the valid combination."""
        self.assertEqual(
            check_use_django_auth_permissions_requires_django_contrib_auth(None), []
        )

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=True, INSTALLED_APPS=[])
    def test_e002_requirement_not_satisfied(self):
        """Correctly raise the corresponding error."""
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
        """Deactivated permissions check does not require 'django.contrib.auth'."""
        self.assertEqual(
            check_use_django_auth_permissions_requires_django_contrib_auth(None), []
        )

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=False, INSTALLED_APPS=[])
    def test_e002_deactivated_not_satisfied(self):
        """Deactivated permissions check does not require 'django.contrib.auth'."""
        self.assertEqual(
            check_use_django_auth_permissions_requires_django_contrib_auth(None), []
        )

    @override_settings(STOCKINGS_TO_PERCENT_PRECISION=5)
    def test_e003_valid_int(self):
        """A valid integer >= 0."""
        self.assertEqual(check_to_percent_precision_is_int(None), [])

    @override_settings(STOCKINGS_TO_PERCENT_PRECISION=0)
    def test_e003_valid_int_zero(self):
        """A valid integer == 0."""
        self.assertEqual(check_to_percent_precision_is_int(None), [])

    @override_settings(STOCKINGS_TO_PERCENT_PRECISION=1.337)
    def test_e003_invalid_float(self):
        """A float is not allowed."""
        self.assertEqual(
            check_to_percent_precision_is_int(None),
            [
                Error(
                    "STOCKINGS_TO_PERCENT_PRECISION has to be a positive integer value!",
                    hint="STOCKINGS_TO_PERCENT_PRECISION has to be a positive "
                    "integer value (actually, zero is ok aswell).",
                    id="stockings.e003",
                )
            ],
        )

    @override_settings(STOCKINGS_TO_PERCENT_PRECISION=False)
    def test_e003_invalid_bool(self):
        """A bool is not allowed."""
        self.assertEqual(
            check_to_percent_precision_is_int(None),
            [
                Error(
                    "STOCKINGS_TO_PERCENT_PRECISION has to be a positive integer value!",
                    hint="STOCKINGS_TO_PERCENT_PRECISION has to be a positive "
                    "integer value (actually, zero is ok aswell).",
                    id="stockings.e003",
                )
            ],
        )

    @override_settings(STOCKINGS_TO_PERCENT_PRECISION=-1)
    def test_e003_invalid_int_negative(self):
        """A negative integer is not allowed."""
        self.assertEqual(
            check_to_percent_precision_is_int(None),
            [
                Error(
                    "STOCKINGS_TO_PERCENT_PRECISION has to be a positive integer value!",
                    hint="STOCKINGS_TO_PERCENT_PRECISION has to be a positive "
                    "integer value (actually, zero is ok aswell).",
                    id="stockings.e003",
                )
            ],
        )

    @override_settings(STOCKINGS_TO_PERCENT_PRECISION=None)
    def test_e003_invalid_none(self):
        """None is not allowed."""
        self.assertEqual(
            check_to_percent_precision_is_int(None),
            [
                Error(
                    "STOCKINGS_TO_PERCENT_PRECISION has to be a positive integer value!",
                    hint="STOCKINGS_TO_PERCENT_PRECISION has to be a positive "
                    "integer value (actually, zero is ok aswell).",
                    id="stockings.e003",
                )
            ],
        )
