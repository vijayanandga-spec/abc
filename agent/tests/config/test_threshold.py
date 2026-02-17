
import unittest
from apminsight.config.threshold import Threshold
from apminsight import constants

custom_config = {}
custom_config[constants.apdexth] = 0.7
custom_config[constants.sql_parametrize] = False
custom_config[constants.last_modified_time] = 1576059127363
custom_config[constants.trace_threshold] = 0
custom_config[constants.trace_size] = 60
custom_config[constants.bg_metric] = 50
custom_config[constants.sql_stracktrace] = 5
custom_config[constants.db_metric] = 100
custom_config[constants.sql_capture] = False
custom_config[constants.trace_enabled] = False

agent_specific_info = {}
agent_specific_info[constants.log_level] = 'INFO'
agent_specific_info[constants.bgtxn_traceth] = 2
agent_specific_info[constants.bgtxn_sampling_factor] = 4
agent_specific_info[constants.bgtxn_trace_enabled] = False
agent_specific_info[constants.bgtxn_tracking_enabled] = False

class ThresholdTest(unittest.TestCase):

    threshold = Threshold()
    threshold.update(custom_config, agent_specific_info)

    def test_is_txn_allowed(self):
        threshold = Threshold()
        self.assertTrue(threshold.is_txn_allowed('/api/list'))
        self.assertFalse(threshold.is_txn_allowed(''))
        self.assertFalse(threshold.is_txn_allowed('/styles.css'))
        self.assertFalse(threshold.is_txn_allowed('/load.js'))

    def test_update_txn_skip_listening(self):
        threshold = Threshold()
        threshold.update_txn_skip_listening('*.chan')
        self.assertListEqual(threshold.get_txn_skip_listening(), ['.chan'])
        self.assertFalse(threshold.is_txn_allowed('/nothing.chan'))
        self.assertTrue(threshold.is_txn_allowed('/load.js'))

    def test_update(self):
        self.assertTrue(custom_config.items() <= self.threshold.thresholdmap.items())
        self.assertTrue(agent_specific_info.items() <= self.threshold.thresholdmap.items())

    def test_get_trace_threshold(self):
        self.assertEqual(self.threshold.get_trace_threshold(), custom_config[constants.trace_threshold]*1000)

    def test_get_sql_trace_threshold(self):
        self.assertEqual(self.threshold.get_sql_trace_threshold(), custom_config[constants.sql_stracktrace]*1000)

    def test_get_bgtxn_trace_threshold(self):
        self.assertEqual(self.threshold.get_bgtxn_trace_threshold(), agent_specific_info[constants.bgtxn_traceth]*1000)
