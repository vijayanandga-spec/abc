import asyncio

from apminsight import constants
from apminsight.logger import agentlogger
from apminsight.instrumentation.wrapper import (
    create_tracker_info,
    handle_dt_headers,
    default_wrapper,
    async_default_wrapper,
    handle_tracker_end,
)
from apminsight.context import clear_cur_context, get_cur_tracker, set_cur_tracker
from apminsight import get_agent


def version():
    import tornado

    return tornado.version


def get_class_path(obj):
    try:
        if isinstance(obj, type):
            module = getattr(obj, "__module__", None)
            name = getattr(obj, "__name__", "")
        elif isinstance(obj, object):
            module = getattr(obj.__class__, "__module__", None)
            name = getattr(obj.__class__, "__name__", "")
        else:
            return ""

        if module is None or module == "builtins":
            return name
        return f"{module}.{name}"

    except Exception as exc:
        agentlogger.exception("Exception while fetching class path in tornado app" + str(exc))
    return ""


def get_txn_params(method, path, host_name, port, qs=""):
    return {
        constants.request_method_str: method,
        constants.path_info_str: path,
        constants.server_name_str: host_name,
        constants.server_port_str: port,
        constants.query_string_str: qs,
    }


def get_request_details(instance):
    request = getattr(instance, "request", None)
    if request:
        if getattr(request, "uri", None) is not None:
            from tornado.httputil import split_host_and_port

            host, port = split_host_and_port(request.host.lower())
            port = port if port else constants.DEFAULT_TORNADO_PORT
            qs = getattr(request, "query", None)
            qs = qs.decode("utf-8") if isinstance(qs, bytes) else qs
            method = getattr(request, "method", "GET")
            path = getattr(request, "path", getattr(request, "uri", ""))
            return get_txn_params(method, path, host, str(port), qs)
    else:
        return None


def wrap_method(parent, method_list, wrapper=None, default=True):
    for method_name in method_list:
        method_addr = getattr(parent, method_name.lower(), None)
        if method_addr and callable(method_addr):
            if hasattr(method_addr, "apm_wrapper"):
                return
            if wrapper is None and default:
                wrapper = async_default_wrapper if asyncio.iscoroutinefunction(method_addr) else default_wrapper

            module_name = get_class_path(parent)
            method_info = {constants.method_str: method_name, constants.component_str: constants.tornado}
            method_wrapper = wrapper(method_addr, module_name, method_info)
            setattr(parent, method_name.lower(), method_wrapper)
            setattr(method_wrapper, "apm_wrapper", True)


def wrap_request_execute(original, module, method_info):

    async def wrapper(*args, **kwargs):
        cur_txn = None
        res = None
        agent = get_agent()
        try:
            asgi_environ = get_request_details(args[0])
            tracker_info = create_tracker_info(module, method_info)
            cur_txn = agent.check_and_create_webtxn(asgi_environ, tracker_info)
            if method_info.get(constants.DT_LK_KEY, None):
                license_key_from_req = asgi_environ.get(method_info.get(constants.DT_LK_KEY))
                handle_dt_headers(license_key_from_req)
        except:
            agentlogger.exception("in asgi wrapper")
        try:
            res = await original(*args, **kwargs)
            if cur_txn:
                cur_txn.set_status_code(args[0].get_status())
            agent.end_txn(cur_txn, res)
        except Exception as exc:
            agent.end_txn(cur_txn, err=exc)
            raise exc
        finally:
            clear_cur_context()
        return res

    return wrapper


def get_rule_handlers(rule):
    if isinstance(rule, (tuple, list)):
        return rule[1]
    elif hasattr(rule, "target"):
        return rule.target
    elif hasattr(rule, "handler_class"):
        return rule.handler_class
    else:
        return None


def instrument_rule_handler(rule):
    handler = get_rule_handlers(rule)

    if isinstance(handler, (tuple, list)):
        for each_rule in handler:
            instrument_rule_handler(each_rule)
        return

    from tornado.websocket import WebSocketHandler
    from tornado.web import StaticFileHandler, RequestHandler

    if handler and isinstance(handler, type) and issubclass(handler, RequestHandler):
        methods = list(getattr(handler, "SUPPORTED_METHODS", []))
        if issubclass(handler, WebSocketHandler) and isinstance(methods, list):
            methods.append("on_message")
        if isinstance(handler, type) and issubclass(handler, StaticFileHandler):
            return

        if not hasattr(handler, "apminsight_instrumented"):
            wrap_method(handler, methods)
            wrap_method(handler, ["_execute"], wrap_request_execute)
            wrap_method(handler, ["log_exception"], wrap_log_exception)
            setattr(handler, "apminsight_instrumented", True)
    return


def route_wrapper(original, module, method_info):
    def wrapper(*args, **kwargs):
        def _bind_rule_params(instance, rule, *args, **kwargs):
            return rule

        rule = _bind_rule_params(*args, **kwargs)

        instrument_rule_handler(rule)
        res = original(*args, **kwargs)
        return res

    return wrapper


def wrap_headers_received(request_conn):
    def function_wrapper(method_call):
        def _wrapper(*args, **kwargs):
            return method_call(*args, **kwargs)

        return _wrapper

    def _wrap_headers_received(wrapped, module, method_info):

        @function_wrapper
        def _inner_wrapper(*args, **kwargs):
            return wrapped(*args, **kwargs)

        return _inner_wrapper

    return _wrap_headers_received


def wrap_log_exception(original, module, method_info):

    def bind_value_param(instance, typ, value, tb):
        return value

    def wrapper(*args, **kwargs):
        res = err = None
        agent = get_agent()
        parent_tracker = get_cur_tracker()
        tracker_info = create_tracker_info(module, method_info, parent_tracker=parent_tracker)
        cur_tracker = agent.check_and_create_tracker(tracker_info)
        try:
            err = bind_value_param(*args, **kwargs)
            res = original(*args, **kwargs)
        except Exception as exc:
            raise exc
        finally:
            handle_tracker_end(cur_tracker, method_info, args, kwargs, res, err)
            set_cur_tracker(parent_tracker)
        return res

    return wrapper


def wrap_start_request(original, module, method_info):
    def _bind_start_request(instance, server_conn, request_conn, *args, **kwargs):
        return request_conn

    def wrapper(*args, **kwargs):
        request_conn = _bind_start_request(*args, **kwargs)
        wrap_method(request_conn, ["write_headers", "finish"])

        message_delegate = original(*args, **kwargs)
        return message_delegate

    return wrapper


module_info = {
    "tornado.httpserver": [
        {
            constants.class_str: "HTTPServer",
            constants.method_str: "start_request",
            constants.component_str: constants.tornado,
            constants.wrapper_str: wrap_start_request,
        }
    ],
    "tornado.routing": [
        {
            constants.class_str: "ReversibleRuleRouter",
            constants.method_str: "process_rule",
            constants.component_str: constants.tornado,
            constants.wrapper_str: route_wrapper,
        }
    ],
}
