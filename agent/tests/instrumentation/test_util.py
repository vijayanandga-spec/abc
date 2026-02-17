
import unittest
from apminsight.instrumentation.util import create_tracker_info
from apminsight.metric.tracker import Tracker

tracker = Tracker()

info = {
        'name' : 'django.exit',
        'method' : 'exit',
        'component' : 'django',
        'is_db_tracker' : True,
        'parent'  : tracker
    }

class TestUtil(unittest.TestCase):

    def test_create_tracker_info(self):
        tracker_info = create_tracker_info('django', info, tracker)
        self.assertEqual(tracker_info['name'], info['name'])
        self.assertEqual(tracker_info['component'], info['component'])
        self.assertEqual(tracker_info['is_db_tracker'], info['is_db_tracker'])
        self.assertEqual(tracker_info['parent'], info['parent'])


