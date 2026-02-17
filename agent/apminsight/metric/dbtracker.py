from apminsight.metric.tracker import Tracker
from apminsight.metric.dbmetric import DbMetric
from apminsight.agentfactory import get_agent
from apminsight.util import get_masked_query, is_empty_string
from apminsight.constants import OPERATION, OBJECT, DB_OPERATION, EXP_STACK_TRACE, STACKTRACE, QUERY


class DbTracker(Tracker):

    def __init__(self, tracker_info={}):
        super(DbTracker, self).__init__(tracker_info)

    def is_allowed_in_trace(self):
        return True

    def get_tracker_info(self, trace_info):
        info = self.get_info()
        if OPERATION in info and OBJECT in info:
            opninfo = info[OPERATION] + "/" + info[OBJECT]
            if opninfo not in trace_info[DB_OPERATION]:
                trace_info[DB_OPERATION].append(opninfo)

        return super(DbTracker, self).get_tracker_info(trace_info)

    def get_additional_info(self):
        info = {}
        if self.is_error():
            info[EXP_STACK_TRACE] = self.get_error().get_error_stack_frames()
        elif self._info.get(STACKTRACE):
            info[STACKTRACE] = self._info[STACKTRACE]

        if QUERY in self._info and is_empty_string(self.get_info(QUERY)):
            return info

        if get_agent().get_threshold().is_sql_parameterized():
            info[QUERY] = get_masked_query(self.get_info(QUERY))
        else:
            info[QUERY] = self.get_info(QUERY)

        return info

    def accumulate(self, name, metric):
        match = metric[name] if name in metric else DbMetric()
        match.accumulate(self)
        metric[name] = match
