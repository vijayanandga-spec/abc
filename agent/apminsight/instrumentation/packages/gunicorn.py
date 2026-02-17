from apminsight import constants
from apminsight.instrumentation.wrapper import wsgi_wrapper, handle_dt_headers
from apminsight.context import get_cur_txn, is_no_active_txn, get_cur_tracker
from apminsight.logger import agentlogger


def wrap_handle_request(original, module_name, method_info):

    def bind_request_param(instance, listener, req, client, addr):
        return req

    def wrapper(*args, **kwargs):
        wsgi_environ = None
        try:
            request = bind_request_param(*args, **kwargs)
            request_headers = request.headers
            host_addr = [header_tuple[1] for header_tuple in request_headers if header_tuple[0] == "HOST"][0]
            host_addr_list = host_addr.split(":") if isinstance(host_addr, str) else list(host_addr_list)
            port = "8000" if len(host_addr_list) < 2 else host_addr_list[1]
            wsgi_environ = {
                constants.request_method_str: request.method,
                constants.query_string_str: request.query,
                constants.path_info_str: request.uri,
                constants.server_port_str: port,
            }
        except:
            agentlogger.exception("in gunicorn.wrap_handle function")
        return wsgi_wrapper(original, module_name, method_info, wsgi_environ)(*args, **kwargs)

    return wrapper


def wrap_default_headers(original, module_name, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return original(*args, **kwargs)
        try:
            res = original(*args, **kwargs)
        except Exception as exc:
            raise exc
        try:
            cur_txn = get_cur_txn()
            cur_txn.set_status_code(int(args[0].status[:3]))

            request_headers = {}
            for header_pair in args[0].req.headers:
                request_headers[header_pair[0]] = header_pair[1]

            if cur_txn.is_dt_response_headers_processed():
                return res

            dtdata = cur_txn.get_dt_response_headers()
            if not dtdata:
                license_key_from_req = request_headers.get(constants.LICENSE_KEY_FOR_DT_REQUEST.upper())
                dtdata = handle_dt_headers(license_key_from_req)
            if dtdata:
                res.append("dtdata: %s\r\n" % get_cur_txn().get_dt_response_headers())
                cur_txn.dt_response_headers_processed()
        except:
            agentlogger.exception("while adding distributed trace headers")
        return res

    return wrapper


def wrap_response(original, module, method_info):
    def bind_exc_info(resp_instance, status, headers, exc_info=None):
        return exc_info

    def wrapper(*args, **kwargs):

        if is_no_active_txn():
            return original(*args, **kwargs)

        res = None
        try:
            res = original(*args, **kwargs)
        except Exception as exc:
            raise exc
        try:
            status_code = args[0].status_code
            exc_info = bind_exc_info(*args, **kwargs)

            if status_code:
                get_cur_txn().set_status_code(int(status_code))
            if exc_info:
                get_cur_tracker().mark_error(exc_info)

        except Exception as exc:
            pass
        return res

    return wrapper


module_info = {
    "gunicorn.workers.sync": [
        {
            constants.class_str: "SyncWorker",
            constants.method_str: "handle_request",
            constants.wrapper_str: wrap_handle_request,
            constants.component_str: constants.gunicorn_comp,
        }
    ],
    "gunicorn.http.wsgi": [
        {
            constants.class_str: "Response",
            constants.method_str: "default_headers",
            constants.wrapper_str: wrap_default_headers,
            constants.component_str: constants.gunicorn_comp,
        },
        {
            constants.class_str: "Response",
            constants.method_str: "start_response",
            constants.wrapper_str: wrap_response,
            constants.component_str: constants.gunicorn_comp,
        },
    ],
}
