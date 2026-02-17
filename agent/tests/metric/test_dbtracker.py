
import unittest
from apminsight.metric.dbtracker import DbTracker

class DbTrackerTest(unittest.TestCase):

    dbtracker = DbTracker({'component': 'MYSQL'})
    query = "select * from developer where name='chan'"
    masked_query = "select * from developer where name=?"
    info = {'query': query}
    dbtracker.set_info(info)

    def test_get_tracker_name(self):
        dbtracker = DbTracker({'component': 'MYSQL'})
        tname = dbtracker.get_tracker_name()
        self.assertEqual('anonymous', tname)
        info = {'query': "update developer set quit=true where name='chan'"}
        dbtracker.set_info(info)
        dbtracker.extract_operartion_info()
        self.assertEqual('MYSQL - update', dbtracker.get_tracker_name())


    def test_extract_operartion_info(self):
        info = self.dbtracker.extract_operartion_info()
        self.assertTrue({'opn' : 'select', 'obj' : 'developer'}.items()<= info.items())

    def test_get_tracker_info(self):
        trace_info = {'db_opn' : []}
        self.dbtracker.get_tracker_info(trace_info)
        self.assertTrue('select/developer' in trace_info.get('db_opn'))

    def test_get_additional_info(self):
        #need to test by changing sql parameterized threshold
        info = self.dbtracker.get_additional_info()
        self.assertEqual(self.masked_query, info['query'])
    