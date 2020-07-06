"""Provides app-specific classes for test cases."""

# Django imports
from django.db.models.signals import post_save  # noqa: F401
from django.test import TestCase


class StockingsTestCaseBase(TestCase):
    """Base class for all app-specific tests."""

    @classmethod
    def _disconnect_signal_callbacks(cls):
        """Disconnect all signal callbacks for testing."""
        pass

    @classmethod
    def _reconnect_signal_callbacks(cls):
        """Reconnect all signal callbacks for testing."""
        pass


class StockingsTestCase(StockingsTestCaseBase):
    """This class supports testing without the app's signals."""

    @classmethod
    def setUpClass(cls):
        """Prepare the testing environment."""
        super().setUpClass()

        cls._disconnect_signal_callbacks()

    @classmethod
    def tearDownClass(cls):
        """Clean up after executing the tests."""
        cls._reconnect_signal_callbacks()

        super().tearDownClass()
