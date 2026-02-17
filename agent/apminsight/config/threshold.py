import re
import apminsight.constants as constants
from apminsight.logger import agentlogger
from apminsight.util import current_milli_time, is_empty_string, is_non_empty_string


class Threshold:

    def __init__(self):
        self.thresholdmap = {}
        self.last_modified = current_milli_time()

    def update_sql_trace_threshold(self, sql_trace_threshold):
        if sql_trace_threshold is not None and isinstance(sql_trace_threshold, int):
            self.thresholdmap[constants.sql_stacktrace] = float(sql_trace_threshold)

    def update_sql_capture_enabled(self, sql_capture_enabled):
        if is_non_empty_string(sql_capture_enabled):
            self.thresholdmap[constants.sql_capture] = True if sql_capture_enabled else False

    def update(self, custom_config, agent_specific):
        try:
            if custom_config is not None:
                self.thresholdmap.update(custom_config)

            if agent_specific is not None:
                self.thresholdmap.update(agent_specific)

            configured_str = self.thresholdmap.get(constants.txn_skip_listening, "")
            self.update_txn_skip_listening(configured_str)
        except Exception:
            agentlogger.exception("updating threshold")

    def update_txn_skip_listening(self, configured_str):
        try:
            if is_empty_string(configured_str):
                self.thresholdmap[constants.txn_skip_listening] = []
                return

            configured_str = re.sub(r"(\*|\s)*", "", configured_str)
            config_array = configured_str.split(",")
            self.thresholdmap[constants.txn_skip_listening] = config_array
        except Exception:
            agentlogger.exception("update skip txn")

    def is_txn_allowed(self, uri):
        if is_empty_string(uri):
            return False

        index = uri.rfind(".")
        if index < 0:
            return True

        extension = uri[index:]
        if extension in self.get_txn_skip_listening():
            return False

        return True

    def get_apdex_th(self):
        return self.thresholdmap.get(constants.apdexth, 0.5)

    def is_sql_capture_enabled(self):
        return self.thresholdmap.get(constants.sql_capture, True)

    def get_webtxn_sampling_factor(self):
        if constants.web_txn_sampling_factor in self.thresholdmap:
            factor = self.thresholdmap.get(constants.web_txn_sampling_factor)
            if type(factor) is int and factor > 0:
                return factor

        return 1

    def get_bgtxn_sampling_factor(self):
        return self.thresholdmap.get(constants.bgtxn_sampling_factor, 1)

    def is_trace_enabled(self):
        return self.thresholdmap.get(constants.trace_enabled, True)

    def get_trace_threshold(self):
        th_seconds = self.thresholdmap.get(constants.trace_threshold, 2)
        return th_seconds * 1000

    def get_sql_trace_threshold(self):
        th_seconds = self.thresholdmap.get(constants.sql_stacktrace, 3)
        return th_seconds * 1000

    def is_sql_parameterized(self):
        return self.thresholdmap.get(constants.sql_parametrize, True)

    def get_last_modified_time(self):
        return self.thresholdmap.get(constants.last_modified_time, self.last_modified)

    def get_apdex_metric_size(self):
        return self.thresholdmap.get(constants.apdex_metric, 250)

    def get_db_metric_size(self):
        return self.thresholdmap.get(constants.db_metric, 500)

    def get_bg_metric_size(self):
        return self.thresholdmap.get(constants.bg_metric, 100)

    def get_trace_metric_size(self):
        return self.thresholdmap.get(constants.trace_size, 30)

    def get_log_level(self):
        return self.thresholdmap.get(constants.log_level, "DEBUG")

    def get_txn_skip_listening(self):
        return self.thresholdmap.get(
            constants.txn_skip_listening, [".css", ".js", ".gif", ".jpg", ".jpeg", ".bmp", ".png", ".ico"]
        )

    def get_txn_tracker_drop_threshold(self):
        return self.thresholdmap.get(constants.txn_tracker_drop_th, 10)

    def get_txn_trace_extcall_threshold(self):
        return self.thresholdmap.get(constants.txn_trace_ext_count_th, 30)

    def is_bgtxn_tracking_enabled(self):
        return self.thresholdmap.get(constants.bgtxn_tracking_enabled, True)

    def is_bgtxn_trace_enabled(self):
        return self.thresholdmap.get(constants.bgtxn_trace_enabled, True)

    def get_bgtxn_trace_threshold(self):
        th_seconds = self.thresholdmap.get(constants.bgtxn_traceth, 5)
        return th_seconds * 1000
