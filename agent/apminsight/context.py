import sys
import threading
from apminsight import constants


def get_thread_local():
    try:
        import gevent
        if 'gevent' in sys.modules:
            from gevent.local import local as Local
            return Local
    except ImportError:
        pass

    return threading.local

local = get_thread_local()

thread_local = local()

def set_async_txn_trace_id(trace_id):
    setattr(thread_local, "apm_async_txn_trace_id", trace_id)


def set_async_tracker_span_id(span_id):
    setattr(thread_local, "apm_async_tracker_span_id", span_id)


def set_async_context(context):
    set_async_txn_trace_id(context.get(constants.TRACE_ID_STR))
    set_async_tracker_span_id(context.get(constants.SPAN_ID_STR))


def get_cur_async_context():
    return {constants.SPAN_ID_STR: get_async_tracker_span_id(), constants.TRACE_ID_STR: get_async_txn_trace_id()}


def get_async_txn_trace_id():
    return getattr(thread_local, "apm_async_txn_trace_id", "")


def get_async_tracker_span_id():
    return getattr(thread_local, "apm_async_tracker_span_id", "")


def has_no_async_context():
    return not bool(get_async_txn_trace_id())


def clear_cur_async_context():
    set_cur_context(None, None, None)


def set_cur_txn_trace_id(trace_id):
    setattr(thread_local, "apm_cur_txn_trace_id", trace_id)


def set_cur_txn(txn):
    setattr(thread_local, "apm_cur_txn", txn)


def set_cur_tracker(tracker):
    if tracker is None:
        set_cur_tracker_span_id(None)
    else:
        set_cur_tracker_span_id(tracker.get_span_id())


def set_cur_tracker_span_id(span_id):
    setattr(thread_local, "apm_cur_tracker_span_id", span_id)


def set_cur_context(txn=None, trace_id=None, span_id=None):
    set_cur_txn(txn)
    set_cur_txn_trace_id(trace_id)
    set_cur_tracker_span_id(span_id)


def clear_cur_context():
    set_cur_context(None, None, None)


def get_cur_context():
    return {constants.SPAN_ID_STR: get_cur_tracker_span_id(), constants.TRACE_ID_STR: get_cur_txn_trace_id()}


def get_cur_txn_trace_id():
    return getattr(thread_local, "apm_cur_txn_trace_id", "")


def get_cur_txn():
    return getattr(thread_local, "apm_cur_txn", None)


def get_cur_tracker_span_id():
    return getattr(thread_local, "apm_cur_tracker_span_id", "")


def get_cur_tracker():
    return get_cur_txn().get_tracker(get_cur_tracker_span_id()) if get_cur_txn() else None


def is_txn_active():
    return bool(get_cur_txn_trace_id())


def is_no_active_txn():
    return not bool(get_cur_txn_trace_id())
