from apminsight import constants
from apminsight.instrumentation.wrapper import wsgi_wrapper, handle_dt_headers
from apminsight.context import get_cur_txn, is_no_active_txn
from apminsight.logger import agentlogger


def wrap_execute(original, module_name, method_info):
    def wrapper(*args, **kwargs):
        try:
            wsgi_environ = args[0].get_environment()
        except:
            agentlogger("while extracting wsgi_environ from waitress request")
        return wsgi_wrapper(original, module_name, method_info, wsgi_environ)(
            *args, **kwargs
        )

    return wrapper


def wrap_build_response_header(original, module_name, method_info):
    def wrapper(*args, **kwargs):

        if is_no_active_txn():
            return original(*args, **kwargs)
        try:
            cur_txn = get_cur_txn()
            cur_txn.set_status_code(int(args[0].status[:3]))

            if cur_txn.is_dt_response_headers_processed():
                return original(*args, **kwargs)

            dtdata = cur_txn.get_dt_response_headers()
            if not dtdata:
                license_key_from_req = args[0].environ.get(
                    constants.LICENSE_KEY_FOR_DT_REQUEST_HTTP
                )
                dtdata = handle_dt_headers(license_key_from_req)
            if dtdata:
                args[0].response_headers.append((constants.DTDATA, dtdata))
                cur_txn.dt_response_headers_processed()
        except:
            agentlogger.exception("while processing request and response headers")
        return original(*args, **kwargs)

    return wrapper


module_info = {
    "waitress.task": [
        {
            constants.class_str: "WSGITask",
            constants.method_str: "execute",
            constants.wrapper_str: wrap_execute,
            constants.component_str: constants.waitress_comp,
        },
        {
            constants.class_str: "Task",
            constants.method_str: "build_response_header",
            constants.wrapper_str: wrap_build_response_header,
            constants.component_str: constants.waitress_comp,
        },
    ],
}
