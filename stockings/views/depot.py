# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Views related to the user's depot."""

# Django imports
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import generic

# app imports
from stockings.models.depot import DepotItem


class DepotItemDetailView(LoginRequiredMixin, generic.detail.DetailView):
    """Provide the details of one single position in the depot."""

    model = DepotItem

    pk_url_kwarg = "depotitem_id"

    context_object_name = "depotitem"

    template_name_suffix = "_detail"
