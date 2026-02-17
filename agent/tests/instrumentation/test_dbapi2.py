
import unittest
from apminsight.instrumentation.dbapi2 import ConnectionProxy, CursorProxy
from apminsight.metric.dbtracker import DbTracker
from apminsight.metric.txn import Transaction
from apminsight.context import set_cur_txn, clear_cur_context

class MockCursor():

    def execute(self, *args, **kwargs):
        return "executed"

class MockConn():

    def cursor(self, *args, **kwargs):
        return MockCursor()


def connect(*args, **kwargs):
    return MockConn()

class TestSqlite(unittest.TestCase):

    def test_instrument_conn(self):
        method_info = {'method':'query', 'component' : 'something'}
        wrapper = ConnectionProxy.instrument_conn(connect, 'dbapi2', method_info)
        conn = wrapper(host='test', port=1611)
        self.assertTrue(isinstance(conn, ConnectionProxy))
        cursor = conn.cursor()
        query = 'select * from mytable'
        self.assertTrue(isinstance(cursor, CursorProxy))
        self.assertEqual(cursor.execute(query), "executed")
        txn = Transaction()
        set_cur_txn(txn)
        self.assertEqual(cursor.execute(query), "executed")
        dbtracker = txn.get_db_calls()[0]
        info = dbtracker.get_info()
        self.assertEqual(info['query'], query)
        self.assertEqual(info['host'], 'test')
        self.assertEqual(info['port'], 1611)
        self.assertEqual(dbtracker.get_component(), 'something')
        clear_cur_context()

