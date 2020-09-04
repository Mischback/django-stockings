"""Minimal url configuration to run development in a tox-based environment."""

# Django imports
from django.contrib import admin
from django.urls import (
    include,
    path,
)

urlpatterns = [
    path("stockings/", include("stockings.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
]

try:
    # django-debug_toolbar is only required during development
    import debug_toolbar

    urlpatterns += [
        path("__debug__/", include(debug_toolbar.urls)),
    ]
except ModuleNotFoundError:
    # This catches the ModuleNotFoundError during testing
    # django-debug_toolbar is just a development requirement
    pass
