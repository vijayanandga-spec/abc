
import unittest
from apminsight.metric.txn import Transaction
from apminsight.metric.tracker import Tracker
from apminsight.metric.dbtracker import DbTracker
from .mock import MockResponse

class TxnTest(unittest.TestCase):

    txn = Transaction()

    def test_end_txn(self):
        self.assertFalse(self.txn.is_completed())
        res = MockResponse(200)
        self.txn.end_txn(res)
        self.assertTrue(self.txn.is_completed())
        self.assertFalse(self.txn.is_error_txn())
        self.assertTrue(self.txn.get_root_tracker().is_completed())

    def test_aggregate_component(self):
        ext_tracker = Tracker({'component': 'MYSQL'})
        extcount = self.txn.get_ext_call_count()
        self.txn.aggregate_component(ext_tracker)
        self.assertEqual(self.txn.get_ext_call_count(), extcount+1)
        self.assertTrue('MYSQL-1' in self.txn.get_external_comps())
        int_tracker = Tracker({'component': 'DJANGO'})
        self.txn.aggregate_component(int_tracker)
        self.assertTrue('DJANGO' in self.txn.get_internal_comps())
        
    def test_check_and_add_db_call(self):
        dbtracker = DbTracker({'component': 'MYSQL'})
        self.txn.check_and_add_db_call(dbtracker)
        self.assertTrue(dbtracker in self.txn.get_db_calls())

    def test_check_and_add_error(self):
        errtracker = Tracker()
        errtracker.end_tracker(RuntimeError('TEST'))
        exc_count = self.txn.get_exceptions_count()
        self.txn.check_and_add_error(errtracker)
        self.assertEqual(self.txn.get_exceptions_count(), exc_count+1)
        self.assertDictEqual({'RuntimeError':1}, self.txn.get_exceptions_info())

    def test_comp_details_for_trace(self):
        tracker = Tracker({'component': 'INTCOMP'})
        errtracker = Tracker({'component' : 'ERRORCOMP'})
        errtracker.end_tracker(RuntimeError('TEST'))
        self.txn.aggregate_component(tracker)
        self.txn.aggregate_component(errtracker)
        details = Transaction.comp_details_for_trace(self.txn.get_internal_comps())
        self.assertTrue(details['success']['INTCOMP']>0)
        self.assertTrue(details['fail']['ERRORCOMP']>0)

    def test_get_trace_info(self):
        trace_info = self.txn.get_trace_info()
        self.assertTrue(type(trace_info['t_name']) is str)
        self.assertTrue(type(trace_info['http_method_name']) is str)
        self.assertTrue(type(trace_info['s_time']) is int)
        rt = trace_info['r_time']
        self.assertTrue(type(rt) is int and rt>=0)
        self.assertTrue(type(trace_info['http_query_str']) is str)
        self.assertTrue(type(trace_info['trace_reason']) is int)
        self.assertTrue(type(trace_info['db_opn']) is list)
        self.assertTrue(trace_info['method_count']==1)

    
    def test_is_error_txn(self):
        res = MockResponse(400)
        self.txn.end_txn(res)
        self.assertTrue(self.txn.is_error_txn())

