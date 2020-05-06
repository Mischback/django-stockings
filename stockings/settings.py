# Django imports
from django.conf import settings

STOCKINGS_DEFAULT_CURRENCY = getattr(settings, "STOCKINGS_DEFAULT_CURRENCY", "EUR")
