"""Provides app-specific mixins to be used with class-based views (CBV)."""

# Django imports
from django.contrib.auth.mixins import PermissionRequiredMixin

# app imports
from stockings.settings import STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS


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
        if STOCKINGS_USE_DJANGO_AUTH_PERMISSIONS:
            return super().has_permission()

        return True
