from apminsight.agentfactory import get_agent
from apminsight.logger import agentlogger
from apminsight.metric.apdexmetric import WebTxnMetric, BgTxnMetric
from apminsight.constants import webtxn_prefix, webtxn_type, bgtxn_prefix
from apminsight.util import is_empty_string


class Metricstore:

    def __init__(self):
        self.web_txn_metric = {}
        self.bg_txn_metric = {}
        self.trace_list = []
        self.trace_history = {}
        self.db_call_count = 0
        self.app_metric_sum = {}
        self.app_metric_avg = {}

    def add_txn(self, txn):
        if txn.get_txn_type() == webtxn_type:
            self.add_web_txn(txn)
        else:
            self.add_bg_txn(txn)

    def add_web_txn(self, txn):
        try:
            if txn.is_completed() is not True:
                return False

            occurence = 0
            namespace = webtxn_prefix + txn.get_url()
            match = namespace in self.web_txn_metric
            txn.aggregate_trackers(txn.get_root_tracker())
            if match is not True:
                metric = WebTxnMetric()
                metric.aggregate(txn)
                self.web_txn_metric[namespace] = metric
                self.check_and_include_in_trace(txn)
                return True

            matched_txn = self.web_txn_metric.get(namespace)
            occurence = matched_txn.increment_and_get_ocurrence()
            sampling_factor = get_agent().get_threshold().get_webtxn_sampling_factor()
            if occurence % sampling_factor != 0:
                agentlogger.critical("txn dropped due to sampling factor")
                return False

            metric_limit = get_agent().get_threshold().get_apdex_metric_size()
            if len(self.web_txn_metric) <= metric_limit:
                matched_txn = self.web_txn_metric.get(namespace)
                matched_txn.aggregate(txn)
                self.web_txn_metric[namespace] = matched_txn

            self.check_and_include_in_trace(txn)
            return True

        except Exception:
            agentlogger.exception("unable to add web txn")
        return False

    def add_bg_txn(self, txn):
        try:
            if txn.is_completed() is not True:
                return False

            occurence = 0
            namespace = bgtxn_prefix + txn.get_url()
            match = namespace in self.bg_txn_metric

            if match is not True:
                metric = BgTxnMetric()
                metric.aggregate(txn)
                self.bg_txn_metric[namespace] = metric
                self.check_and_include_in_trace(txn)
                return True

            matched_txn = self.bg_txn_metric.get(namespace)

            metric_limit = get_agent().get_threshold().get_bg_metric_size()
            if len(self.bg_txn_metric) <= metric_limit:
                matched_txn = self.bg_txn_metric.get(namespace)
                matched_txn.aggregate(txn)
                self.bg_txn_metric[namespace] = matched_txn

            self.check_and_include_in_trace(txn)
            return True

        except Exception:
            agentlogger.exception("unable to add web txn")
        return False

    def is_critical(self, txn):
        # external call count need to be considered
        txn_info = (
            txn.get_url() + "-" + txn.get_http_request_method() if txn.get_txn_type == webtxn_type else txn.get_url()
        )
        last_critically_collected = self.trace_history.get(txn_info, None)
        critical = False
        if last_critically_collected is None:
            collected_info = {}
            collected_info["rt"] = txn.get_rt()
            collected_info["exceptioncount"] = txn.get_exceptions_count()
            self.trace_history[txn_info] = collected_info
            critical = True
        else:
            if last_critically_collected["exceptioncount"] < txn.get_exceptions_count():
                last_critically_collected["exceptioncount"] = txn.get_exceptions_count()
                critical = True

            if last_critically_collected["rt"] < txn.get_rt():
                last_critically_collected["rt"] = txn.get_rt()
                critical = True

        return critical

    def check_and_include_in_trace(self, txn):
        threshold = get_agent().get_threshold()

        if txn.get_txn_type() == webtxn_type:
            if threshold.is_trace_enabled() is not True:
                return False
        else:
            if threshold.is_bgtxn_trace_enabled() is not True:
                return False

        if len(self.trace_list) > threshold.get_trace_metric_size():
            return False

        trace_reason = 0x0000

        if txn.get_txn_type() == webtxn_type:

            if txn.get_rt() >= threshold.get_trace_threshold():
                trace_reason |= 0x0008

        elif txn.get_rt() >= threshold.get_bgtxn_trace_threshold():
            trace_reason |= 0x0008

        if txn.get_exceptions_count() > 0:
            trace_reason |= 0x0010

        if trace_reason > 0 and self.is_critical(txn):
            self.trace_list.append(txn)
            return True

        return False

    def get_formatted_data(self):
        formatted_data = []
        ins_dbmetric = {}
        opn_dbmetric = {}
        web_instance_metric = WebTxnMetric()
        bg_instance_metric = BgTxnMetric()

        for txn_namespace in self.web_txn_metric.keys():
            txnmetric = self.web_txn_metric[txn_namespace]
            txn_data = txnmetric.get_formatted_data(ns=txn_namespace)
            formatted_data.append(txn_data)
            web_instance_metric.accumulate(txnmetric)

            txn_dbmetric = {}
            for dbtracker in txnmetric.get_db_calls():
                info = dbtracker.get_info()
                opn = info.get("opn", "")
                obj = info.get("obj", "")
                if is_empty_string(opn) or is_empty_string(obj):
                    continue

                dbtracker.accumulate("db/" + opn + "/" + obj + "/dummy-db", txn_dbmetric)
                dbtracker.accumulate("db/" + opn + "/all/dummy-db", opn_dbmetric)
                dbtracker.accumulate("db/all/all/dummy-db", ins_dbmetric)

            Metricstore.iter_and_append_dbmetric(formatted_data, txn_dbmetric, ns=txn_namespace)

        for txn_namespace in self.bg_txn_metric.keys():
            txnmetric = self.bg_txn_metric[txn_namespace]
            txn_data = txnmetric.get_formatted_data(ns=txn_namespace)
            formatted_data.append(txn_data)
            bg_instance_metric.accumulate(txnmetric)

            txn_dbmetric = {}
            for dbtracker in txnmetric.get_dbcalls():
                info = dbtracker.extract_operartion_info()
                opn = info.get("opn", "")
                obj = info.get("obj", "")
                if is_empty_string(opn) or is_empty_string(obj):
                    continue

                dbtracker.accumulate("db/" + opn + "/" + obj + "/dummy-db", txn_dbmetric)
                dbtracker.accumulate("db/" + opn + "/all/dummy-db", opn_dbmetric)
                dbtracker.accumulate("db/all/all/dummy-db", ins_dbmetric)

            Metricstore.iter_and_append_dbmetric(formatted_data, txn_dbmetric, ns=txn_namespace)

        if len(self.web_txn_metric) > 0 or len(self.bg_txn_metric) > 0:
            Metricstore.iter_and_append_dbmetric(formatted_data, opn_dbmetric)
            Metricstore.iter_and_append_dbmetric(formatted_data, ins_dbmetric)
        if len(self.web_txn_metric) > 0:
            formatted_data.append(web_instance_metric.get_formatted_data())
        if len(self.bg_txn_metric) > 0:
            formatted_data.append(web_instance_metric.get_formatted_data())

        return formatted_data

    @staticmethod
    def iter_and_append_dbmetric(formatted_data, dbmetrics, ns=""):
        for opn_index in dbmetrics.keys():
            dbmetric = dbmetrics[opn_index]
            info = {"ns": ns, "name": opn_index}
            data = dbmetric.get_formatted_dbmetric()
            formatted_data.append([info, data])

    def get_formatted_trace(self):
        formatted_trace = []
        for eachtxn in self.trace_list:
            formatted_trace.append(eachtxn.get_trace_data())

        return formatted_trace

    def cleanup(self):
        self.web_txn_metric = {}
        self.bg_txn_metric = {}
        self.trace_list = []
        self.trace_history = {}
        self.db_call_count = 0
        self.app_metric_sum = {}
        self.app_metric_avg = {}

    def get_webtxn_metric(self):
        return self.web_txn_metric

    def get_bgtxn_metric(self):
        return self.bg_txn_metric

    def get_trace_list(self):
        return self.trace_list

    def get_db_call_count(self):
        return self.db_call_count

    def get_app_metric_sum(self):
        return self.app_metric_sum

    def get_app_metric_avg(self):
        return self.app_metric_avg
