
import os
import unittest
from tests.metric.mock import  MockResponse
from apminsight.agent import Agent
from apminsight.metric.txn import Transaction
from apminsight.metric.tracker import Tracker
from apminsight.metric.dbtracker import DbTracker
from apminsight.config.configuration import Configuration
from apminsight.config.threshold import Threshold
from apminsight.collector.ins_info import Instanceinfo
from apminsight.metric.metricstore import Metricstore
from apminsight.context import get_cur_txn, clear_cur_context
from apminsight.context import set_cur_txn, get_cur_tracker

class AgentTest(unittest.TestCase):

    agent = Agent.initialize({'appname': 'charnzet'})
    def test_initialize(self):
        os.environ['S247_LICENSE_KEY'] = ''
        with self.assertRaises(RuntimeError):
             Agent.initialize()

        os.environ['S247_LICENSE_KEY'] = 'eu_chandhru'
        self.assertTrue(Agent.initialize() is not None)
        self.assertEqual(self.agent.get_config().get_app_name(), 'charnzet')

    def test_is_data_collection_allowed(self):
        self.assertTrue(self.agent.is_data_collection_allowed())
        self.agent.ins_info.status = 911
        self.assertTrue(self.agent.is_data_collection_allowed())
        self.agent.ins_info.status = 910
        self.assertFalse(self.agent.is_data_collection_allowed())
        self.agent.ins_info.status = None

    def test_check_and_create_webtxn(self):
        self.assertEqual(self.agent.check_and_create_webtxn(None, None), None)
        self.agent.ins_info.status = 910
        self.assertEqual(self.agent.check_and_create_webtxn({}, {}), None)
        self.agent.ins_info.status = None
        self.assertEqual(self.agent.check_and_create_webtxn({}, {}), None)
        self.agent.threshold.thresholdmap['transaction.skip.listening'] = ['.css', '.js', '.gif', '.jpg', '.jpeg', '.bmp', '.png', '.ico']
        txn = self.agent.check_and_create_webtxn({'PATH_INFO': '/quit.js'}, {})
        self.assertTrue(txn is None)
        txn = self.agent.check_and_create_webtxn({'PATH_INFO': '/quit'}, {})
        self.assertTrue(isinstance(txn, Transaction))
        self.assertTrue(get_cur_txn()==txn)
        clear_cur_context()

    def test_check_and_create_tracker(self):
        self.assertIsNone(self.agent.check_and_create_tracker(None))
        set_cur_txn(Transaction())
        self.assertIsNone(self.agent.check_and_create_tracker(None))
        tracker = self.agent.check_and_create_tracker({})
        self.assertTrue(isinstance(tracker, Tracker))
        dbtracker = self.agent.check_and_create_tracker({'is_db_tracker': True})
        self.assertTrue(isinstance(dbtracker, DbTracker))
        self.assertTrue(get_cur_tracker()==dbtracker)
        clear_cur_context()

    def test_end_txn(self):
        self.agent.end_txn(None)
        txn = Transaction()
        self.agent.end_txn(txn)
        self.assertTrue(txn.is_completed())
        self.agent.end_txn(txn, MockResponse(400))
        self.assertTrue(txn.is_error_txn())
        self.agent.end_txn(txn, MockResponse(200), RuntimeError("TESTERR"))
        self.assertTrue(txn.is_error_txn())

    def test_end_tracker(self):
        tracker = Tracker()
        self.agent.end_tracker(None)
        self.agent.end_tracker(tracker)
        self.assertFalse(tracker.is_completed())
        txn = Transaction()
        set_cur_txn(txn)
        self.agent.end_tracker(tracker)
        self.assertTrue(tracker.is_completed())
        self.agent.end_tracker(tracker, RuntimeError("TESTERR"))
        self.assertTrue(tracker.is_error())
        clear_cur_context()

    def test_get_config(self):
        self.assertTrue(isinstance(self.agent.get_config(), Configuration))

    def test_get_threshold(self):
        self.assertTrue(isinstance(self.agent.get_threshold(), Threshold))

    def test_get_ins_info(self):
        self.assertTrue(isinstance(self.agent.get_ins_info(), Instanceinfo))

    def test_get_metric_store(self):
        self.assertTrue(isinstance(self.agent.get_metric_store(), Metricstore))

    


    
