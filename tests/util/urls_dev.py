"""Provides a minimum url configuration to run the development of the app in
a tox-based environment."""

# Django imports
from django.conf.urls import include, url  # noqa: F401
from django.contrib import admin

urlpatterns = [
    url(r'^admin/', admin.site.urls),
]
