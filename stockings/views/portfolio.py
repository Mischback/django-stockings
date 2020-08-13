"""Provides views for the :class:`stockings.models.portfolio.Portfolio` model."""

# Django imports
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.utils.translation import ugettext_lazy as _
from django.views import generic

# app imports
from stockings.models.portfolio import Portfolio

from stockings.views.mixins import (  # isort:skip
    StockingsLimitToUserMixin,
    StockingsPermissionRequiredMixin,
)


@login_required
def default(request):  # noqa: D401
    """The default view for ``portfolio/`` urls.

    Notes
    -----
    This view checks the number of Portfolio instances of the requesting user.
    If there is exactly one (1) Portfolio, it will redirect to the detail view
    (provided by :func:`~stockings.views.portfolio.show`). In any other case, it
    will provide a list of Portfolio instances for further selection.
    """
    # check the number of Portfolio instances for this user
    if Portfolio.objects.filter(user=request.user).count() == 1:
        # if there is exactly one Portfolio, just go ahead and show it
        return redirect(
            "portfolio-detail",
            portfolio_id=Portfolio.objects.filter(user=request.user).first().id,
        )
    else:
        # create a list of Portfolio instances
        return redirect("portfolio-list")


@login_required
def detail(request, portfolio_id):
    """Show the details of one Portfolio instance."""
    raise NotImplementedError("Show a single Portfolio instance.")


class PortfolioListView(
    StockingsPermissionRequiredMixin, StockingsLimitToUserMixin, generic.ListView
):
    """Provides a list of :class:`stockings.models.portfolio.Portfolio` items.

    Notes
    -----
    This implementation makes use of Django's generic class-based view
    :class:`django.views.generic.ListView`.
    """

    model = Portfolio
    """Required attribute to control, which model will be listed."""

    permission_denied_message = _(
        "You have insufficient permissions and may not access this page."
    )
    """Optional attribute to provide a custom permission denied message.

    This will be used by
    :class:`stockings.views.mixins.StockingsPermissionRequiredMixin` if the
    user does not have sufficient permissions to access the page.

    Notes
    -----
    This message is prepared to be localized.
    """

    permission_required = "stockings.view_portfolio"
    """The required permission to access this view.

    This is not an app-specific permission, but automatically created and
    assigned by `django.contrib.auth`.
    """
