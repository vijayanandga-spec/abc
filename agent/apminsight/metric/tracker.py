from apminsight.constants import (
    CONTEXT,
    PARENT_CONTEXT,
    IS_ASYNC,
    ASYNC_PARENT_CONTEXT,
    OPERATION,
    SPAN_ID_STR,
    TRACE_ID_STR,
    LOGINFO,
    TIME,
    max_exc_per_trace,
    SH_STRING,
    SH_ERR_CLS,
    SH_STACK_TRACE,
    SH_ASYNC_ROOT,
    SH_EXT_COMP,
    SH_IS_ERROR,
    SH_HOST_NAME,
    SH_IS_FAULT,
    SH_START_TIME,
    SH_PORT_NUMBER,
    SH_END_TIME,
    SH_FUN_NAME,
    SH_COMP_NAME,
    SH_SPAN_ID,
    SH_PAR_SPAN_ID,
    SH_DIST_TRACE,
    SH_QUERY_STR,
    SH_ERR_INFO,
    SH_ERR_MSG,
    SH_ERR_STACK_TRACE,
    STACKTRACE,
    SH_SPAN_PRIORITY,
)
from apminsight.constants import SpanConstants
from apminsight.util import current_milli_time
from apminsight.metric.error import ErrorInfo
from apminsight.logger import agentlogger
from apminsight.util import is_ext_comp, remove_null_keys, get_current_stacktrace
from apminsight import constants
from apminsight import context


