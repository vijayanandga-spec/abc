
import unittest
from apminsight.agentfactory import get_agent
from apminsight.collector.reshandler import handle_connect_response, handle_data_response

res_data = { 
    'data' : { 
        'instance-info':{
            'instanceid': 'chan'
        },
        'response-code' : 701
        }
    }

class ResHandlerTest(unittest.TestCase):

    def test_handle_connect_response(self):
        self.assertFalse(handle_connect_response('chan'))
        self.assertFalse(handle_connect_response({}))
        self.assertFalse(handle_connect_response({'data': 'nothing'}))
        self.assertTrue(handle_connect_response(res_data))
        self.assertEqual(701, get_agent().get_ins_info().get_status())
        get_agent().get_ins_info().status = None        


    def test_handle_data_response(self):
        self.assertFalse(handle_data_response('chan'))
        self.assertFalse(handle_data_response({}))
        self.assertFalse(handle_data_response({'data': 'nothing'}))
        self.assertTrue(handle_data_response(res_data))
        self.assertEqual(701, get_agent().get_ins_info().get_status())
        get_agent().get_ins_info().status = None
        

    
