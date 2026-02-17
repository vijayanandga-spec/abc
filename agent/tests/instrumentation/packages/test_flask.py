
import unittest

from apminsight.instrumentation.packages.flask import get_status_code

class TestFlask(unittest.TestCase):

    def test_get_status_code(self):
        wrapper = get_status_code(mock_flask_method, None, None)
        self.assertEqual(wrapper(), "flask")

        from apminsight.metric.txn import Transaction
        from apminsight.context import set_cur_txn
        txn = Transaction()
        set_cur_txn(txn)
        wrapper = get_status_code(mock_flask_method, None, None)
        self.assertEqual(wrapper(), "flask")

        wrapper = get_status_code(mock_flask_exception, None, None)
        wrapper()
        self.assertEqual(txn.get_status_code(), 403)

def mock_flask_exception():
    from werkzeug.exceptions import Forbidden
    exc =Forbidden()
    return exc

def mock_flask_method():
    return "flask"