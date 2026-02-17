
import unittest

from apminsight.metric.dbtracker import DbTracker
from apminsight.instrumentation.packages.cassandra import extract_query

class MockResponseFuture:
    def __init__(self, coordinator_host):
        self.coordinator_host = ':'.join(coordinator_host)

class MockReturnValue:
    def __init__(self, response_future):
        self.response_future = response_future

class TestCassandra(unittest.TestCase):

    def test_extract_query(self):

        extract_query(None, None, None, None)
        extract_query(None, ['tall'], {}, None)
        query = 'select * from table'
        with self.assertRaises(AttributeError):
            extract_query(None, ['tall', query], {}, None)

        dbtracker = DbTracker()
        extract_query(dbtracker, ['tall', query], {}, None)
        self.assertEqual(dbtracker.get_info()['query'], query)
        extract_query(dbtracker, ['tall', b'select * from table2'], {}, None)
        self.assertEqual(dbtracker.get_info()['query'], 'select * from table2')

        r_f = MockResponseFuture(('myhost','1234'))
        extract_query(dbtracker, ['tall', query], {}, MockReturnValue(r_f))
        info = {'query': 'select * from table', 'host' : 'myhost', 'port' : 1234}
        self.assertDictEqual(dbtracker.get_info(), info)