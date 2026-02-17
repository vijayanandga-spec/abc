
import unittest
from apminsight.metric.dbmetric import DbMetric
from apminsight.metric.dbtracker import DbTracker


class DbMetricTest(unittest.TestCase):

    dbmetric = DbMetric()     
    
    dbtracker = DbTracker({'component' : 'MYSQL'})     
    query = "select * from developer where name='chan'"
    dbtracker.set_info({'query': query})
    dbtracker.end_tracker(None)

    errdb = DbTracker({'component' : 'MYSQL'})
    errdb.set_info({'query': query})
    errdb.end_tracker(RuntimeError('TESTERROR'))


    def test_accumulate(self):
        self.dbmetric.accumulate(self.dbtracker)
        self.dbmetric.accumulate(self.dbtracker)
        self.dbmetric.accumulate(self.errdb)
        self.assertEqual(self.dbmetric.opn, 'select')
        self.assertEqual(self.dbmetric.obj, 'developer')
        self.assertEqual(self.dbmetric.component, 'MYSQL')
        self.assertEqual(self.dbmetric.errorct, 1)
        self.assertEqual(self.dbmetric.time, self.dbtracker.get_rt()*2)
        self.assertEqual(self.dbmetric.count, 2)
        self.assertEqual(self.dbmetric.minrt, self.dbtracker.get_rt())
        self.assertEqual(self.dbmetric.maxrt, self.dbtracker.get_rt())
