from apminsight import constants
from apminsight.instrumentation.wrapper import wsgi_wrapper, handle_dt_headers
from apminsight.context import get_cur_txn, is_no_active_txn
from apminsight.logger import agentlogger
        
def wrap_send_headers(original, module, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return original(*args, **kwargs)
        request_headers = {}
        cur_txn = get_cur_txn()
        try:
            cur_txn.set_status_code(int(args[0].status[:3]))
            for key, val in args[0].inheaders.items():
                    request_headers[key.decode()] = val.decode()
                
            if cur_txn.is_dt_response_headers_processed():
                return original(*args, **kwargs)
            
            dtdata = cur_txn.get_dt_response_headers()
            if not dtdata:
                license_key_from_req = request_headers.get(constants.LICENSE_KEY_FOR_DT_REQUEST.title())
                dtdata = handle_dt_headers(license_key_from_req)

            if dtdata:
                args[0].outheaders.append((constants.DTDATA.encode('ASCII'), str(dtdata).encode('ASCII')))
                cur_txn.dt_response_headers_processed()
        except:
            agentlogger.exception('while processing request and response headers')
        return original(*args, **kwargs)
    return wrapper

def wrap_respond(original, module, method_info, wsgi_environ=None):
    def wrapper(*args, **kwargs):
        try:
            wsgi_environ = args[0].env
        except:
            agentlogger.exception('while extracting wsgi environ')
        return wsgi_wrapper(original, module, method_info, wsgi_environ)(*args, **kwargs)
    return wrapper

module_info = {
    'cheroot.server' : [
        {
            constants.class_str : 'HTTPRequest',
            constants.method_str : 'send_headers',
            constants.component_str : constants.cheroot_comp,
            constants.wrapper_str : wrap_send_headers
        }
    ],
    'cheroot.wsgi' : [
        {
            constants.class_str : 'Gateway',
            constants.method_str : 'respond',
            constants.component_str : constants.cheroot_comp,
            constants.wrapper_str : wrap_respond
        }
    ],
 }
