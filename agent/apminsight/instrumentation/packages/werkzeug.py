from apminsight import constants
from apminsight.instrumentation.wrapper import wsgi_wrapper, handle_dt_headers
from apminsight.context import get_cur_txn, is_no_active_txn
from apminsight.logger import agentlogger

def wrap_debugged_application(original, module, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return original(*args, **kwargs)
        if len(args)>2:
            try:
                cur_txn = get_cur_txn()
                if cur_txn.get_dt_response_headers() or cur_txn.is_dt_response_headers_processed():
                    return original(*args, **kwargs)
                license_key_from_req = args[1].get(constants.LICENSE_KEY_FOR_DT_REQUEST_HTTP)
                handle_dt_headers(license_key_from_req)
            except:
                agentlogger.exception('while processing request headers')
        return original(*args, **kwargs)
    return wrapper
        
def wrap_run_wsgi(original, module, method_info):
    def wrapper(*args, **kwargs):
        wsgi_environ=None
        try:
            wsgi_environ = args[0].make_environ()
        except:
            agentlogger.exception('while constructing wsgi_environ')
        return wsgi_wrapper(original, module, method_info, wsgi_environ)(*args, **kwargs)
    return wrapper

def wrap_get_wsgi_headers(original, module, method_info):
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
            if not cur_txn.is_dt_response_headers_processed() and cur_txn.get_dt_response_headers():
                res.add(constants.DTDATA, get_cur_txn().get_dt_response_headers())
                cur_txn.dt_response_headers_processed()
        except:
            agentlogger.exception('while setting response headers for distributed trace')
        return res
    return wrapper
        
module_info = {
    'werkzeug.debug' : [
        {
            constants.class_str : 'DebuggedApplication',
            constants.method_str : '__call__',
            constants.wrapper_str : wrap_debugged_application,
            constants.component_str : constants.werkzeug_comp
        },
    ],
    'werkzeug.serving' : [
        {
            constants.class_str : 'WSGIRequestHandler',
            constants.method_str : 'run_wsgi',
            constants.wrapper_str : wrap_run_wsgi,
            constants.component_str : constants.werkzeug_comp
        },
    ],
    'werkzeug.wrappers.response' : [
        {
            constants.class_str : 'Response',
            constants.method_str : 'get_wsgi_headers',
            constants.wrapper_str : wrap_get_wsgi_headers,
            constants.component_str : constants.werkzeug_comp
        }
    ]
}