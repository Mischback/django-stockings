"""Provides app-specific URLs."""

# Django imports
from django.urls import path

# app imports
from .views import portfolio

urlpatterns = [
    path("portfolio/", portfolio.default, name="portfolio-default"),
    path(
        "portfolio/<int:portfolio_id>/",
        portfolio.PortfolioDetailView.as_view(),
        name="portfolio-detail",
    ),
    path(
        "portfolio/list/", portfolio.PortfolioListView.as_view(), name="portfolio-list"
    ),
]
