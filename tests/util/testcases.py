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


class StockingsORMTestCase(StockingsTestCase):
    """This class supports testing with fixture data.

    What is inside this test fixture?
    =================================

    Objects
    -------
    - 3 user instances
        - Alice, Bob, Charly (superuser)
        - all passwords: "foobar"
    - 5 StockItem instances
        - StockItem01 (XX0000000001); 10 StockItemPrice instances (Pfizer)
        - StockItem02 (XX0000000002); 10 StockItemPrice instances (Fox Corp)
        - StockItem03 (XX0000000003); 5 StockItemPrice instances (Walt Disney)
        - StockItem04 (XX0000000004); 5 StockItemPrice instances (Cisco)
        - StockItem05 (XX0000000005); 5 StockItemPrice instances (Merck)
    - 35 StockItemPrice instances
        - see above
    - 3 Portfolio instances
        - PortfolioA (Alice)
        - PortfolioB1 (Bob)
        - PortfolioB2 (Bob)
    - 8 PortfolioItem instances
        - PortfolioA - StockItem01:
            - BUY; 4; 2,90; 33,10; 2020-07-01 09:28:11
            - SELL; 4; 2,90; 34,50; 2020-07-08 09:29:08
        - PortfolioA - StockItem02:
            - BUY; 5; 2,90; 25,50; 2020-07-02 09:31:36
            - SELL; 5; 2,90; 27,55; 2020-07-06 09:32:26
            - BUY; 10; 2,90; 24,97; 2020-07-08 09:33:20
        - PortfolioA - StockItem03:
            - BUY; 7; 2,90; 110,25; 2020-07-05 09:35:27
        - PortfolioB1 - StockItem01:
            - BUY; 3; 1,90; 32,15; 2020-07-03 09:36:59
        - PortfolioB1 - StockItem04:
            - BUY: 4; 1,90; 45,90; 2020-07-06 09:42:02
            - BUY: 6; 1,90; 46,10; 2020-07-07 09:42:42
            - SELL: 5; 1,90; 46,50; 2020-07-10 09:43:23
        - PortfolioB1 - StockItem05:
            - BUY; 1; 1,90; 79,00; 2020-07-06 09:44:04
            - SELL; 1; 1,90; 79,50; 2020-07-06 09:46:19
            - BUY; 5; 1,90; 79,00; 2020-07-07 09:47:14
            - SELL; 3; 1,90; 76,65; 2020-07-10 09:47:53
        - PortfolioB2 - StockItem02:
            - BUY; 3; 3,50; 25,75; 2020-07-02 09:49:46
            - SELL; 3; 3,50; 25,25; 2020-07-09 09:50:35
        - PortfolioB2 - StockItem04:
            - BUY; 20; 3,50; 46,20; 2020-07-07 09:51:17
    -17 Trade instances
        - see above

    Command to dump the data
    ------------------------

    > tox -q -e django -- \
        dumpdata \
            --all \
            --indent 2 \
            --exclude admin.logentry \
            --exclude auth.permission \
            --exclude sessions.session \
            --exclude contenttypes.contenttype \
            --output tests/util/fixtures/test_data.json
    """

    fixtures = ["tests/util/fixtures/test_data.json"]
