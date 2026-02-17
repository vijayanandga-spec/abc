
import unittest
from apminsight.metric.tracker import Tracker
from apminsight.metric.component import Component

class ComponentTest(unittest.TestCase):

    intcompname = 'DJANGO'
    inttracker = Tracker({'component' : intcompname})
    inttracker.end_tracker(None)

    intcomp1 = Component(inttracker)
    intcomp2 = Component(inttracker)

    host = 'localhost'
    port = '3306'
    extcompname = 'MYSQL'

    exttracker = Tracker({'component' : extcompname})
    exttracker.set_info({'host': host, 'port' : port})
    exttracker.end_tracker(None)

    extcomp1 = Component(exttracker)
    extcomp2 = Component(exttracker)

    def test_is_same_machine(self):
        status = self.intcomp1.is_same_machine(self.intcomp2)
        self.assertEqual(True, status)
        status = self.extcomp1.is_same_machine(self.extcomp2)
        self.assertEqual(True, status)
        status = self.intcomp1.is_same_machine(self.extcomp2)
        self.assertEqual(False, status)

    def test_get_comp_index(self):
        index = self.intcomp1.get_comp_index()
        self.assertEqual(self.intcomp1.get_name(), index)
        index = self.extcomp1.get_comp_index()
        comp = self.extcomp1
        expected = comp.get_name()+comp.get_host()+comp.get_port()
        self.assertEqual(expected, index)

    def test_get_info_as_obj(self):
        info = self.intcomp1.get_info_as_obj()
        self.assertEqual(0, info['isExt'])
        info = self.extcomp1.get_info_as_obj()
        self.assertEqual(1, info['isExt'])
        self.assertEqual(self.host, info['host'])
        self.assertEqual(self.port, info['port'])

    def test_aggregate(self):
        totalrt = self.extcomp1.get_rt() + self.extcomp2.get_rt()
        self.extcomp1.aggregate(self.extcomp2)
        self.assertEqual(totalrt, self.extcomp1.get_rt())
        self.assertEqual(2, self.extcomp1.get_count())
        self.assertEqual(0, self.extcomp1.get_error_count())

    def test_aggregate_to_global(self):
        res = {}
        comp_index = self.extcomp1.get_comp_index()
        self.extcomp1.aggregate_to_global(res)
        self.assertDictEqual(res, { comp_index : self.extcomp1})

    #def test_check_and_aggregate_component(self):
    #   self.extcomp1.check_and_aggregate_component()