import time
import asyncio
from urllib import parse
from abc import abstractmethod
from apminsight import constants
from apminsight.util import current_milli_time, is_empty_string, remove_null_keys
from apminsight.metric.tracker import Tracker
from apminsight.metric.dbtracker import DbTracker
from apminsight.agentfactory import get_agent
from apminsight.metric.component import Component
from apminsight.logger import agentlogger
from apminsight.constants import TxnSpecificConfig


class Transaction:

    def __init__(self, root_tracker_info={}, txn_config=None):
        self.__root_tracker = Tracker(root_tracker_info)
        self.__start_time = current_milli_time()
        self.__end_time = None
        self.__rt = 0
        self.__completed = False
        self.__exceptions_info = {}
        self.__exceptions_count = 0
        self.__external_comps = {}
        self.__internal_comps = {}
        self.__extcall_count = 0
        self.__db_calls = []
        self.__method_count = 1
        self.__trace_id = root_tracker_info.get(constants.CONTEXT).get(constants.TRACE_ID_STR)
        self.__custom_params = None
        self.__cpu_start_time = int(time.thread_time_ns() / 1000000)
        self.__cpu_end_time = None
        self.__trackers = {self.__root_tracker.get_span_id(): self.__root_tracker}
        self.__dt_response_headers = None
        self.__dt_count = 0
        self.__dt_req_headers_injected = False
        self.__dt_response_headers_processed = None
        self._txn_config = TxnConfig(txn_config)
        self._asynchronous = 0
        self._custom_name = None
        self._ignore_txn = False

        # Setting root tracker to priority 1 for all traces capturing
        self.__root_tracker.set_priority()

    def get_trackers(self):
        return self.__trackers

    def get_tracker(self, span_id):
        return self.__trackers.get(span_id)

    def add_tracker(self, tracker):
        self.__trackers[tracker.get_span_id()] = tracker

    def end_txn(self, res=None, err=None):
        try:
            if self._ignore_txn or self.is_completed():
                return
            agent = get_agent()
            self.__root_tracker.end_tracker(err)
            self.__end_time = current_milli_time()
            self.__rt = self.__end_time - self.__start_time
            self.__completed = True
            self.__cpu_end_time = int(time.thread_time_ns() / 1000000)
            if agent.get_config().is_using_exporter():
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                task = loop.create_task(agent.get_metric_dispatcher().construct_payload(self._create_txn_payload))
                if not loop.is_running():
                    loop.run_until_complete(asyncio.gather(task))
            else:
                agent.push_to_queue(self)
        except:
            agentlogger.exception("in end_txn")

    def _create_txn_payload(self, transaction_info={}):
        from apminsight import get_agent

        transaction_info[constants.exporter_param_key_request_url] = self.get_txn_name()
        transaction_info[constants.exporter_param_key_transaction_duration] = self.get_rt()
        transaction_info[constants.exporter_param_key_bytes_in] = None
        transaction_info[constants.exporter_param_key_bytes_out] = None
        transaction_info[constants.exporter_param_key_transaction_type] = self.get_txn_type()
        transaction_info[constants.exporter_param_key_distributed_count] = self.get_dt_count()
        transaction_info[constants.exporter_param_key_thread_id] = None
        transaction_info[constants.exporter_param_key_collection_time] = self.get_start_time()
        transaction_info[constants.exporter_param_key_collection_end_time] = self.get_end_time()
        transaction_info[constants.exporter_param_key_cpu_time] = self.get_cpu_time()
        transaction_info[constants.exporter_param_key_memory_usage] = None
        transaction_info[constants.exporter_param_key_trace_id] = self.get_trace_id()
        transaction_info[constants.exporter_param_key_custom_params] = None
        transaction_info[constants.exporter_param_key_async] = self._asynchronous
        transaction_info[constants.exporter_param_key_custom_params] = self.get_custom_params()
        return self._create_final_payload(transaction_info)

    def _create_final_payload(self, transaction_info):
        remove_null_keys(transaction_info)
        method_info = self.__add_trackers()
        txn_payload = {
            "apm": {
                constants.data_str: True,
                "application_info": {
                    constants.exporter_param_key_application_type: constants.python_comp,
                    constants.exporter_param_key_application_name: get_agent().get_config().get_app_name(),
                    constants.exporter_param_key_instance_id: get_agent().get_ins_info().get_instance_id(),
                },
                constants.transaction_info_str: transaction_info,
                constants.method_info_str: {"span_info": method_info},
            }
        }
        return txn_payload

    def handle_end_tracker(self, tracker):
        self.aggregate_component(tracker)
        self.check_and_add_db_call(tracker)
        self.check_and_add_error(tracker)

    def aggregate_component(self, tracker):
        if is_empty_string(tracker.get_component()):
            return

        component = Component(tracker)
        if component.is_ext():
            component.aggregate_to_global(self.__external_comps)
            self.__extcall_count += component.get_count() + component.get_error_count()
        else:
            component.aggregate_to_global(self.__internal_comps)

    def check_and_add_db_call(self, db_tracker):
        if isinstance(db_tracker, DbTracker):
            self.__db_calls.append(db_tracker)

    def check_and_add_error(self, tracker):
        if not tracker.is_error():
            return

        err_name = tracker.get_error_name()
        if is_empty_string(err_name):
            return

        err_count = self.__exceptions_info.get(err_name, 0)
        self.__exceptions_info[err_name] = err_count + 1
        self.__exceptions_count += 1

    @staticmethod
    def comp_details_for_trace(allcompinfo):
        comp_details = {"success": {}, "fail": {}}
        for eachcomp in allcompinfo.keys():
            compinfo = allcompinfo[eachcomp]
            if compinfo.get_name() in comp_details["success"].keys():
                comp_details["success"][compinfo.get_name()] += compinfo.get_count()
                comp_details["fail"][compinfo.get_name()] += compinfo.get_error_count()
            else:
                comp_details["success"][compinfo.get_name()] = compinfo.get_count()
                comp_details["fail"][compinfo.get_name()] = compinfo.get_error_count()

        return comp_details

    def __add_trackers(self):
        method_info = []
        for tracker in self.__trackers.values():
            method_info.append(tracker.add_tracker_data())
        return method_info

    def get_trace_info(self):
        trace_info = {}
        trace_info["t_name"] = self.get_txn_prefix() + self.get_txn_name()
        trace_info["s_time"] = self.get_start_time()
        trace_info["r_time"] = self.get_rt()
        if self.get_txn_type() == 1:
            trace_info["http_query_str"] = self.get_query_string()
            trace_info["http_input_params"] = self.get_http_input_params()
            trace_info["http_method_name"] = self.get_http_request_method()
            if self.get_status_code() is not None:
                trace_info["httpcode"] = self.get_status_code()
        trace_info["trace_reason"] = 4
        trace_info["db_opn"] = []
        trace_info["loginfo"] = []
        trace_info["method_count"] = self.get_method_count()
        trace_info["dt_count"] = self.__dt_count
        trace_info["ext_components"] = Transaction.comp_details_for_trace(self.__external_comps)
        trace_info["int_components"] = Transaction.comp_details_for_trace(self.__internal_comps)

        return trace_info

    def get_trace_data(self):
        trace_info = self.get_trace_info()
        trace_data = self.__root_tracker.get_tracker_data_for_trace(trace_info)
        return [trace_info, trace_data]

    def get_method_count(self):
        return self.__method_count

    def increment_method_count(self, count):
        if isinstance(count, int):
            self.__method_count += count

    def get_root_tracker(self):
        return self.__root_tracker

    @abstractmethod
    def get_txn_name(self):
        pass

    def get_rt(self):
        return self.__rt

    def set_rt(self, rt):
        if isinstance(rt, int):
            self.__rt = rt

    def get_start_time(self):
        return self.__start_time

    def get_end_time(self):
        return self.__end_time

    def get_exceptions_info(self):
        return self.__exceptions_info

    def get_exceptions_count(self):
        return self.__exceptions_count

    def set_exceptions_count(self, count):
        if isinstance(count, int):
            self.__exceptions_count = count

    def clear_db_calls(self):
        self.__db_calls = []

    def get_db_calls(self):
        return self.__db_calls

    def update_db_calls(self, db_calls):
        if isinstance(db_calls, list):
            self.__db_calls += db_calls

    def get_internal_comps(self):
        return self.__internal_comps

    def get_external_comps(self):
        return self.__external_comps

    def get_ext_call_count(self):
        return self.__extcall_count

    def is_completed(self):
        return self.__completed

    def get_trace_id(self):
        return self.__trace_id

    def get_cpu_time(self):
        if self.__cpu_end_time:
            return self.__cpu_end_time - self.__cpu_start_time
        else:
            return None

    def set_custom_params(self, key, value):

        if self.__custom_params is None:
            self.__custom_params = {key: [value]}
        elif len(self.__custom_params) > 10:
            return
        elif self.__custom_params.get(key):
            if len(self.__custom_params[key]) < 10:
                self.__custom_params[key].append(value)
        else:
            self.__custom_params[key] = [value]

    def get_custom_params(self):
        return self.__custom_params

    def get_dt_count(self):
        return self.__dt_count

    def increment_dt_count(self):
        self.__dt_count += 1

    def get_dt_response_headers(self):
        return self.__dt_response_headers

    def set_dt_response_headers(self, resp_headers):
        self.__dt_response_headers = resp_headers

    def dt_req_headers_injected(self, flag=None):
        if flag:
            self.__dt_req_headers_injected = flag
        return self.__dt_req_headers_injected

    def is_dt_response_headers_processed(self):
        return self.__dt_response_headers_processed

    def dt_response_headers_processed(self):
        self.__dt_response_headers_processed = True

    def get_txn_config(self):
        return self._txn_config

    def aggregate_trackers(self, tracker):
        for child_tracker in tracker.get_child_trackers():
            self.aggregate_trackers(child_tracker)
        self.handle_end_tracker(tracker)

    def get_sql_stacktrace_threshold(self):
        return self._txn_config.get_sql_stacktrace_threshold()

    def get_normalized_txn_name(self):
        normalized_url = self._txn_config.get_normalized_url()
        if normalized_url:
            return normalized_url
        return self.get_txn_name()
    
    def get_async_index(self):
        return self._asynchronous

    def set_async_index(self, async_index):
        self._asynchronous = async_index

    def is_error_txn(self):
        return self.__root_tracker.is_error()

    def set_custom_name(self, custom_name: str) -> None:
        self._custom_name = custom_name

    def ignore_txn(self):
        self._ignore_txn = True
        agentlogger.info(f"Txn ignored for {self.get_txn_name()}")


