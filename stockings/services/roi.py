# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Provide different calculations for the Return of Invest."""

# Python imports
import logging

# external imports
from pyxirr import DayCount, InvalidPaymentsError, xirr

logger = logging.getLogger(__name__)


def mwrr(cashflows, current_value=None):
    """Calculate the money-weighted rate of return (MWRR).

    Uses ``xirr`` from the ``pyxirr`` package internally.

    Parameters
    ----------
    cashflows: list - A list of all cashflows; providing a Django QuerySet does
                      work.
    current_value: StockingsMoney - The current value to be considered for the
                                    calculation. It is meant to be an instance
                                    of StockingsMoney, but the ``amount`` and
                                    ``timestamp`` are accessed directly, so
                                    a plain dict may work aswell.

    Returns
    -------
    ``float`` or ``None``
    """
    # Convert ``cashflows`` into the required format.
    # This is basically two list comprehensions in one, extracting the required
    # ``amount`` and ``timestamp`` attributes into a list of tuples...
    data = [
        (flow.timestamp.date(), float(flow.net_cashflow.amount)) for flow in cashflows
    ]

    if not data:
        return 0.0

    # ...split into dedicated lists
    dates, amounts = map(list, zip(*data))

    if current_value is not None:
        dates.append(current_value.timestamp.date())
        amounts.append(float(current_value.amount))

    logger.debug(dates)
    logger.debug(amounts)

    try:
        return xirr(dates, amounts, day_count=DayCount.ACT_ACT_ISDA)
    except InvalidPaymentsError:
        return 0.0
