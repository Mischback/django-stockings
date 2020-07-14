"""Provides app-specific URLs."""

# Django imports
from django.urls import path

# app imports
from .views import portfolio

urlpatterns = [
    path("portfolio/", portfolio.default, name="portfolio-default"),
]
