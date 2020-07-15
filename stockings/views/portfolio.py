"""Provides views for the :class:`stockings.models.portfolio.Portfolio` model."""

# Django imports
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect

# app imports
from stockings.models.portfolio import Portfolio


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


@login_required
def listing(request):
    """List all available Portfolio instances of a given user."""
    raise NotImplementedError("List all Portfolio instances.")
