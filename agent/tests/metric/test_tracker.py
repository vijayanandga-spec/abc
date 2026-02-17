
import unittest
from apminsight.metric.tracker import Tracker

class TrackerTest(unittest.TestCase):

    tracker = Tracker()
    child_tracker = Tracker()
    tracker.add_child_tracker(child_tracker)
    tracker.end_tracker(None)

    errortracker = Tracker()
    errortracker.end_tracker(RuntimeError('TEST'))

    def test_mark_error(self):
        self.assertFalse(self.tracker.is_error())
        self.assertTrue(self.errortracker.is_error())

    def test_end_tracker(self):
        self.assertTrue(self.tracker.is_completed())
        self.assertTrue(self.errortracker.is_completed())
        self.assertTrue(self.errortracker.is_error())

    def test_check_and_add_loginfo(self):
        trace_info = {}
        self.errortracker.check_and_add_loginfo(trace_info)
        self.assertEqual(len(trace_info['loginfo']), 1)
        loginfo = trace_info['loginfo'].pop()
        self.assertTrue('time' in loginfo)
        self.assertTrue('st' in loginfo)
        self.assertEqual(loginfo['level'], 'FATAL')
        self.assertEqual(loginfo['str'], 'TEST')
        self.assertEqual(loginfo['err_clz'], 'RuntimeError')

    def test_get_tracker_info(self):
        tracker_info = self.tracker.get_tracker_info()
        self.assertTrue(len(tracker_info)==7)
        self.assertTrue(type(tracker_info[0]) is int)
        self.assertTrue(type(tracker_info[1]) is str)
        self.assertTrue(type(tracker_info[2]) is str)
        self.assertTrue(type(tracker_info[3]) is int)
        self.assertTrue(type(tracker_info[4]) is int)
        self.assertTrue(tracker_info[3]>= tracker_info[4])
        self.assertTrue(type(tracker_info[5]) is dict)
        self.assertTrue(type(tracker_info[6]) is list)

    def test_get_additional_info(self):
        info = self.tracker.get_additional_info()
        self.assertTrue(type(info) is dict)

    def test_get_tracker_data_for_trace(self):
        trace_info = {'method_count' : 1}
        tracker_data = self.tracker.get_tracker_data_for_trace(trace_info)
        self.assertEqual(trace_info['method_count'], 2)
        self.assertTrue(self.child_tracker.get_tracker_info(trace_info) in tracker_data[6])

    def test_get_tracker_name(self):
        self.assertEqual(self.tracker.get_tracker_name(), 'anonymous')
        self.tracker.set_info({'opn': 'SET'})
        self.assertEqual(self.tracker.get_tracker_name(), ' - SET')
        self.tracker.set_component('COMP')
        self.assertEqual(self.tracker.get_tracker_name(), 'COMP - SET')
        self.tracker.set_info({'host': 'local', 'port' : '3306'})
        self.assertEqual(self.tracker.get_tracker_name(), 'COMP - SET - local:3306')






        
    

    
        
        