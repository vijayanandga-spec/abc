
import unittest
from apminsight.collector.rescodes import is_valid_rescode, get_rescode_message
from apminsight.collector.rescodes import is_allowed_to_send_request
from apminsight.collector.rescodes import is_retry_limit_exceeded
from apminsight.collector.rescodes import get_retry_counter
from apminsight.util import current_milli_time

rescodes = {
    701 : 'LICENSE_EXPIRED',
    702 : 'LICENSE_INSTANCES_EXCEEDED',
    703 : 'INSTANCE_ADD_FAILED',
    704 : 'INSUFFICIENT_CREDITS',
    900 : 'MARKED_FOR_DELETE',
    901 : 'INVALID_AGENT',
    910 : 'UNMANAGE_AGENT',
    911 : 'MANAGE_AGENT',
    0 : 'SHUTDOWN'
}

class RescodesTest(unittest.TestCase):

    def test_is_valid_rescode(self):
        for each in rescodes.keys():
            self.assertTrue(is_valid_rescode(each))
        
        self.assertFalse(is_valid_rescode(700))

    def test_get_rescode_message(self):
        for each in rescodes.keys():
            self.assertEqual(get_rescode_message(each), rescodes[each])

        self.assertEqual(500, 500)

    def test_is_allowed_to_send_request(self):
        self.assertTrue(is_allowed_to_send_request(None, None))
        self.assertTrue(is_allowed_to_send_request(701, None))
        self.assertFalse(is_allowed_to_send_request(701, 11))
        self.assertTrue(is_allowed_to_send_request(701, 12))
        self.assertFalse(is_allowed_to_send_request(701, 3*24*60+1))
        self.assertFalse(is_allowed_to_send_request(703, 31))
        self.assertTrue(is_allowed_to_send_request(703, 25))

    def test_is_retry_limit_exceeded(self):
        self.assertFalse(is_retry_limit_exceeded(None, None))
        self.assertFalse(is_retry_limit_exceeded(701, None))
        self.assertFalse(is_retry_limit_exceeded(100, None))
        self.assertFalse(is_retry_limit_exceeded("701", None))
        self.assertFalse(is_retry_limit_exceeded(910, 20))
        self.assertTrue(is_retry_limit_exceeded(900, 3*24*60))
        self.assertTrue(is_retry_limit_exceeded(901, 3*24*60))
        self.assertTrue(is_retry_limit_exceeded(701, 15*24*60))
        self.assertTrue(is_retry_limit_exceeded(702, 15*24*60))

        
    def test_get_retry_count(self):
        self.assertEqual(1, get_retry_counter(None, 1))
        self.assertEqual(1, get_retry_counter(700, None))
        self.assertEqual(1, get_retry_counter(500, 1))
        self.assertEqual(1, get_retry_counter(910, 1))
        self.assertEqual(1, get_retry_counter(911, 1))
        self.assertEqual(1, get_retry_counter(704, 1))
        time = current_milli_time() - 2*60*1000
        self.assertEqual(2, get_retry_counter(701, time))

    




