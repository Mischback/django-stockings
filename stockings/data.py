"""Provides data structures for communication between objects."""

# Django imports
from django.utils.timezone import now


class StockingsMoney:
    """Provides a structured interface to pass money-related data around.

    Throughout django-stockings, all money-related data is always constructed
    of an actual value, its currency and a timestamp. This class provides a
    mean to pass these information around between different objects."""

    def __init__(self, amount, currency, timestamp=None):
        """Create a simple app-specific Money object.

        No validation/verification is done here, it will probably break, when
        the included values are stored in Django models (because of Django's
        validation).

        ``timestamp`` may be omitted, the object's creation time will be used
        to fill that gap."""

        self.amount = amount
        self.currency = currency
        self.timestamp = timestamp or now()

    def __str__(self):
        return '{} {} ({})'.format(
            self.currency, self.amount, self.timestamp
        )  # pragma: nocover

    def convert(self, target_currency):
        """Convert the value of the object to another target currency.

        Currency conversion 'should be' implemented, but is highly dependent
        on the availability of exchange rates between the currencies."""
        raise NotImplementedError('Currency conversion is currently not implemented!')