class WebTxn(Transaction):
    def __init__(self, wsgi_environ={}, root_tracker_info={}, txn_config=None):
        self.__url = wsgi_environ.get(constants.path_info_str, str())
        self.__query = wsgi_environ.get(constants.query_string_str, str())
        self.__http_input_params = self.get_request_params()
        self.__http_request_method = wsgi_environ.get(constants.request_method_str, str())
        self.__status_code = 200
        self._http_host = wsgi_environ.get(constants.HTTP_HOST, None) or wsgi_environ.get(constants.HTTP, None)
        super().__init__(root_tracker_info, txn_config)

    def get_txn_name(self):
        if self._custom_name:
            return self._custom_name
        return self.__url

    def end_txn(self, res=None, err=None):
        try:
            if not self.get_root_tracker().get_component() == constants.django_comp:
                if res is not None and hasattr(res, constants.status_code_str):
                    self.__status_code = res.status_code
                if err is not None:
                    self.__status_code = 500
        except:
            agentlogger.exception("while getting status code of the Transaction " + self.get_txn_name())

        super().end_txn(res, err)

    def get_status_code(self):
        return self.__status_code

    def set_status_code(self, code):
        if isinstance(code, int):
            self.__status_code = code

    def get_http_request_method(self):
        return self.__http_request_method

    def get_query_string(self):
        return self.__query

    def get_request_params(self):
        params = {}
        if self.__query:
            parsed = parse.parse_qs(parse.urlparse(self.__query).query)
            params.update({key, value[0]} for key, value in parsed.items())
        return params

    def get_http_input_params(self):
        return self.__http_input_params

    def get_txn_type(self):
        return constants.webtxn_type  # txn_type is 1 for web txns

    def get_txn_prefix(self):
        return constants.webtxn_prefix

    def get_rum_appkey(self):
        return self._txn_config.get_rum_appkey()

    def get_webtxn_naming_use_requesturl(self):
        return self._txn_config.get_txn_naming_use_requesturl()

    def is_error_txn(self):
        if isinstance(self.__status_code, int) and self.__status_code >= 400:
            return True

        return super().is_error_txn()

    def get_http_host(self):
        return self._http_host

    def _create_txn_payload(self):
        transaction_info = {}
        transaction_info[constants.exporter_param_key_query_string] = self.get_query_string()
        transaction_info[constants.exporter_param_key_http_input_params] = self.get_http_input_params()
        transaction_info[constants.exporter_param_key_request_method] = self.get_http_request_method()
        transaction_info[constants.exporter_param_key_response_code] = self.get_status_code()
        transaction_info[constants.exporter_param_key_http_host] = self.get_http_host()

        return super()._create_txn_payload(transaction_info)


