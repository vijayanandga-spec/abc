from apminsight import constants
from apminsight.logger import agentlogger
from apminsight.context import is_no_active_txn, get_cur_txn
from apminsight.agentfactory import get_agent
from apminsight.instrumentation.wrapper import default_wrapper
from apminsight.util import is_non_empty_string


def wrap_urlopen(original, module, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return original(*args, **kwargs)
        headers = kwargs.get("headers", None)
        if not headers or not isinstance(headers, dict):
            return default_wrapper(original, module, method_info)(*args, **kwargs)
        try:
            license_key_for_dt = get_agent().get_config().get_license_key_for_dt()
            kwargs.get("headers").update({constants.LICENSE_KEY_FOR_DT_REQUEST: license_key_for_dt})
            get_cur_txn().dt_req_headers_injected(True)
        except Exception as exc:
            agentlogger.error(f"Error adding DT request headers: {exc}")
        return default_wrapper(original, module, method_info)(*args, **kwargs)

    return wrapper


def get_request_url(conn, url: str = ""):
    from urllib3.connectionpool import HTTPSConnection

    if isinstance(conn, HTTPSConnection):
        return "https://" + conn.host + url
    else:
        return "http://" + conn.host + url


def get_conn_host_port(conn):
    if conn:
        return conn.host, conn.port
    return None, None


def bind_params(conn, method, url, **bkwargs):
    return conn, method, url, dict(bkwargs.get("headers", {}))


def extract_urllib3_request(tracker, args=(), kwargs={}, return_value=None, error=None):
    try:
        conn, method, url, request_headers = bind_params(*args, **kwargs)
        host, port = get_conn_host_port(conn)
        method = method if is_non_empty_string(method) else "REQUESTS-GET"
        url = get_request_url(conn, url)
        url = url if is_non_empty_string(url) else ""
        status = response_headers = None
        if return_value is not None:
            status = str(return_value.status)
            response_headers = dict(return_value.headers) if hasattr(return_value, 'headers') else None
        tracker_name = tracker.get_tracker_name() or ""
        if status is not None:
            tracker.set_tracker_name(f"{tracker_name} : {method} - {status} - {url}")
            if status.isdigit() and int(status) >= 400:
                tracker.set_as_http_err()
        else:
            tracker.set_tracker_name(f"{tracker_name} : {method} - {url}")
        tracker.set_info({
            constants.HTTP_METHOD: method,
            constants.HOST: host,
            constants.PORT: port,
            constants.URL: url,
            constants.STATUS: status,
            constants.RESPONSE_HEADERS: response_headers,
            constants.REQUEST_HEADERS: request_headers,
        })
    except Exception as exc:
        agentlogger.info(f"Error extracting URLLIB3 request: {exc}")


module_info = {
    "urllib3.connectionpool": [
        {
            constants.class_str: "HTTPConnectionPool",
            constants.method_str: "urlopen",
            constants.component_str: constants.http_comp,
            constants.wrapper_str: wrap_urlopen,
            constants.extract_info_str: extract_urllib3_request,
        }
    ],
}
