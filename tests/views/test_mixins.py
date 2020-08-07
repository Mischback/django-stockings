"""Tests for module `stockings.views.mixins`."""

# Python imports
from unittest import mock, skip  # noqa

# Django imports
from django.http import HttpResponse
from django.test import RequestFactory, override_settings, tag  # noqa
from django.views.generic import View

# app imports
from stockings.views.mixins import StockingsPermissionRequiredMixin

# app imports
from ..util.testcases import StockingsTestCase


class EmptyResponseView(View):
    """Just a dummy CBV to test the app's mixins."""

    def get(self, request, *args, **kwargs):
        """Return an empty HTTP response."""
        return HttpResponse()


class MixinAppliedView(StockingsPermissionRequiredMixin, EmptyResponseView):
    """Combines the app's mixin with the dummy CBV."""

    # actually the tests won't trigger any exceptions, because they are only
    # verifying, that the right methods are called.
    # Found this test setup in Django's own tests of the django.contrib.auth
    # mixins.
    # May be useful for future mixin tests.
    raise_exception = True


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
        view = MixinAppliedView.as_view()
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
        view = MixinAppliedView.as_view()
        response = view(request)

        self.assertEqual(response.status_code, 200)

        # THIS is the relevant assertion!
        self.assertFalse(mock_has_permission.called)