class BackGroundTxn(Transaction):
    def __init__(self, txn_name, root_tracker_info={}, txn_config=None):
        super().__init__(root_tracker_info, txn_config)
        self.__txn_name = txn_name
        self.__async_parent_context = root_tracker_info.get(constants.ASYNC_PARENT_CONTEXT)
        self._asynchronous = 2 if self.__async_parent_context else 0

    def get_txn_name(self):
        if self._custom_name:
            return self._custom_name
        return self.__txn_name

    def get_txn_type(self):
        return constants.bgtxn_type

    def get_txn_prefix(self):
        return constants.bgtxn_prefix

    def _create_txn_payload(self):
        if self._asynchronous == 2:
            transaction_info = {}
            transaction_info[constants.exporter_param_key_trace_id] = self.__async_parent_context.get(
                constants.TRACE_ID_STR
            )
            transaction_info[constants.exporter_param_key_async] = self._asynchronous
            transaction_info[constants.exporter_param_key_cpu_time] = self.get_cpu_time()
            transaction_info[constants.exporter_param_key_memory_usage] = None
            transaction_info[constants.exporter_param_key_bytes_in] = None
            transaction_info[constants.exporter_param_key_bytes_out] = None
            transaction_info[constants.exporter_param_key_custom_params] = None
            transaction_info[constants.exporter_param_key_http_host] = None
            return self._create_final_payload(transaction_info)
        return super()._create_txn_payload()


class TxnConfig:
    def __init__(self, txn_config):
        self.__sql_stacktrace_threshold = txn_config.get(constants.sql_stacktrace, 3)
        self.__rum_appkey = txn_config.get(constants.web_rum_appkey, "")
        self.__txn_naming_use_requesturl = txn_config.get(constants.webtxn_naming_use_requesturl, "")
        self.__normalized_url = txn_config.get(TxnSpecificConfig.NORMALIZED_URL)
    def get_sql_stacktrace_threshold(self):
        return self.__sql_stacktrace_threshold

    def get_rum_appkey(self):
        return self.__rum_appkey

    def get_txn_naming_use_requesturl(self):
        return self.__txn_naming_use_requesturl

    def get_normalized_url(self):
        return self.__normalized_url
