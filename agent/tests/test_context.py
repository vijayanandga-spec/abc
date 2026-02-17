
import unittest
from apminsight import context
from apminsight.metric.txn import Transaction
from apminsight.metric.tracker import Tracker

class ContextTest(unittest.TestCase):
 
    def test_set_cur_txn(self):
        txn = Transaction({}, {})
        context.set_cur_txn(txn)
        self.assertEqual(txn, context.get_cur_txn())
    
    def test_set_cur_tracker(self):
        tracker = Tracker({})
        context.set_cur_tracker(tracker)
        self.assertEqual(tracker, context.get_cur_tracker())

    def test_ser_cur_context(self):
        txn = Transaction({}, {})
        tracker = Tracker({})
        context.ser_cur_context(txn, tracker)
        self.assertEqual(txn, context.get_cur_txn())
        self.assertEqual(tracker, context.get_cur_tracker())
        self.assertEqual(True, context.is_txn_active())
        self.assertEqual(False, context.is_no_active_txn())

    def test_clear_cur_context(self):
        context.clear_cur_context()
        self.assertEqual(None, context.get_cur_txn())
        self.assertEqual(None, context.get_cur_tracker())
        self.assertEqual(False, context.is_txn_active())
        self.assertEqual(True, context.is_no_active_txn())
