# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""App-specific field definitions."""

# Django imports
from django.forms import ModelChoiceField


class DepotItemChoiceField(ModelChoiceField):
    """Custom choice field with specific formatting of the options.

    Used to provide the dropdown to select a
    :class:`~stockings.models.depot.DepotItem` instance. However, the magic
    ``__str__()`` method of those items provides too much context (and is mostly
    geared to work on the console) for the frontend. This custom implementation
    strips most of the information down.
    """

    def label_from_instance(self, obj):  # noqa: D102
        return "{} ({}) - {}".format(
            obj.stock_item.name, obj.stock_item.isin, obj.depot.name
        )
