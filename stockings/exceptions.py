"""Provides app-specific exceptions."""


class StockingsException(Exception):
    """Base class for all app-specific exceptions."""

    pass


class StockingsCurrencyConversionError(StockingsException):
    """This exception is raised whenever the conversion of currencies is
    required."""

    pass


class StockingsInterfaceError(StockingsException):
    """This exception is raised, if an operation is performed, that is not
    intended."""

    pass