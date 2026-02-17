
import unittest

from apminsight.metric.dbtracker import DbTracker
from apminsight.instrumentation.packages.pymemcache import extract_info

class MockPymemcacheClient:
    def __init__(self, server):
        self.server = server

class TestPymemcache(unittest.TestCase):

    def test_extract_info(self):

        extract_info(None, None, None, None)
        extract_info(None, ['tall'], {}, None)
        query = 'SET'
        with self.assertRaises(AttributeError):
            extract_info(None, ['tall', query], {}, None)

        dbtracker = DbTracker()
        extract_info(dbtracker, ['tall', query], {}, None)
        self.assertEqual(dbtracker.get_info()['opn'], query)
        extract_info(dbtracker, ['tall', b'SET'], {}, None)
        self.assertEqual(dbtracker.get_info()['opn'], 'SET')

        extract_info(dbtracker, [MockPymemcacheClient(('myhost',1234)), query], {}, None)
        info = {'opn': 'SET', 'host' : 'myhost', 'port' : 1234}
        self.assertDictEqual(dbtracker.get_info(), info)