# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""App-specific exceptions."""


class YFinanceSimpleException(Exception):
    """Base exception for this app."""


class YFinanceSimpleServiceException(YFinanceSimpleException):
    """Base exception for the actual service."""
