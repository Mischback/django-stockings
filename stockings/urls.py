"""Provides app-specific URLs."""

# Django imports
from django.urls import path

# app imports
from .views import portfolio

urlpatterns = [
    path("portfolio/", portfolio.default, name="portfolio-default"),
    path("portfolio/<int:portfolio_id>/", portfolio.detail, name="portfolio-detail"),
    path("portfolio/list/", portfolio.listing, name="portfolio-list"),
]
