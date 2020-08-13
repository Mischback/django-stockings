"""Tests for module `stockings.views.mixins`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.core.exceptions import ImproperlyConfigured
from django.http import HttpResponse
from django.test import RequestFactory, override_settings, tag  # noqa
from django.views.generic import View

# app imports
from ..util.testcases import StockingsTestCase

from stockings.views.mixins import (  # isort:skip
    StockingsLimitToUserMixin,
    StockingsPermissionRequiredMixin,
)


class EmptyResponseView(View):
    """Just a dummy CBV to test the app's mixins."""

    def get(self, request, *args, **kwargs):
        """Return an empty HTTP response."""
        return HttpResponse()


class QuerySetView(View):
    """Just a dummy CBV to test the app's mixins with database access."""

    def get(self, request, *args, **kwargs):
        """Hit the database and return an empty HTTP response."""
        objects = self.get_queryset()  # noqa: F841

        return HttpResponse()


class LimitToUserMixinAppliedView(StockingsLimitToUserMixin, QuerySetView):
    """Combines the app's mixin with a dummy CBV."""

    model = None


class PermissionRequiredMixinAppliedView(
    StockingsPermissionRequiredMixin, EmptyResponseView
):
    """Combines the app's mixin with the dummy CBV."""

    # actually the tests won't trigger any exceptions, because they are only
    # verifying, that the right methods are called.
    # Found this test setup in Django's own tests of the django.contrib.auth
    # mixins.
    # May be useful for future mixin tests.
    raise_exception = True


@tag("views", "mixins")
class StockingsLimitToUserMixinTest(StockingsTestCase):
    """Provides the tests for `StockingsLimitToUserMixin`."""

    factory = RequestFactory()

    def test_mixin_raises_error_on_missing_model(self):
        """The attribute `model` is required."""
        request = self.factory.get("/rand")
        request.user = "foo"
        view = LimitToUserMixinAppliedView.as_view()

        with self.assertRaises(ImproperlyConfigured):
            response = view(request)  # noqa: F841

    def test_mixin_uses_stockings_manager_method(self):
        """The app-specific manager is correctly called."""
        cbv = LimitToUserMixinAppliedView
        cbv.model = mock.MagicMock()

        request = self.factory.get("/rand")
        request.user = "foo"
        view = cbv.as_view()

        response = view(request)

        self.assertEqual(response.status_code, 200)

        self.assertTrue(cbv.model.stockings_manager.filter_by_user.called)
        cbv.model.stockings_manager.filter_by_user.assert_called_with(request.user)


@tag("views", "mixins")
class StockingsPermissionRequiredMixinTest(StockingsTestCase):
    """Provides the tests for `StockingsPermissionRequiredMixin`."""

    # This utility helps to construct (valid) request objects.
    factory = RequestFactory()

    @mock.patch("stockings.views.mixins.PermissionRequiredMixin.has_permission")
    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=True)
    def test_mixin_uses_parent_implementation_to_check_permissions(
        self, mock_has_permission
    ):
        """The real permission check is done by django.contrib.auth's own mixin."""
        request = self.factory.get("/rand")
        request.user = "foo"
        view = PermissionRequiredMixinAppliedView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        # THIS is the relevant assertion!
        self.assertTrue(mock_has_permission.called)

    @override_settings(STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS=False)
    @mock.patch("stockings.views.mixins.PermissionRequiredMixin.has_permission")
    def test_mixin_returns_true_if_permissions_are_deactivated(
        self, mock_has_permission
    ):
        """Permission checks are skipped."""
        request = self.factory.get("/rand")
        request.user = "foo"
        view = PermissionRequiredMixinAppliedView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        # THIS is the relevant assertion!
        self.assertFalse(mock_has_permission.called)
