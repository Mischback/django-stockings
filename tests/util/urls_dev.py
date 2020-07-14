"""Minimal url configuration to run development in a tox-based environment."""

# Django imports
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("stockings/", include("stockings.urls")),
    path("admin/", admin.site.urls),
]
