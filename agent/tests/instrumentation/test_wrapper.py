
import unittest

from apminsight.context import set_cur_txn, get_cur_txn
from apminsight.metric.txn import Transaction
from apminsight.metric.tracker import Tracker
from apminsight.instrumentation.wrapper import default_wrapper, handle_tracker_end
from apminsight.instrumentation.wrapper import copy_attributes
from apminsight.instrumentation import instrument_method


class Mock:

    data = "chan"


class TestWrapper(unittest.TestCase):
    
    def actual(self, val):
        return val + 10

    def test_instrument_method(self):
        instrument_method('test', None, {'method': 'actual'})
        instrument_method(None, None, None)
        instrument_method('test', TestWrapper, {'method': 'actual'})
        self.assertTrue(getattr(TestWrapper, 'actual') != self.actual)
        wrapper = getattr(TestWrapper, 'actual')
        self.assertTrue(wrapper.__name__ == 'actual')

    def test_default_wrapper(self):
        wrapper = default_wrapper(self.actual, 'test', {})
        self.assertEqual(wrapper(10), 20)

    def test_copy_attributes(self):
        obj1 = Mock()
        setattr(obj1, 'custom',  10)
        obj2 = Mock()
        copy_attributes(obj1, obj2)
        self.assertEqual(getattr(obj2, 'custom'),  10)

    def test_handle_tracker_end(self):
        handle_tracker_end(None, None, None, None, None, None)
        txn = Transaction()        
        tracker = Tracker()
        set_cur_txn(txn)
        handle_tracker_end(tracker, None, None, None, None, None)
        self.assertTrue(tracker.is_completed())
        set_cur_txn(None)
