
import unittest

from apminsight.metric.dbtracker import DbTracker
from apminsight.instrumentation.packages.mysql import extract_query

class MockDictCursor:
    def __init__(self, connection):
        self.connection = connection

class MockMysqlConn:
            def __init__(self, host=None, port=None):
                self.host = host
                self.port = port
                
class TestMysql(unittest.TestCase):

    def test_extract_query(self):
        extract_query(None, None, None, None)
        extract_query(None, ['chan'], {}, None)
        query = 'select * from table'
        with self.assertRaises(AttributeError):
            extract_query(None, ['chan', query], {}, None)

        dbtracker = DbTracker()
        extract_query(dbtracker, ['chan', query], {}, None)
        self.assertEqual(dbtracker.get_info()['query'], query)
        extract_query(dbtracker, ['chan', b'select * from table2'], {}, None)
        self.assertEqual(dbtracker.get_info()['query'], 'select * from table2')

        
        connection = MockMysqlConn('myhost',1234)
        extract_query(dbtracker, [MockDictCursor(connection), query], {}, None)
        info = {'query': 'select * from table', 'host' : 'myhost', 'port' : 1234}
        self.assertDictEqual(dbtracker.get_info(), info)
        
