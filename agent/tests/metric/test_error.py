
import unittest
from apminsight.metric.error import ErrorInfo

class ErrorInfoTest(unittest.TestCase):

    def test_get_type(self):
        errinfo = None
        try:
            raise RuntimeError('TESTERROR')
        except Exception as exc:
            errinfo = ErrorInfo(exc)

        self.assertEqual('RuntimeError', errinfo.get_type())
        self.assertEqual('TESTERROR', errinfo.get_message())


    
