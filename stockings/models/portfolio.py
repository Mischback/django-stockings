"""These classes represent a portfolio and its items."""

# Django imports
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class Portfolio(models.Model):
    """Represents a portolio of stocks."""

    # A human-readable name of the ``Portolio`` object.
    name = models.CharField(max_length=50,)

    # Reference to Django's ``User`` object.
    # In fact, the project may have substituted Django's default user object,
    # so this is as pluggable as possible.
    # Please note, that Django's ``User`` object (or its substitute) will not
    # have a backwards relation to this object.
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='+',
    )

    class Meta:
        app_label = 'stockings'
        unique_together = ['name', 'user']
        verbose_name = _('Portfolio')
        verbose_name_plural = _('Portfolios')
