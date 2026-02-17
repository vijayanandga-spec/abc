
import unittest
import random
from apminsight.metric.apdexmetric import TxnMetric
from apminsight.metric.txn import Transaction
from apminsight.metric.tracker import  Tracker
from apminsight.metric.dbtracker import DbTracker
from apminsight.config.threshold import  Threshold
from apminsight.metric.component import Component
from .mock import MockResponse

def get_txnmetric_attributes():
    return ['rt', 'err_rt', 'satisfied', 'tolerating',  
        'frustrated', 'err_count', 'min_rt', 'max_rt',
        'count']

def get_txnmetric_obj():
    txnmetric = TxnMetric()
    for each in get_txnmetric_attributes():
        setattr(txnmetric, each, random.randint(1,  100))

    txnmetric.error_codes = { 400 : 2 }
    txnmetric.exceptions_info  = { 'Error' : 3 }
    txnmetric.internal_comps = {'DJANGO' : Component(Tracker({'component' : 'DJANGO'}))}
    txnmetric.external_comps = {'MYSQL' : Component(Tracker({'component' : 'MYSQL'}))} 
    txnmetric.db_calls = [ DbTracker({'component' : 'MYSQL'})]
    return  txnmetric
        

class ApdexMetricTest(unittest.TestCase):

    txnmetric = TxnMetric()

    txn = Transaction()
    txn.end_txn()

    errortxn = Transaction()
    res = MockResponse(400)
    errortxn.end_txn(res)

    def test_accumulate(self):
        txnmetric1 = TxnMetric()
        txnmetric2  = get_txnmetric_obj()
        txnmetric1.accumulate(txnmetric2)
        for each_atr in get_txnmetric_attributes():
            self.assertEqual(getattr(txnmetric1, each_atr), getattr(txnmetric2, each_atr))
        
        self.assertTrue('DJANGO' in txnmetric1.internal_comps)
        self.assertTrue(isinstance(txnmetric1.internal_comps['DJANGO'], Component))
        self.assertTrue('MYSQL' in txnmetric1.external_comps)
        self.assertTrue(isinstance(txnmetric1.external_comps['MYSQL'], Component))
        self.assertDictEqual(txnmetric1.error_codes, txnmetric2.error_codes)
        self.assertDictEqual(txnmetric1.exceptions_info, txnmetric2.exceptions_info)

    def test_update_apdex_metric(self):
        self.txnmetric.satisfied = 1
        self.txnmetric.tolerating = 3
        self.txnmetric.frustrated = 2
        self.txn.set_rt(100)
        self.txnmetric.update_apdex_metric(self.txn)
        self.txn.set_rt(1500)
        self.txnmetric.update_apdex_metric(self.txn)
        self.txn.set_rt(2001)
        self.txnmetric.update_apdex_metric(self.txn)
        self.assertEqual(self.txnmetric.satisfied, 2)
        self.assertEqual(self.txnmetric.tolerating, 4)
        self.assertEqual(self.txnmetric.frustrated, 3)


    def test_update_req_count(self):
        prevcount = self.txnmetric.count
        self.txnmetric.update_req_count(self.txn)
        prev_err_count = self.txnmetric.err_count
        self.txnmetric.update_req_count(self.errortxn)
        self.assertTrue(self.txnmetric.count== prevcount+1)
        self.assertTrue(self.txnmetric.err_count== prev_err_count+1)

    def test_aggregate(self):
        self.txnmetric.err_rt = 0
        self.txnmetric.err_count = 0
        self.txnmetric.count =  0
        self.errortxn.set_rt(20)
        self.txn.set_rt(50)
        self.txnmetric.aggregate(self.txn)
        self.txnmetric.aggregate(self.errortxn)
        self.assertEqual(self.txnmetric.err_count, 1)
        self.assertEqual(self.txnmetric.count, 1)
        self.assertEqual(self.txnmetric.err_rt, 20)
        self.assertEqual(self.txnmetric.rt, 50)

    def test_aggregate_non_error_txn(self):
        self.txnmetric.count =  1
        self.txnmetric.rt = 100
        self.txnmetric.min_rt  = 10
        self.txnmetric.max_rt =  50
        self.txn.set_rt(120)
        self.txnmetric.aggregate_non_error_txn(self.txn)
        self.assertEqual(self.txnmetric.count,  2)
        self.assertEqual(self.txnmetric.rt,  220)
        self.assertEqual(self.txnmetric.min_rt,  10)
        self.assertEqual(self.txnmetric.max_rt,  120)
        self.txn.set_rt(5)
        self.txnmetric.aggregate_non_error_txn(self.txn)
        self.assertEqual(self.txnmetric.min_rt,  5)
        self.txn.set_rt(0)
        self.txnmetric.aggregate_non_error_txn(self.txn)
        self.assertEqual(self.txnmetric.min_rt,  0)
        self.assertEqual(self.txnmetric.max_rt,  120)

        
    def test_aggregate_txn_sub_resources(self):
        self.txn.update_db_calls(['test', 'properly'])
        self.txnmetric.aggregate_txn_sub_resources(self.txn)
        self.assertEqual(self.txnmetric.db_calls,  self.txn.get_db_calls())
        self.txnmetric.aggregate_txn_sub_resources(self.txn)
        self.assertEqual(self.txnmetric.db_calls,  self.txn.get_db_calls()+self.txn.get_db_calls())

    def test_aggregate_exceptions(self):
        self.txnmetric.exceptions_info = {}
        excinfo = {'Error' : 2}
        self.txnmetric.aggregate_exceptions(excinfo)
        self.assertDictEqual(self.txnmetric.exceptions_info, excinfo)
        self.txnmetric.aggregate_exceptions(excinfo)
        self.assertDictEqual(self.txnmetric.exceptions_info, {'Error' : 4})


    def test_aggregate_components(self):
        tracker = Tracker()
        http_comp =  Component(tracker)
        mysql_comp = Component(tracker)
        comp1  = {'HTTP' :  http_comp}
        comp2  = {'MYSQL' :  mysql_comp}
        TxnMetric.aggregate_components(comp1, comp2)
        self.assertTrue(isinstance(comp1['HTTP'], Component))
        self.assertTrue(isinstance(comp1['MYSQL'], Component))
        TxnMetric.aggregate_components(comp1, comp2)
        self.assertTrue(isinstance(comp1['MYSQL'], Component))

    def test_accumulate_errorcodes(self):
        self.txnmetric.error_codes = {400 : 1}
        self.txnmetric.accumulate_errorcodes({400:2})
        self.assertDictEqual({400:3}, self.txnmetric.error_codes)
        self.txnmetric.accumulate_errorcodes({500:2})
        self.assertDictEqual({400:3, 500:2}, self.txnmetric.error_codes)

    def test_aggregate_errorcode(self):
        self.txnmetric.error_codes= {}
        self.txnmetric.aggregate_errorcode(self.errortxn)
        self.assertTrue(self.txnmetric.error_codes[400]==1)
        self.txnmetric.aggregate_errorcode(self.errortxn)
        self.assertTrue(self.txnmetric.error_codes[400]==2)
       
    def test_get_formatted_data(self):
        data = self.txnmetric.get_formatted_data(ns='test')
        self.assertTrue(len(data)==2)
        info, data_part = data
        apdex_rt_data, additional_metric = data_part
        self.assertTrue(type(info)==dict)
        self.assertTrue(len(data_part)==2)
        self.assertTrue(type(apdex_rt_data)==list)
        self.assertTrue(type(additional_metric)==dict)
        self.assertTrue(len(apdex_rt_data)==9)
        self.assertTrue(len(additional_metric)==4)
        self.assertTrue(type(additional_metric['httpcode'])==dict)
        self.assertTrue(type(additional_metric['error_rt'])==int)
        self.assertTrue(type(additional_metric['logmetric'])==dict)
        self.assertTrue(type(additional_metric['components'])==list)


