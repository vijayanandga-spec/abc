from apminsight import constants
from apminsight.logger import agentlogger
from apminsight.context import (
    get_cur_txn,
    is_no_active_txn,
    has_no_async_context,
    get_cur_async_context,
    get_cur_context,
    set_async_context,
    get_cur_tracker,
)
from apminsight.instrumentation.wrapper import (
    asgi_wrapper,
    async_default_wrapper,
    default_wrapper,
    async_background_wrapper,
    background_wrapper,
)

import inspect
import functools
import asyncio


def is_async_callable(obj):
    while isinstance(obj, functools.partial):
        obj = obj.func

    return asyncio.iscoroutinefunction(obj) or (callable(obj) and asyncio.iscoroutinefunction(obj.__call__))


def get_name(endpoint):
    if inspect.isroutine(endpoint) or inspect.isclass(endpoint):
        return endpoint.__name__
    return endpoint.__class__.__name__


def asgi_starlette_app_call(original, module, method_info):
    async def wrapper(self, scope, send, receive):
        if get_cur_txn():
            return await async_default_wrapper(original, module, method_info)(self, scope, send, receive)
        else:
            return await asgi_wrapper(original, module, method_info)(self, scope, send, receive)

    return wrapper


def starlette_func_wrapper(handler, module, method_info):
    try:
        method_info[constants.method_str] = get_name(handler)
        if is_async_callable(handler):
            new_handler = async_default_wrapper(handler, module, method_info.copy())
        else:
            new_handler = default_wrapper(handler, module, method_info.copy())
        return new_handler
    except Exception as exc:
        agentlogger.info("Exception while binding the handler in func_wrapper", str(exc))
        return new_handler


def wrap_route_call(original, module, method_info):

    def wrapper(*args, **kwargs):
        def bind_endpoint(inst, path, endpoint, *args, **kwargs):
            return inst, path, endpoint, args, kwargs

        inst, path, endpoint, bargs, bkwargs = bind_endpoint(*args, **kwargs)
        try:
            res = original(inst, path, endpoint, *bargs, **bkwargs)
        except Exception as exc:
            raise exc
        finally:
            method_info[constants.method_str] = get_name(endpoint)
            if args[0].app == endpoint:
                args[0].app = args[0].endpoint = starlette_func_wrapper(endpoint, module, method_info)
            else:
                args[0].app = async_default_wrapper(args[0].app, module, method_info.copy())
        return res

    return wrapper


def wrap_run_threadpool(original, module, method_info):

    def bind_run_in_threadpool(func, *args, **kwargs):
        return func, args, kwargs

    async def wrapper(*args, **kwargs):
        func, args, kwargs = bind_run_in_threadpool(*args, **kwargs)
        try:
            cur_context = None
            if is_no_active_txn():
                if has_no_async_context():
                    return await original(func, *args, **kwargs)
                else:
                    cur_context = get_cur_async_context()
            else:
                cur_context = get_cur_context()
                get_cur_txn().set_async_index(1)

            func = wrap_threadpool_func(cur_context, func, module, method_info.copy())
        except Exception as exc:
            agentlogger.exception(f"Starlette Exception at run threadpool , {exc}")
        return await original(func, *args, **kwargs)

    return wrapper


def wrap_threadpool_func(cur_context, original, module, method_info):

    method_info[constants.method_str] = get_name(original)

    async def async_pool_wrapper(*args, **kwargs):
        if not cur_context:
            return original(*args, **kwargs)
        set_async_context(cur_context)
        agentlogger.info(f" Wrap_threadpool in async {method_info.get(constants.method_str)}")
        return await async_default_wrapper(original, module, method_info.copy())(*args, **kwargs)

    def pool_wrapper(*args, **kwargs):
        if not cur_context:
            return original(*args, **kwargs)
        set_async_context(cur_context)
        agentlogger.info(f" Wrap_threadpool {method_info.get(constants.method_str)}")
        return default_wrapper(original, module, method_info.copy())(*args, **kwargs)

    return async_pool_wrapper if is_async_callable(original) else pool_wrapper


def wrap_exception_handler(original, module, method_info):

    def bind_exc(instance, request, exc, *args, **kwargs):
        return exc

    def exception_extract_info(tracker, args=(), kwargs={}, return_value=None, error=None):
        try:
            exc = bind_exc(*args, **kwargs)
            status_code = getattr(return_value, "status_code", 500)
            set_exc_info_status_code_details(exc, status_code)
        except Exception as exc:
            agentlogger.exception(f"Starlette Exception while setting status code {exc}")

    method_info[constants.extract_info_str] = exception_extract_info
    return starlette_func_wrapper(original, module, method_info)


def wrap_custom_exception_handler(original, module, method_info):

    def bind_exc(request, exc, *args, **kwargs):
        return exc

    def exception_extract_info(tracker, args=(), kwargs={}, return_value=None, error=None):
        try:
            exc = bind_exc(*args, **kwargs)
            status_code = getattr(return_value, "status_code", 500)
            set_exc_info_status_code_details(exc, status_code)
        except Exception as exc:
            agentlogger.exception(f"Starlette Exception while setting status code {exc}")

    method_info[constants.extract_info_str] = exception_extract_info
    return starlette_func_wrapper(original, module, method_info)


def set_exc_info_status_code_details(exc_instance, status_code):
    cur_txn = get_cur_txn()
    if cur_txn and exc_instance:
        get_cur_tracker().mark_error(exc_instance)
        cur_txn.set_status_code(status_code)


