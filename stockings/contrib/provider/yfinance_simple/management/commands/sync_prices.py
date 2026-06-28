# SPDX-FileCopyrightText: 2026 Mischback
# SPDX-License-Identifier: MIT
# SPDX-FileType: SOURCE

"""Add a command to ``django-admin.py``."""

# Django imports
from django.core.management.base import BaseCommand, CommandError

# app imports
from stockings.contrib.provider.yfinance_simple.exceptions import (
    YFinanceSimpleServiceException,
)
from stockings.contrib.provider.yfinance_simple.services import fetch_prices


class Command(BaseCommand):
    """Implement a command for ``django-admin``."""

    help = "Fetch price information from Yahoo Finance"

    def add_arguments(self, parser):  # noqa: D102
        parser.add_argument("--period", type=str, default="5d")

    def handle(self, *args, **options):  # noqa: D102
        self.stdout.write("Updating price information from Yahoo Finance...")

        try:
            result = fetch_prices(period=options["period"])

            self.stdout.write(
                self.style.SUCCESS(
                    "Command completed. Created {} new price information objects.".format(
                        result["imported"]
                    )
                )
            )

            if result["failed"]:
                self.stdout.write(
                    self.style.WARNING(
                        "Warning: The following tiggers failed to update: {}".format(
                            result["failed"]
                        )
                    )
                )
        except YFinanceSimpleServiceException as e:
            raise CommandError("Command failed!") from e
