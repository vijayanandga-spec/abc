import sys
from unittest import result   
from apminsight import constants, name
from apminsight.context import get_cur_txn
from apminsight.instrumentation.wrapper import wsgi_wrapper, default_wrapper
from apminsight.logger import agentlogger
from apminsight.instrumentation.util import callable_name

def wrap_start_response(original):

    def wrapper(status, response_headers, *args):
        try:
            cur_txn = get_cur_txn()
            if cur_txn:
                cur_txn.set_status_code(int(status.split(" ")[0]))
                if cur_txn.get_dt_response_headers():
                    response_headers.append((constants.DTDATA, cur_txn.get_dt_response_headers()))
        except Exception as e:
            agentlogger.info("Error occurred while wrapping start_response:", e) 
        return original(status, response_headers, *args)
    return wrapper
    
def wrap_app_call(original, module, method_info):
    def bind_args(instance, environ, start_response, *args, **kwargs):
        return instance, environ, start_response, args, kwargs

    def wrapper(*args, **kwargs):
        instance, environ, start_response, _args, _kwargs = bind_args(*args, **kwargs)
        cur_txn = get_cur_txn()
        response_wrapper = wrap_start_response(start_response)
        if cur_txn :
            return default_wrapper(original, module, method_info)(instance, environ, response_wrapper, *_args, **_kwargs)
        else:
            return wsgi_wrapper(original, module, method_info)(instance, environ, response_wrapper, *_args, **_kwargs)
    return wrapper


def extract_exception_info(tracker, args=(), kwargs={}, return_value=None, error=None):
    def get_resp(instance, req, resp, ex, params):
        return resp
    
    try:
        cur_txn = get_cur_txn()
        if cur_txn:
            resp = get_resp(*args, **kwargs)
            response_code = int(resp.status.split()[0])
            cur_txn.set_status_code(response_code)

        exc_info = sys.exc_info()
        tracker.mark_error(exc_info[1])
        
    except Exception as e:
        agentlogger.info("Error occurred while extracting exception info:", e)

def method_wrapper(original, module, method_info):
    
    def wrapper(*args, **kwargs):
        try:
            module = callable_name(original)
        except Exception as e:
            agentlogger.info("Error occurred while getting callable name:", e)
        return default_wrapper(original, module, method_info)(*args, **kwargs)

    wrapper._apminsight_wrapped = True
    return wrapper


def wrap_http_methods(original, module, method_info):
    http_method_info = {
        constants.method_str: "",
        constants.component_str:constants.falcon_comp,
    }
    def wrapper(*args, **kwargs):
        method_map = original(*args, **kwargs)
        wrapped_method_map = {}
        for http_method, responder in method_map.items():
            # Skip if already wrapped to avoid double-wrapping
            if getattr(responder, '_apminsight_wrapped', False):
                wrapped_method_map[http_method] = responder
            else:
                wrapped_method_map[http_method] = method_wrapper(responder, "", http_method_info)
        return wrapped_method_map

    return wrapper


module_info = {
    "falcon.api": [{
        constants.class_str: "API",
        constants.method_str: "__call__",
        constants.wrapper_str: wrap_app_call,
        constants.DT_LK_KEY: constants.LICENSE_KEY_FOR_DT_REQUEST_HTTP,
        constants.component_str:constants.falcon_comp,
    },{
        constants.class_str: "API",
        constants.method_str: "_handle_exception",
        constants.wrapper_str: default_wrapper,
        constants.extract_info_str: extract_exception_info,
        constants.component_str:constants.falcon_comp,
    }],
    "falcon.app": [{
        constants.class_str: "App",
        constants.method_str: "__call__",
        constants.wrapper_str: wrap_app_call,
        constants.DT_LK_KEY: constants.LICENSE_KEY_FOR_DT_REQUEST_HTTP,
        constants.component_str:constants.falcon_comp,
    },{
        constants.class_str: "App",
        constants.method_str: "_handle_exception",
        constants.wrapper_str: default_wrapper,
        constants.extract_info_str: extract_exception_info,
        constants.component_str:constants.falcon_comp,
    }],
    "falcon.routing.util": [{
        constants.method_str: "map_http_methods",
        constants.wrapper_str: wrap_http_methods,
        constants.component_str:constants.falcon_comp,
    },{
        constants.method_str: "create_http_method_map",
        constants.wrapper_str: wrap_http_methods,
        constants.component_str:constants.falcon_comp,
    }],
    "falcon.routing.compiled": [{
        constants.method_str: "map_http_methods",
        constants.wrapper_str: wrap_http_methods,
        constants.component_str:constants.falcon_comp,
    },{
        constants.method_str: "create_http_method_map",
        constants.wrapper_str: wrap_http_methods,
        constants.component_str:constants.falcon_comp,
    }]
}
