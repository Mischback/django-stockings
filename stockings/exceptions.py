"""Provides app-specific exceptions."""


class StockingsException(Exception):
    """Base class for all app-specific exceptions."""

    pass


class StockingsCurrencyConversionError(StockingsException):  # noqa: D205, D400
    """This exception is raised whenever the conversion of currencies is
    required.
    """

    pass


class StockingsInterfaceError(StockingsException):  # noqa: D205, D400
    """This exception is raised, if an operation is performed, that is not
    intended.
    """

    pass


class StockingsTemplateError(StockingsException):
    """This exception is raised, if there is an error in the app's templatetags."""

    pass
