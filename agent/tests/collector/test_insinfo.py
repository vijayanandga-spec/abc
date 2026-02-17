
import unittest
from apminsight.collector.ins_info import Instanceinfo

class TestInsInfo(unittest.TestCase):

    def test_get_info_file_path(self):
        self.assertEqual(None, Instanceinfo.get_info_file_path())
        self.assertEqual(None, Instanceinfo.get_info_file_path({}))
        self.assertEqual(None, Instanceinfo.get_info_file_path({'agentbasedir': None}))
        self.assertEqual("/chan/apminsight.json", Instanceinfo.get_info_file_path({'agentbasedir': '/chan'}))

    def test_update_status(self):
        insinfo = Instanceinfo({'instanceid':'chandhru', 'status'  : 701})
        insinfo.update_status(700)
        self.assertEqual(insinfo.get_status(), 701)
        insinfo.retry_counter = (15*24*60) - 2
        insinfo.update_status(701)
        self.assertEqual(insinfo.get_status(), 701)
        insinfo.retry_counter = 15*24*60
        insinfo.update_status(701)
        self.assertEqual(insinfo.get_status(), 0)

    def test_update_instance_info(self):
        insinfo = Instanceinfo()
        insinfo.update_instance_info('chan', None)
        self.assertEqual(insinfo.get_instance_id(), 'chan')
        self.assertEqual(insinfo.get_status(), 911)
        insinfo.update_instance_info('chan', 700)
        self.assertEqual(insinfo.get_instance_id(), 'chan')
        self.assertEqual(insinfo.get_status(), 700)  
        insinfo.update_instance_info('chan', 701)
        self.assertEqual(insinfo.get_instance_id(), 'chan')
        self.assertEqual(insinfo.get_status(), 701)

    def test_get_as_json(self):
        insinfo = Instanceinfo()
        info = insinfo.get_as_json()
        self.assertTrue(type(info['instanceId']) is str)
        self.assertTrue(info['status'] is None)
        self.assertTrue(type(info['time']) is int)
        insinfo = Instanceinfo({'instanceid':'chandhru', 'status'  : 700})
        info = insinfo.get_as_json()
        self.assertTrue(info['instanceId'] == 'chandhru')
        self.assertTrue(info['status'] == 700)
        self.assertTrue(type(info['time']) is int)


    

    


