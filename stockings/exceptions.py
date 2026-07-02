# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""App-specific exceptions."""


class StockingsException(Exception):
    """Base class for all app-specific exceptions."""


class StockingsModelException(StockingsException):
    """Base class for all app-specific and model-related exceptions."""


class StockingsInterfaceError(StockingsException):
    """Base class for all app-specific exceptions related to data interfaces."""
