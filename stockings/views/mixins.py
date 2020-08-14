"""Provides app-specific mixins to be used with class-based views (CBV)."""

# Django imports
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.core.exceptions import ImproperlyConfigured


class StockingsLimitToUserMixin:
    """Limits the resulting queryset to objects, that belong to the current user.

    This mixin overwrites the view's ``get_queryset()`` method and automatically
    uses the model's app-specific ``stockings_manager`` with its
    ``filter_by_user()`` method.

    The view, that uses this mixin, must provide the attribute ``model`` to
    actually make this mixin usable by any class-based view of the app.
    """

    def get_queryset(self):
        """Return a queryset that only contains objects, that belong to the current user.

        Internally, the returned queryset will use the app- and model-specific
        implementation of :class:`django.db.models.Manager` as provided by
        ``stockings_manager`` on all of the app's models. All of these managers
        rely on an app- and model-specific implementation of
        :class:`django.db.models.QuerySet` that provide a model-specific method
        ``filter_by_user()``.

        Returns
        -------
        django.db.models.QuerySet
            The actual returned QuerySet is provided by the model's app-specific
            manager ``stockings_manager``.

        Raises
        ------
        django.core.exceptions.ImproperlyConfigured
            The attribute ``model`` has to be defined on the view.
        """
        if self.model is None:
            raise ImproperlyConfigured(
                "{} is missing the `model` attribute!".format(self.__class__.__name__)
            )

        return self.model.stockings_manager.get_queryset().filter_by_user(
            self.request.user
        )


class StockingsPermissionRequiredMixin(PermissionRequiredMixin):  # noqa: D205, D400
    """An app-specific re-implementation of Django's
    :class:`~django.contrib.auth.mixins.PermissionRequiredMixin`.

    This re-implementation allows to enable or disable the permission checks,
    depending on the value of the app-specific setting
    :attr:`~stockings.settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS`.

    Like the original implementation, it is required to make this the first
    ancestor of the CBV.
    """

    def has_permission(self):
        """Determine, if the user has the required permissions.

        If :attr:`~stockings.settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS` is
        set to ``True``, this method simply calls
        :meth:`django.contrib.auth.mixins.PermissionRequiredMixin.has_permission`
        and thus checks the user's assigned permissions.

        If :attr:`~stockings.settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS` is
        ``False``, the permission check is skipped and ``True`` is returned.

        Returns
        -------
        bool
            ``True`` if the user is allowed to access the view, ``False``
            otherwise.
        """
        if settings.STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS:
            return super().has_permission()

        return True
