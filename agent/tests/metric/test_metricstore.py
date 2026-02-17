
import unittest
from apminsight.metric.metricstore import Metricstore
from apminsight.metric.txn import Transaction
from apminsight.config.threshold import Threshold
from apminsight.metric.apdexmetric import TxnMetric
from apminsight.metric.dbmetric import DbMetric
from apminsight.metric.dbtracker import DbTracker
from .mock import mock_function

class MetricStoreTest(unittest.TestCase):

    store = Metricstore()

    def test_add_web_txn(self):
        txn = Transaction()
        self.assertFalse(self.store.add_web_txn(txn))
        txn.end_txn()
        actualfn = Threshold.get_webtxn_sampling_factor
        Threshold.get_webtxn_sampling_factor = mock_function(2)
        self.assertTrue(self.store.add_web_txn(txn))
        self.assertFalse(self.store.add_web_txn(txn))
        self.assertTrue(self.store.add_web_txn(txn))
        self.assertTrue('transaction/http/' in self.store.get_webtxn_metric())
        Threshold.get_webtxn_sampling_factor = actualfn

    def test_is_critical(self):
        txn = Transaction({'PATH_INFO': '/test'})
        txn.end_txn()
        self.store.trace_history = {}
        self.assertTrue(self.store.is_critical(txn))
        txn.set_rt(150)
        txn.set_exceptions_count(2)
        self.store.trace_history = {'/test-': {'exceptioncount' : 2, 'rt' : 200}}
        self.assertFalse(self.store.is_critical(txn))
        self.assertEqual(self.store.trace_history['/test-']['rt'], 200)
        self.assertEqual(self.store.trace_history['/test-']['exceptioncount'], 2)
        self.store.trace_history = {'/test-': {'exceptioncount' : 1, 'rt' : 200}}
        self.assertTrue(self.store.is_critical(txn))
        self.store.trace_history = {'/test-': {'exceptioncount' : 3, 'rt' : 100}}
        self.assertTrue(self.store.is_critical(txn))

    def test_check_and_include_in_trace(self):
        txn = Transaction()
        txn.end_txn()
        res = self.store.check_and_include_in_trace(txn)
        self.assertFalse(res)
        txn.set_rt(400)
        txn.set_exceptions_count(4)
        res = self.store.check_and_include_in_trace(txn)
        self.assertTrue(res)

    def test_iter_and_append_dbmetric(self):
        dbtracker = DbTracker({'component' : 'MYSQL'})
        dbmetric = DbMetric()
        dbmetric.accumulate(dbtracker)
        formatted_data = []
        Metricstore.iter_and_append_dbmetric(formatted_data, {'test' : dbmetric}, ns='testns')
        self.assertTrue(len(formatted_data)==1)
        info, data = formatted_data[0]
        self.assertTrue('testns'==info['ns'])
        self.assertTrue('test'==info['name'])
        self.assertTrue(len(data)==5)

    def test_get_formatted_trace(self):
        store = Metricstore()
        txn = Transaction()
        store.trace_list = [txn]
        tracelist = store.get_formatted_trace()
        self.assertTrue(len(tracelist)==1)

    def test_get_formatted_data(self):
        store = Metricstore()
        txn = Transaction()
        txn.end_txn()
        apdex = TxnMetric()
        apdex.aggregate(txn)
        store.web_txn_metric = {"-" : apdex}
        data = store.get_formatted_data()
        self.assertTrue(len(data)==2)

    def test_cleanup(self):
        test = {'test': 'something'}
        self.store.web_txn_metric=test
        self.store.bg_txn_metric=test
        self.store.trace_list=['test']
        self.store.trace_history = test
        self.store.db_call_count=3
        self.store.app_metric_sum = test
        self.store.app_metric_avg = test
        self.store.cleanup()
        self.assertDictEqual(self.store.web_txn_metric,{})
        self.assertDictEqual(self.store.bg_txn_metric,{})
        self.assertEqual(self.store.trace_list,[])
        self.assertDictEqual(self.store.trace_history, {})
        self.assertTrue(self.store.db_call_count==0)
        self.assertDictEqual(self.store.app_metric_sum, {})
        self.assertDictEqual(self.store.app_metric_avg, {})


    