class Tracker:

    def __init__(self, tracker_info={}):
        self.__name = tracker_info.get("name", "anonymous")
        self.__actual_method = tracker_info.get("name", "anonymous")
        self.__component = tracker_info.get("component", "")
        self.__start_time = current_milli_time()
        self.__end_time = 0
        self.__rt = 0
        self.__child_overhead = 0
        self._info = {}
        self.__child_trackers = []
        self.__error = None
        self.__is_error = False
        self.__exception = None
        self.__is_exception = 0
        self.__completed = False
        self.__http_err = 0
        self.__context = tracker_info.get(CONTEXT)
        self.__parent_context = tracker_info.get(PARENT_CONTEXT, {})
        self.__dt_trace = False
        self.__async_root = tracker_info.get(IS_ASYNC)
        self.__async_parent_context = tracker_info.get(ASYNC_PARENT_CONTEXT, {})
        self.__priority = 0  # for all traces capturing

    def end_tracker(self, err=None):
        from apminsight.metric.dbtracker import DbTracker

        try:
            if err is not None:
                self.mark_error(err)
            self.__end_time = current_milli_time()
            total_time = self.__end_time - self.__start_time
            self.__rt = total_time - self.__child_overhead
            if (
                isinstance(self, DbTracker)
                and not self.is_error()
                and self.__rt >= context.get_cur_txn().get_sql_stacktrace_threshold() * 1000
            ):
                self._info[constants.STACKTRACE] = get_current_stacktrace()
            parent = self.get_parent()
            if parent is not None:
                parent.update_child_overhead(total_time)
                parent.add_child_tracker(self)
            if self.is_distributed_trace():
                context.get_cur_txn().increment_dt_count()

            self.__completed = True
        except:
            agentlogger.exception("while ending the tracker, " + self.__name)

    def get_parent(self):
        parent_span_id = self.get_parent_span_id()
        cur_txn = context.get_cur_txn()
        if cur_txn is not None and parent_span_id is not None:
            return cur_txn.get_tracker(parent_span_id)

    def get_parent_context(self):
        return self.__parent_context

    def set_parent_context(self, context):
        self.__parent_context = context

    def get_actual_method(self):
        return self.__actual_method

    def set_tracker_name(self, name):
        if isinstance(name, str):
            self.__name = name

    def get_end_time(self):
        return self.__end_time

    def set_end_time(self, end_time):
        if isinstance(end_time, int):
            self.__end_time = end_time

    def set_priority(self, value: int = 1):
        self.__priority = value

    def mark_error(self, err):
        if err is not None:
            self.__is_error = True
            self.__name += " : " + str(type(err).__name__ if hasattr(type(err), "__name__") else "Error")
            if isinstance(err, Exception) and not hasattr(err, "apminsight"):
                self.__error = ErrorInfo(err)
                err.apminsight = True

    def mark_exception(self, err: Exception) -> None:
        if err is not None:
            self.__is_exception = 1
            self.__name = "Custom-Captured-Exception-" + str(
                type(err).__name__ if hasattr(type(err), "__name__") else "Error"
            )
            if isinstance(err, Exception) and not hasattr(err, "apminsight"):
                self.__exception = ErrorInfo(err)
                setattr(err, "apminsight", True)

    def get_child_overhead(self):
        return self.__child_overhead

    def update_child_overhead(self, total_time):
        self.__child_overhead += total_time

    def get_child_trackers(self):
        return self.__child_trackers

    def add_child_tracker(self, child_trakcer):
        self.__child_trackers.append(child_trakcer)

    def get_tracker_name(self):
        if OPERATION not in self._info:
            return self.__name

        query_info = self._info[OPERATION]
        if constants.host_str in self._info and constants.port_str in self._info:
            query_info += " - " + self._info[constants.host_str] + ":" + str(self._info[constants.port_str])

        return self.__name + " : " + query_info

    def get_rt(self):
        return self.__rt

    def set_rt(self, rt):
        if isinstance(rt, int):
            self.__rt = rt

    def complete(self):
        self.__completed = True

    def is_completed(self):
        return self.__completed is True

    def get_component(self):
        return self.__component

    def set_component(self, component):
        if isinstance(component, str):
            self.__component = component

    def get_info(self, key=None):
        if key is None:
            return self._info
        if key and isinstance(key, str):
            return self._info.get(key)

    def set_info(self, info):
        self._info.update(info)

    def is_error(self):
        if self.__is_error:
            return True

        return False

    def set_as_http_err(self):
        self.__http_err = 1

    def is_http_err(self):
        return self.__http_err

    def get_error_name(self):
        if self.__error is not None:
            try:
                return self.__error.get_type()
            except:
                agentlogger.exception("While extracting error information")

        return ""

    def __get_err_info(self):
        return self.__error

    def is_exception(self):
        return self.__is_exception

    def get_exception_name(self) -> str:
        if self.__exception is not None:
            try:
                return self.__exception.get_type()
            except:
                agentlogger.exception("While extracting exception information")

        return ""

    def set_exception(self, err):
        self.__exception = ErrorInfo(err)

    def get_span_id(self):
        return self.__context.get(SPAN_ID_STR)

    def get_parent_span_id(self):
        return self.__parent_context.get(SPAN_ID_STR) or self.__async_parent_context.get(SPAN_ID_STR)

    def get_context(self):
        return self.__context

    def set_context(self, context):
        self.__context = context

    def get_trace_id(self):
        return self.__context.get(TRACE_ID_STR)

    def is_distributed_trace(self):
        return self.__dt_trace

    def set_dt_trace(self):
        self.__dt_trace = True

    def check_and_add_loginfo(self, trace_info={}):
        if LOGINFO not in trace_info:
            trace_info[LOGINFO] = []

        if self.is_error() and len(trace_info[LOGINFO]) <= max_exc_per_trace:
            log_info = {}
            err_info = self.__get_err_info()
            log_info[TIME] = err_info.get_time()
            log_info[constants.level_str] = err_info.get_level()
            log_info[SH_STRING] = err_info.get_message()
            log_info[SH_ERR_CLS] = err_info.get_type()
            log_info[SH_STACK_TRACE] = err_info.get_error_stack_frames()
            trace_info[LOGINFO].append(log_info)
        elif self.is_exception() and len(trace_info[LOGINFO]) <= max_exc_per_trace:
            excinfo = self.__get_exc_info()
            log_info[TIME] = excinfo.get_time()
            log_info[constants.level_str] = excinfo.get_level()
            log_info[SH_STRING] = excinfo.get_message()
            log_info[SH_ERR_CLS] = excinfo.get_type()
            log_info[SH_STACK_TRACE] = excinfo.get_error_stack_frames()
            trace_info[LOGINFO].append(log_info)

    def get_tracker_info(self, trace_info={}):
        self.check_and_add_loginfo(trace_info)
        tracker_info = []
        tracker_info.append(self.__start_time)
        tracker_info.append(self.get_tracker_name())
        tracker_info.append(self.__component)
        tracker_info.append(self.__rt + self.__child_overhead)  # total
        tracker_info.append(self.__rt)  # exclusive
        tracker_info.append(self.get_additional_info())
        tracker_info.append([])
        return tracker_info

    def get_additional_info(self):
        info = {}
        if self.is_error():
            info["exception_st"] = self.__error.get_error_stack_frames()
        if self.is_distributed_trace():
            info["dtdata"] = self.get_info().get("dtdata")
        return info

    def get_tracker_data_for_trace(self, trace_info):
        cur_tracker_info = self.get_tracker_info(trace_info)

        for eachchild in self.__child_trackers:
            child_tracker_data = eachchild.get_tracker_data_for_trace(trace_info)
            cur_tracker_info[6].append(child_tracker_data)

        return cur_tracker_info

    def get_span_priority(self):
        if self.__error or self.__exception or self.get_component() in constants.ext_components:
            return 1
        return self.__priority

    def add_tracker_data(self):
        method_data = {
            SpanConstants.START_TIME: self.__start_time,
            SpanConstants.END_TIME: self.__end_time,
            SpanConstants.FUN_NAME: self.get_tracker_name(),
            SpanConstants.SPAN_ID: self.get_span_id(),
            SpanConstants.PAR_SPAN_ID: self.get_parent_span_id(),
            SpanConstants.DIST_TRACE: self.get_info().get("dtdata", {}),
            SpanConstants.ASYNC_ROOT: self.__async_root,
            SpanConstants.IS_FAULT: self.__is_exception,
            SpanConstants.IS_ERROR: 1 if self.is_error() or self.is_http_err() else 0,
            SpanConstants.EXT_COMP: int(is_ext_comp(self.get_component())),
            SpanConstants.COMP_NAME: self.get_component() or constants.python_str,
            SpanConstants.SPAN_PRIORITY: self.get_span_priority(),
        }
        if self.get_component() == constants.http_comp:
            method_data.update({
                SpanConstants.HOST_NAME: self._info.get("url", ""),
                SpanConstants.REQUEST_HEADERS: self._info.get("request_headers", None),
                SpanConstants.RESPONSE_HEADERS: self._info.get("response_headers", None),
                SpanConstants.STATUS: self._info.get("status", 200),
            })
        elif self._info.get(constants.host_str):
            method_data[SH_HOST_NAME] = self._info.get(constants.host_str, "")
        if self._info.get(constants.port_str):
            method_data[SH_PORT_NUMBER] = self._info.get(constants.port_str)

        if self._info.get(constants.query_str, ""):
            method_data[SH_QUERY_STR] = self._info.get(constants.query_str)
        method_data[SH_ERR_INFO] = []
        if self.__error:
            err_info = self.__get_err_info()
            error_details = {}
            error_details[TIME] = err_info.get_time()
            error_details[constants.level_str] = err_info.get_level()
            error_details[SH_ERR_MSG] = err_info.get_message()
            error_details[SH_ERR_CLS] = err_info.get_type()
            method_data[SH_ERR_INFO].append(error_details)
            method_data[SH_ERR_STACK_TRACE] = self.__get_err_info().get_error_stack_frames()
        elif self.__exception:
            exc_info = self.__exception
            exception_details = {}
            exception_details[TIME] = exc_info.get_time()
            exception_details[constants.level_str] = exc_info.get_level()
            exception_details[SH_ERR_MSG] = exc_info.get_message()
            exception_details[SH_ERR_CLS] = exc_info.get_type()
            method_data[SH_ERR_INFO].append(exception_details)
            method_data[SH_ERR_STACK_TRACE] = self.__exception.get_error_stack_frames()
        else:
            method_data[SH_ERR_STACK_TRACE] = self._info.get(STACKTRACE)

        remove_null_keys(method_data)
        return method_data
