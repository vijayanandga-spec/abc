
import unittest
from apminsight import util

class UtilTest(unittest.TestCase):

    def test_is_non_empty_string(self):
        self.assertEqual(False, util.is_non_empty_string(None))
        self.assertEqual(False, util.is_non_empty_string(4))
        self.assertEqual(False, util.is_non_empty_string(''))
        self.assertEqual(True, util.is_non_empty_string('some'))

    def test_is_empty_string(self):
        self.assertEqual(True, util.is_empty_string(None))
        self.assertEqual(True, util.is_empty_string(4))
        self.assertEqual(True, util.is_empty_string(''))
        self.assertEqual(False, util.is_empty_string('some'))

    def test_is_digit(self):
        self.assertEqual(False, util.is_digit(''))
        self.assertEqual(False, util.is_digit('s'))
        self.assertEqual(False, util.is_digit('90'))
        self.assertEqual(True, util.is_digit('0'))

    def test_get_masked_query(self):
        query = "select * from  table where id=14 and name='chan'"
        expected_query = "select * from  table where id=? and name=?"
        masked_query = util.get_masked_query(query)
        self.assertEqual(masked_query, expected_query)
        
