"""Provides data structures for communication between objects."""

# Django imports
from django.utils.timezone import now

# app imports
from stockings.exceptions import StockingsInterfaceError


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
        return "{} {} ({})".format(
            self.currency, self.amount, self.timestamp
        )  # pragma: nocover

    def add(self, summand):
        """Add `summand` to the object and return a new `StockingsMoney` object.

        The new object will have `currency` set to the original object's
        currency and its `timestamp` will be updated."""

        # This block ensures, that `summand` has a `currency` attribute and a
        # method `convert()`.
        try:
            # perform currency conversion, if necessary
            if self.currency != summand.currency:
                summand = summand.convert(self.currency)
        except AttributeError:
            raise StockingsInterfaceError(
                "StockingsMoney.add() was called with an incompatible summand."
            )

        # This block ensures, that `summand` has a `amount` attribute (this is
        # catched by the `AttributeError`) and furthermore will only work with
        # 'addable' `amount` values (this is catched by the `TypeError`).
        try:
            # actually return the new object with summed up `amounts`
            return StockingsMoney(self.amount + summand.amount, self.currency)
        except (AttributeError, TypeError):
            raise StockingsInterfaceError(
                "StockingsMoney.add() was called with an incompatible summand."
            )

    def convert(self, target_currency):
        """Convert the value of the object to another target currency.

        Currency conversion 'should be' implemented, but is highly dependent
        on the availability of exchange rates between the currencies."""
        raise NotImplementedError("Currency conversion is currently not implemented!")

    def multiply(self, multiplier):
        """Multiply this object's amount with `multiplier` and updates the timestamp."""

        # TODO: 'multiplier' should be some sort of number

        self.amount *= multiplier
        self.timestamp = now()

        return self
