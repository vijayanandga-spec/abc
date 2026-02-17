from apminsight import constants
from apminsight.logger import agentlogger


def bind_params( instance, conn, host, absolute_uri, request_uri, method, body, headers, *args, **kwargs):
    return instance, conn, host, absolute_uri, request_uri, method, body, headers

def extract_req(tracker, args=(), kwargs={}, return_value=None, error=None):
    request_info = {}
    try:
        _, conn, host, url, request_uri, method, body, headers = bind_params(*args, **kwargs)
        request_info.update({
            constants.HTTP_METHOD: method,
            constants.HOST: conn.host,
            constants.PORT: conn.port,
            constants.URL: url,
            constants.REQUEST_HEADERS: headers if isinstance(headers,dict) else {},
        })
        if return_value:
            status = str(return_value[0].status) if return_value else ''
            tracker.set_tracker_name(f"{tracker.get_tracker_name()} : {method} - {status} - {url}")
            tracker.set_as_http_err() if int(status) >= 400 else 0
            request_info[constants.RESPONSE_HEADERS] = dict(return_value[0])
        else:
            tracker.set_tracker_name(f"{tracker.get_tracker_name()} : {method} - {url}")

    except Exception as exc:
        agentlogger.exception(f"Extracting request details failed: {exc}")
    tracker.set_info(request_info)


module_info = {
    "httplib2": [
        {
            constants.class_str: "Http",
            constants.method_str: "_request",
            constants.component_str: constants.http_comp,
            constants.extract_info_str: extract_req,
        },
    ],
}
