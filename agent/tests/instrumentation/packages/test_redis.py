
import unittest
from apminsight.metric.tracker import Tracker
from apminsight.context import set_cur_tracker, clear_cur_context
from apminsight.instrumentation.packages.redis import extract_info
from apminsight.instrumentation.packages.redis import wrap_send_command

class MockRedisConn:

    def __init__(self, host, port):
        self.host = host
        self.port = port


class TestRedis(unittest.TestCase):

    @staticmethod
    def mock_method(conn=None, opn=None):
        return "mock_method"

    def test_wrap_send_command(self):
        wrapper = wrap_send_command(TestRedis.mock_method, 'test', None)
        self.assertEqual(wrapper(), "mock_method")
        tracker = Tracker({'component' : 'REDIS'})
        set_cur_tracker(tracker)
        wrapper(MockRedisConn('test', 3000), 'GET')
        info = {'opn': 'GET', 'host' : 'test', 'port' : 3000}
        self.assertDictEqual(tracker.get_info(), info)
        clear_cur_context()

    def test_extract_info(self):
        tracker = Tracker()
        extract_info(None, None)
        extract_info(tracker, None)
        extract_info(tracker, (MockRedisConn('chan', 3372), 'SET'))
        self.assertDictEqual(tracker.get_info(), {})
        tracker.set_component('REDIS')
        extract_info(tracker, (MockRedisConn('chan', 2754), 'SET'))
        info = {'opn': 'SET', 'host' : 'chan', 'port' : 2754}
        self.assertDictEqual(tracker.get_info(), info)



