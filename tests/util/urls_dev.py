"""Minimal url configuration to run development in a tox-based environment."""

# Django imports
from django.contrib import admin
from django.urls import include, path

# external imports
import debug_toolbar

urlpatterns = [
    path("stockings/", include("stockings.urls")),
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    path("__debug__/", include(debug_toolbar.urls)),
]
