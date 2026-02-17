import json
import asyncio
from apminsight.agentfactory import get_agent
from apminsight.logger import agentlogger, update_handler_file_name
from apminsight.util import is_callable, is_non_empty_string
from apminsight.metric.tracker import Tracker
from apminsight.constants import (
    DT_LK_KEY,
    path_info_str,
    query_string_str,
    request_method_str,
    server_port_str,
    wrap_args_str,
    extract_info_str,
    DT_TXN_NAME,
    DT_ST_TIME,
    DT_INS_ID,
    HTTP,
)
from apminsight.instrumentation.util import create_tracker_info, is_async
from apminsight.context import (
    clear_cur_context,
    is_no_active_txn,
    has_no_async_context,
    get_cur_tracker,
    set_cur_tracker,
    get_cur_txn,
)


def wsgi_wrapper(original, module, method_info, environ=None):
    def wrapper(*args, **kwargs):
        cur_txn = get_cur_txn()
        if cur_txn:
            return default_wrapper(original, module, method_info)(*args, **kwargs)

        res = None
        agent = get_agent()
        try:
            wsgi_environ = environ or args[1]
            tracker_info = create_tracker_info(module, method_info)
            cur_txn = agent.check_and_create_webtxn(wsgi_environ, tracker_info)
            if method_info.get(DT_LK_KEY):
                license_key_from_req = wsgi_environ.get(method_info.get(DT_LK_KEY))
                handle_dt_headers(license_key_from_req)
        except:
            agentlogger.exception("in wsgi wrapper")
        try:
            res = original(*args, **kwargs)
            agent.end_txn(cur_txn, res)
        except Exception as exc:
            agent.end_txn(cur_txn, err=exc)
            raise exc
        finally:
            clear_cur_context()
        return res

    return wrapper


def get_asgi_environ(scope, method_info):
    asgi_environ = {}
    headers_list = scope.get("headers")
    for each_header_pair in headers_list:
        if str(each_header_pair[0].decode()) == method_info.get(DT_LK_KEY):
            asgi_environ[str(each_header_pair[0].decode())] = each_header_pair[1].decode()

        if str(each_header_pair[0].decode()) == HTTP:
            asgi_environ["HTTP"] = each_header_pair[1].decode()

    asgi_environ.update(
        {
            path_info_str: scope["path"],
            query_string_str: str(scope[query_string_str.lower()]),
            request_method_str: scope["method"],
            server_port_str: str(scope["server"][1]),
        }
    )
    return asgi_environ


def asgi_wrapper(original, module, method_info):
    async def wrapper(self, scope, send, receive):
        if scope is None or scope.get("path") is None:
            import inspect

            if inspect.iscoroutinefunction(original):
                res = await original(self, scope, send, receive)
            else:
                res = original(self, scope, send, receive)
            return res

        cur_txn = None
        res = None
        agent = get_agent()
        try:
            asgi_environ = get_asgi_environ(scope, method_info)
            tracker_info = create_tracker_info(module, method_info)
            cur_txn = agent.check_and_create_webtxn(asgi_environ, tracker_info)
            if method_info.get(DT_LK_KEY):
                license_key_from_req = asgi_environ.get(method_info.get(DT_LK_KEY))
                handle_dt_headers(license_key_from_req)
        except:
            agentlogger.exception("in asgi wrapper")
        try:
            import inspect

            if inspect.iscoroutinefunction(original):
                res = await original(self, scope, send, receive)
            else:
                res = original(self, scope, send, receive)
            agent.end_txn(cur_txn, res)
        except Exception as exc:
            agent.end_txn(cur_txn, err=exc)
            raise exc
        finally:
            clear_cur_context()
        return res

    return wrapper


def background_wrapper(original, bgtxn_name=None, module=None, method_info=None, async_root=False):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            cur_txn = None
            res = None
            agent = get_agent()
            try:
                tracker_info = create_tracker_info(module, method_info, async_root=async_root)
                txn_name = get_bgtxn_name(original, tracker_info["name"], bgtxn_name)
                cur_txn = agent.check_and_create_bgtxn(txn_name, tracker_info)

            except:
                agentlogger.exception("while setting up background transaction")
            try:
                res = original(*args, **kwargs)
                agent.end_txn(cur_txn, res)
            except Exception as exc:
                agent.end_txn(cur_txn, err=exc)
                raise exc
            finally:
                clear_cur_context()
            return res
        else:
            return original(*args, **kwargs)

    return wrapper


def async_background_wrapper(original, bgtxn_name=None, module=None, method_info=None, async_root=False):
    async def wrapper(*args, **kwargs):
        cur_txn = None
        res = None
        agent = get_agent()
        err = None
        try:
            tracker_info = create_tracker_info(module, method_info, async_root=async_root)
            txn_name = get_bgtxn_name(original, tracker_info["name"], bgtxn_name)
            cur_txn = agent.check_and_create_bgtxn(txn_name, tracker_info)
        except:
            agentlogger.exception("while setting up background transaction")
        try:
            import inspect

            if inspect.iscoroutinefunction(original):
                res = await original(*args, **kwargs)
            else:
                res = original(*args, **kwargs)
            try:
                agent.end_txn(cur_txn, res)
            except:
                agentlogger.exception("in async background wrapper")
        except Exception as exc:
            err = exc
            agent.end_txn(cur_txn, err=exc)
            raise exc
        finally:
            clear_cur_context()
        return res

    return wrapper


