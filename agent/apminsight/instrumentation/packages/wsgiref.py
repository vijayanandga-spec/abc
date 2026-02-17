import json
from apminsight import constants
from apminsight.instrumentation.wrapper import wsgi_wrapper, handle_dt_headers
from apminsight.context import get_cur_txn, is_no_active_txn
from apminsight.logger import agentlogger
from apminsight import constants

def wrap_send_headers(server_handler, original):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return original(*args, **kwargs)
        try:
            cur_txn = get_cur_txn()
            cur_txn.set_status_code(int(server_handler.status[:3]))

            if get_cur_txn().is_dt_response_headers_processed():
                return original(*args, **kwargs)
            
            dtdata = get_cur_txn().get_dt_response_headers()
            if not dtdata:
                license_key_from_req = server_handler.environ.get(constants.LICENSE_KEY_FOR_DT_REQUEST_HTTP)
                dtdata = handle_dt_headers(license_key_from_req)
            if dtdata:
                server_handler.headers[constants.DTDATA] = json.dumps(dtdata)
                cur_txn.dt_response_headers_processed()
        except:
            agentlogger.exception('while processing request and response headers')
        return original(*args, **kwargs)
    return wrapper
 
def wrap_run(original, module, method_info):
    def wrapper(*args, **kwargs):
        if len(args)==2:
            try:
                args[0].setup_environ()
                setattr(args[0], 'send_headers', wrap_send_headers(args[0], args[0].send_headers))
                wsgi_environ = args[0].environ
            except:
                agentlogger.exception('in wsgiref.wrap_run function')
            try:
                res = wsgi_wrapper(original, module, method_info, wsgi_environ)(*args, **kwargs)
            except Exception as exc:
                raise exc
            return res
        else:
            return original(*args, **kwargs)
    return wrapper
        
module_info = {
    'wsgiref.handlers' : [
        {
            constants.class_str : 'BaseHandler',
            constants.method_str : 'run',
            constants.wrapper_str : wrap_run,
            constants.component_str : constants.wsgiref_comp
        }
    ]
}