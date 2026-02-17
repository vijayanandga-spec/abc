from apminsight.agentfactory import get_agent
from apminsight.logger import agentlogger
from apminsight import constants
from apminsight.util import current_milli_time
from apminsight.collector.reqhandler import send_req
from apminsight.collector.rescodes import is_allowed_to_send_request
from apminsight.collector.reshandler import handle_data_response


def get_data_with_time(ins_info, data):
    millis = current_milli_time()
    last_reported = ins_info.get_last_reported()
    last_reported = current_milli_time if last_reported is None else last_reported
    return [millis, last_reported, data]


def process_collected_data():
    ins_info = get_agent().get_ins_info()
    status = ins_info.get_status()
    metric_store = get_agent().get_metric_store()
    try:
        if status == constants.manage_agent:
            apdex_data = metric_store.get_formatted_data()
            trace_data = metric_store.get_formatted_trace()
            apdex_response = send_req(constants.arh_data, get_data_with_time(ins_info, apdex_data))
            handle_data_response(apdex_response)
            if len(trace_data) > 0:
                trace_response = send_req(constants.arh_trace, get_data_with_time(ins_info, trace_data))
                handle_data_response(trace_response)

        elif status == constants.unmanage_agent:
            trace_response = send_req(constants.arh_data, get_data_with_time(ins_info, []))
            handle_data_response(trace_response)

        else:
            if is_allowed_to_send_request(ins_info.get_status(), ins_info.get_retry_counter()):
                payload = get_data_with_time(ins_info, [])
                response = send_req(constants.arh_data, payload)
                handle_data_response(response)
    except Exception as exc:
        agentlogger.exception("While processing collected data")
    finally:
        metric_store.cleanup()