def async_default_wrapper(original, module, method_info):
    async def wrapper(*args, **kwargs):
        if is_no_active_txn():
            if has_no_async_context():
                import inspect

                if inspect.iscoroutinefunction(original):
                    res = await original(*args, **kwargs)
                else:
                    res = original(*args, **kwargs)
                return res
            else:
                return await async_background_wrapper(
                    original, module=module, method_info=method_info, async_root=True
                )(*args, **kwargs)
        res = err = None
        agent = get_agent()
        parent_tracker = get_cur_tracker()
        tracker_info = create_tracker_info(module, method_info, parent_tracker)
        cur_tracker = agent.check_and_create_tracker(tracker_info)
        try:
            import inspect

            if inspect.iscoroutinefunction(original):
                res = await original(*args, **kwargs)
            else:
                res = original(*args, **kwargs)

        except Exception as exc:
            err = exc
            raise exc
        finally:
            handle_tracker_end(cur_tracker, method_info, args, kwargs, res, err)
            set_cur_tracker(parent_tracker)

        return res

    # special handling for flask route decorator
    wrapper.__name__ = getattr(original, "__name__", "")
    return wrapper


def default_wrapper(original, module, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            if has_no_async_context():
                return original(*args, **kwargs)
            else:
                return background_wrapper(original, module=module, method_info=method_info, async_root=True)(
                    *args, **kwargs
                )

        res = None
        err = None
        agent = get_agent()
        parent_tracker = get_cur_tracker()
        tracker_info = create_tracker_info(module, method_info, parent_tracker=parent_tracker)
        cur_tracker = agent.check_and_create_tracker(tracker_info)
        try:
            res = original(*args, **kwargs)
        except Exception as exc:
            err = exc
            raise exc
        finally:
            handle_tracker_end(cur_tracker, method_info, args, kwargs, res, err)
            set_cur_tracker(parent_tracker)

        return res

    # special handling for flask route decorator
    wrapper.__name__ = getattr(original, "__name__", "")
    return wrapper


def replace_view_wrapper(args, args_index):
    temp = list(args)
    act_method = args[args_index]
    module_name = act_method.__module__
    args_method_info = {"method": getattr(act_method, "__name__", "")}
    # Special case for flask where two different routes have same view function
    view_wrapper = getattr(act_method, "apm_view_wrapper", None)
    if view_wrapper is None:
        view_wrapper = (
            async_default_wrapper(act_method, module_name, args_method_info)
            if asyncio.iscoroutinefunction(act_method)
            else default_wrapper(act_method, module_name, args_method_info)
        )
        try:
            setattr(act_method, "apm_view_wrapper", view_wrapper)
        except AttributeError:
            agentlogger.exception("in args_wrapper function")
    copy_attributes(act_method, view_wrapper)
    temp[args_index] = view_wrapper
    return temp


def args_wrapper(original, module, method_info):
    def wrapper(*args, **kwargs):
        new_args = args
        if wrap_args_str in method_info:
            args_index = method_info[wrap_args_str]
            if isinstance(args, (list, tuple)) and len(args) > args_index and is_callable(args[args_index]):
                try:
                    new_args = replace_view_wrapper(args, args_index)
                except Exception:
                    agentlogger.exception("error in args wrapper")

        return original(*new_args, **kwargs)

    return wrapper

def custom_wrapper(original, module, method_info):
    if is_async(original):
        return async_default_wrapper(original, module, method_info)
    
    return background_wrapper(original, module=module, method_info=method_info)


def handle_tracker_end(tracker, method_info, args, kwargs, res, err):
    try:
        if isinstance(tracker, Tracker) is not True:
            return

        if type(method_info) is dict and extract_info_str in method_info:
            extractor = method_info[extract_info_str]
            extractor(tracker, args=args, kwargs=kwargs, return_value=res, error=err)

        tracker.end_tracker(err=err)
    except Exception:
        agentlogger.exception("While handling tracker end")


def copy_attributes(source, dest):
    try:
        for att in source.__dict__:
            setattr(dest, att, getattr(source, att))

    except Exception as exc:
        agentlogger.info(f"copying attribute: {str(exc)}")


def get_bgtxn_name(original, tracker_name="", bgtxn_name=None):
    if is_non_empty_string(bgtxn_name):
        return bgtxn_name
    elif is_non_empty_string(tracker_name):
        return tracker_name
    else:
        return getattr(original, "__name__", "annonymus_background_transaction")


def handle_dt_headers(license_key_from_req):
    dtdata = None
    try:
        if license_key_from_req == get_agent().get_config().get_license_key_for_dt():
            cur_txn = get_cur_txn()
            dtdata = {
                DT_TXN_NAME: cur_txn.get_normalized_txn_name(),
                DT_ST_TIME: str(cur_txn.get_start_time()),
                DT_INS_ID: get_agent().get_ins_info().get_instance_id(),
            }
            cur_txn.set_dt_response_headers(json.dumps(dtdata))
    except:
        agentlogger.exception("while processing distributed trace headers")
    return dtdata


def update_application_name(name):
    agent = get_agent()
    if agent:
        agent.get_config().update_app_name(name)
        update_handler_file_name(name)