def http_exception_info(tracker, args=(), kwargs={}, return_value=None, error=None):
    def bind_http_exception_args(instance, status_code, *args, **kwargs):
        return instance, status_code

    try:
        exc_instance, status_code = bind_http_exception_args(*args, **kwargs)
        set_exc_info_status_code_details(exc_instance, status_code)
    except Exception as exc:
        agentlogger.info(f"Starlette Exception while fetching http_exception_info {exc}")


def wrap_add_exception_handler(original, module, method_info):
    def wrapper(*args, **kwargs):
        def bind_add_exception_handler(instance, exc_class_or_status_code, handler, *args, **kwargs):
            return instance, exc_class_or_status_code, handler, args, kwargs

        instance, exc_class_or_status_code, handler, args, kwargs = bind_add_exception_handler(*args, **kwargs)
        if handler:
            handler = wrap_custom_exception_handler(handler, module, method_info)
        return original(instance, exc_class_or_status_code, handler, *args, **kwargs)

    return wrapper


def server_error_handler(original, module, method_info):

    def wrapper(*args, **kwargs):
        res = None
        try:
            res = original(*args, **kwargs)
            handler = getattr(args[0], "handler", None)
            if handler:
                args[0].handler = starlette_func_wrapper(handler, module, method_info)
        except Exception as exc:
            agentlogger.info(f"Starlette Exception at server_error_handler {exc}")
            raise exc
        return res

    return wrapper


def wrap_background_task(original, module, method_info):

    async def wrapper(*args, **kwargs):
        res = None
        try:
            func = getattr(args[0], "func", None)
            if func:
                is_async = getattr(args[0], "is_async", False)
                func_name = getattr(func, "__name__", "fastapi/BackgroundTask.__call__")
                task_wrapper = async_background_wrapper if is_async else background_wrapper
                args[0].func = task_wrapper(func, func_name, module, method_info)
            res = await original(*args, **kwargs)
        except Exception as exc:
            raise exc
        return res

    return wrapper


def wrap_response(original, module, method_info):
    def wrapper(*args, **kwargs):
        res = original(*args, **kwargs)
        try:
            txn = get_cur_txn()
            status_code = getattr(args[0], "status_code", None)
            if txn and status_code:
                txn.set_status_code(int(status_code))
        except Exception as exc:
            agentlogger.info("Error while fetching status code " + str(exc))
        return res

    return wrapper


module_info = {
    "starlette.concurrency": [
        {
            constants.method_str: "run_in_threadpool",
            constants.wrapper_str: wrap_run_threadpool,
            constants.component_str: constants.starlette_comp,
        },
    ],
    "starlette.applications": [
        {
            constants.class_str: "Starlette",
            constants.method_str: "__call__",
            constants.wrapper_str: asgi_starlette_app_call,
            constants.component_str: constants.starlette_comp,
        }
    ],
    "starlette.routing": [
        {
            constants.class_str: "Route",
            constants.method_str: "__init__",
            # constants.wrap_args_str : 2,
            constants.wrapper_str: wrap_route_call,
            constants.component_str: constants.starlette_comp,
        }
    ],
    "starlette.middleware.exceptions": [
        {
            constants.class_str: "ExceptionMiddleware",
            constants.method_str: "__call__",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.starlette_comp,
        },
        {
            constants.class_str: "ExceptionMiddleware",
            constants.method_str: "http_exception",
            constants.wrapper_str: wrap_exception_handler,
            constants.component_str: constants.starlette_comp,
        },
        {
            constants.class_str: "ExceptionMiddleware",
            constants.method_str: "add_exception_handler",
            constants.wrapper_str: wrap_add_exception_handler,
            constants.component_str: constants.starlette_comp,
        },
    ],
    "starlette.exceptions": [
        {
            constants.class_str: "ExceptionMiddleware",
            constants.method_str: "__call__",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.starlette_comp,
        },
        {
            constants.class_str: "ExceptionMiddleware",
            constants.method_str: "http_exception",
            constants.wrapper_str: wrap_exception_handler,
            constants.component_str: constants.starlette_comp,
        },
        {
            constants.class_str: "ExceptionMiddleware",
            constants.method_str: "add_exception_handler",
            constants.wrapper_str: wrap_add_exception_handler,
            constants.component_str: constants.starlette_comp,
        },
        {
            constants.class_str: "HTTPException",
            constants.method_str: "__init__",
            constants.wrapper_str: default_wrapper,
            constants.extract_info_str: http_exception_info,
            constants.component_str: constants.starlette_comp,
        },
    ],
    "starlette.middleware.errors": [
        {
            constants.class_str: "ServerErrorMiddleware",
            constants.method_str: "__call__",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.starlette_comp,
        },
        {
            constants.class_str: "ServerErrorMiddleware",
            constants.method_str: "__init__",
            constants.wrapper_str: server_error_handler,
            constants.component_str: constants.starlette_comp,
        },
        {
            constants.class_str: "ServerErrorMiddleware",
            constants.method_str: "error_response",
            constants.wrapper_str: wrap_exception_handler,
            constants.component_str: constants.starlette_comp,
        },
        {
            constants.class_str: "ServerErrorMiddleware",
            constants.method_str: "debug_response",
            constants.wrapper_str: wrap_exception_handler,
            constants.component_str: constants.starlette_comp,
        },
    ],
    "starlette.background": [
        {
            constants.class_str: "BackgroundTask",
            constants.method_str: "__call__",
            constants.wrapper_str: wrap_background_task,
            constants.component_str: constants.starlette_comp,
        },
    ],
    "starlette.responses": [
        {
            constants.class_str: "Response",
            constants.method_str: "__init__",
            constants.wrapper_str: wrap_response,
            constants.component_str: constants.starlette_comp,
        }
    ],
}
