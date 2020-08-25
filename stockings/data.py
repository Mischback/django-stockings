"""Provides data structures for communication between objects."""

# Python imports
import decimal

# Django imports
from django.utils.timezone import now

# app imports
from stockings.exceptions import StockingsInterfaceError


class StockingsMoney:
    """Provides a structured interface to pass money-related data around.

    Throughout django-stockings, all money-related data is always constructed
    of an actual value (amount), its currency and a timestamp. This class provides
    a mean to pass these information around between different objects.

    No validation / verification is done in this object, but will be applied by
    Django's ORM layer.

    Parameters
    ----------
    amount
        The actual numerical value.
    currency : str
        The currency of the object. Should be a pre-determined string, because
        the models only accept a set of valid values, but is not enforced in
        objects of this class.
    timestamp : datetime.datetime, optional
        Money-related fields always provide a timestamp, usually describing their
        last update. If this parameter is omitted, it will be set to the current
        time, as provided by Django's wrapper to `now`.

    Returns
    -------
    StockingsMoney
        A new class instance.

    Raises
    ------
    StockingsInterfaceError
        If add() is called with an incompatible summand or multiply() with an
        incompatible multiplier.
    """

    amount = None
    currency = None
    timestamp = None

    def __init__(self, amount, currency, timestamp=None):
        """Create a simple app-specific Money object."""
        self.amount = amount
        self.currency = currency
        self.timestamp = timestamp or now()

    def __eq__(self, other):
        """Determine equality of two instances."""
        if type(other) is type(self):
            return self.__dict__ == other.__dict__

        return False

    def __str__(self):
        """Return a string representation of the instance."""
        return "{} {} ({})".format(
            self.currency, self.amount, self.timestamp
        )  # pragma: nocover

    def add(self, summand):
        """Add `summand` to the object and return a new `StockingsMoney` object.

        The new object will have `currency` set to the original object's
        currency and its `timestamp` will be updated.

        Parameters
        ----------
        summand : StockingsMoney
            The value to be added to the object, should typically be an instance
            of `StockingsMoney` aswell.

        Returns
        -------
        StockingsMoney
            A new instance of `StockingsMoney`, where `amount` is the requested
            sum, `currency` is unchanged and `timestamp` is set to the current
            `datetime.datetime` .

        Raises
        ------
        StockingsInterfaceError
            If `summand` does not have a `convert()` method, a `currency`
            attribute or the actual addition causes a `TypeError`.
        """
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
            return StockingsMoney(
                self.amount + summand.amount,
                self.currency,
                max(self.timestamp, summand.timestamp),
            )
        except (AttributeError, TypeError):
            raise StockingsInterfaceError(
                "StockingsMoney.add() was called with an incompatible summand."
            )

    def convert(self, target_currency):
        """Convert the value of the object to another currency.

        Parameters
        ------------
        target_currency : str
            The three-letter identifier of the currency to be converted to.

        Returns
        --------
        StockingsMoney
            A new instance of `StockingsMoney` is returned, with adjusted `amount`
            and updated `currency` values.

        Raises
        -------
        NotImplementedError
            This error is raised until currency conversion is actually implemented
            in a future release.

        Warnings
        ----------
        Currency conversion is currently **not implemented** and calling this method
        will most likely raise `NotImplementedError`.

        Notes
        -------
        Currency conversion is dependent on the availability of currency exchange
        rates. These rates **should** be matching the object's `timestamp`, meaning
        that a history of conversion rates must be maintained inside the app.

        Furthermore, to reduce required conversion rate updates, only a specific
        set of target currencies should be available.
        """
        if self.currency == target_currency:
            return self

        raise NotImplementedError("Currency conversion is currently not implemented!")

    def multiply(self, multiplier):
        """Multiply the object's `amount` with `multiplier`.

        `multiplier` is a given (decimal) number. Thus, no currency conversion is
        required to calculate the new `amount` and the returned `StockingsMoney`
        instance will provide the original `currency`.

        The `StockingsMoney` instance's `timestamp` will be set to the time of
        the multiplication. This means, that possibly *older* values are
        artificially updated to a current timestamp.

        Parameters
        ------------
        multiplier : number
            The number to multiply with. Must be castable to `decimal.Decimal`.

        Returns
        --------
        StockingsMoney
            A new instance of `StockingsMoney`, where `amount` is the requested
            product, `currency` is unchanged and `timestamp` is set to the current
            `datetime.datetime` .

        Raises
        -------
        StockingsInterfaceError
            If the `multiplier` is not compatible for multiplication with a
            `decimal.Decimal` value.
        """
        try:
            return StockingsMoney(
                self.amount * decimal.Decimal(multiplier), self.currency, self.timestamp
            )
        except (ValueError, TypeError, decimal.InvalidOperation):
            raise StockingsInterfaceError(
                "StockingsMoney.multiply() was called with an incompatible multiplier."
            )
