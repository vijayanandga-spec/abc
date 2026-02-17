from copy import copy
from apminsight.agentfactory import get_agent


class TxnMetric:

    def __init__(self):
        self.rt = 0
        self.min_rt = 0
        self.max_rt = 0
        self.err_rt = 0
        self.count = 0
        self.err_count = 0
        self.internal_comps = {}
        self.external_comps = {}
        self.db_calls = []
        self.exceptions_info = {}
        self.occurrence = 0

    def accumulate(self, metric):
        self.rt += metric.rt
        self.err_rt += metric.err_rt
        self.count += metric.count
        self.err_count += metric.err_count
        self.aggregate_int_comps(metric.internal_comps)
        self.aggregate_ext_comps(metric.external_comps)
        self.aggregate_exceptions(metric.exceptions_info)
        if self.min_rt == 0 or self.min_rt > metric.min_rt:
            self.min_rt = metric.min_rt

        if self.max_rt == 0 or self.max_rt < metric.max_rt:
            self.max_rt = metric.max_rt

    def update_req_count(self, txn):
        if txn.is_error_txn():
            self.err_count += 1
        else:
            self.count += 1

    def aggregate(self, txn):
        if txn.is_error_txn():
            self.err_count += 1
            self.err_rt += txn.get_rt()
            self.aggregate_txn_sub_resources(txn)
            return
        self.aggregate_non_error_txn(txn)

    def aggregate_non_error_txn(self, txn):
        self.rt += txn.get_rt()
        self.count += 1
        self.aggregate_txn_sub_resources(txn)
        if self.min_rt == 0 or self.min_rt > txn.get_rt():
            self.min_rt = txn.get_rt()

        if self.max_rt == 0 or self.max_rt < txn.get_rt():
            self.max_rt = txn.get_rt()

    def aggregate_txn_sub_resources(self, txn):
        self.db_calls += txn.get_dbcalls()
        self.aggregate_exceptions(txn.get_exceptions_info())
        self.aggregate_int_comps(txn.get_internal_comps())
        self.aggregate_ext_comps(txn.get_external_comps())

    def aggregate_exceptions(self, cur_exc_info={}):
        if len(cur_exc_info) <= 0:
            return

        exc_info = self.exceptions_info.keys()
        for each_error in cur_exc_info.keys():
            if each_error in exc_info:
                self.exceptions_info[each_error] += cur_exc_info[each_error]
            else:
                self.exceptions_info[each_error] = cur_exc_info[each_error]

    def aggregate_int_comps(self, current):
        TxnMetric.aggregate_components(self.internal_comps, current)

    def aggregate_ext_comps(self, current):
        TxnMetric.aggregate_components(self.external_comps, current)

    @staticmethod
    def aggregate_components(base={}, current={}):
        comp_size = len(current)
        if comp_size <= 0:
            return

        for each_comp_index in current.keys():
            cur_comp = current[each_comp_index]
            if each_comp_index in base.keys():
                base_comp = base[each_comp_index]
                base_comp.aggregate(cur_comp)
            else:
                base[each_comp_index] = copy(cur_comp)

    def append_internal_comps(self, comps_list):
        for _, comp in self.internal_comps.items():
            comps_list.append(comp.get_info_as_obj())

    def append_external_comps(self, comps_list):
        for _, comp in self.external_comps.items():
            comps_list.append(comp.get_info_as_obj())

    def get_all_component_details(self):
        comps_list = []
        self.append_internal_comps(comps_list)
        self.append_external_comps(comps_list)
        return comps_list

    def increment_and_get_ocurrence(self):
        self.occurrence += 1
        return self.occurrence

    def get_count(self):
        return self.count

    def get_error_count(self):
        return self.err_count

    def get_rt(self):
        return self.rt

    def get_error_rt(self):
        return self.err_rt

    def get_min_rt(self):
        return self.min_rt

    def get_max_rt(self):
        return self.max_rt

    def get_dbcalls(self):
        return self.db_calls

    def get_internal_comps(self):
        return self.internal_comps

    def get_external_comps(self):
        return self.external_comps

    def get_exceptions_info(self):
        return self.exceptions_info


class WebTxnMetric(TxnMetric):
    def __init__(self):
        super(WebTxnMetric, self).__init__()
        self.satisfied = 0
        self.tolerating = 0
        self.frustrated = 0
        self.error_codes = {}

    def get_satisfied(self):
        return self.satisfied

    def get_tolerated(self):
        return self.tolerating

    def get_frustrated(self):
        return self.frustrated

    def accumulate(self, metric):
        super(WebTxnMetric, self).accumulate(metric)
        if isinstance(metric, BgTxnMetric):
            return
        self.satisfied += metric.satisfied
        self.tolerating += metric.tolerating
        self.frustrated += metric.frustrated
        self.accumulate_errorcodes(metric.error_codes)

    def update_apdex_metric(self, txn):
        threshold = get_agent().get_threshold()
        if txn.get_rt() <= threshold.get_apdex_th() * 1000:
            self.satisfied += 1
        elif txn.get_rt() <= threshold.get_apdex_th() * 4000:
            self.tolerating += 1
        else:
            self.frustrated += 1

    def accumulate_errorcodes(self, errorcodes):
        for each_error_code in errorcodes.keys():
            if each_error_code in self.error_codes:
                self.error_codes[each_error_code] += errorcodes[each_error_code]
            else:
                self.error_codes[each_error_code] = errorcodes[each_error_code]

    def aggregate(self, txn):
        super(WebTxnMetric, self).aggregate(txn)
        if isinstance(txn, BgTxnMetric):
            return
        self.update_apdex_metric(txn)

    def aggregate_errorcode(self, txn):
        if txn.is_error_txn() and txn.get_status_code() >= 400:
            if txn.get_status_code() in self.error_codes:
                self.error_codes[txn.get_status_code()] += 1
            else:
                self.error_codes[txn.get_status_code()] = 1

    def aggregate_txn_sub_resources(self, txn):
        self.aggregate_errorcode(txn)
        super(WebTxnMetric, self).aggregate_txn_sub_resources(txn)

    def get_formatted_data(self, ns=""):
        apdex_score = 0
        if self.get_count() > 0:
            apdex_score = (self.get_satisfied() + (self.get_tolerated() / 2)) / self.get_count()

        apdex_rt_data = [
            self.get_rt(),
            self.get_min_rt(),
            self.get_max_rt(),
            self.get_count(),
            apdex_score,
            self.get_satisfied(),
            self.get_tolerated(),
            self.get_frustrated(),
            self.get_error_count(),
        ]
        additional_metric = {"httpcode": self.error_codes, "error_rt": self.get_error_rt()}
        additional_metric["logmetric"] = self.get_exceptions_info()
        additional_metric["components"] = self.get_all_component_details()
        info_part = {"ns": ns, "name": "apdex"}
        data_part = [apdex_rt_data, additional_metric]
        return [info_part, data_part]


class BgTxnMetric(TxnMetric):
    def __init__(self):
        super(BgTxnMetric, self).__init__()

    def get_formatted_data(self, ns=""):
        rt_data = [self.get_rt(), self.get_min_rt(), self.get_max_rt(), self.get_count(), self.get_error_count()]
        additional_metric = {}
        additional_metric["error_rt"] = self.get_error_rt()
        additional_metric["logmetric"] = self.get_exceptions_info()
        additional_metric["components"] = self.get_all_component_details()
        info_part = {"ns": ns, "name": "bckgrnd"}
        data_part = [rt_data, additional_metric]
        return [info_part, data_part]
