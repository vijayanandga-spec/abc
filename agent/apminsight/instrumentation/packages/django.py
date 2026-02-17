from apminsight import constants
from apminsight.instrumentation.wrapper import (
    wsgi_wrapper,
    default_wrapper,
    handle_dt_headers,
    asgi_wrapper,
    update_application_name,
)
from apminsight.context import is_no_active_txn, get_cur_txn, get_cur_tracker
from apminsight.logger import agentlogger
from apminsight.instrumentation.util import callable_name, get_module, caught_exc_wrapper

from apminsight.util import is_non_empty_string


@caught_exc_wrapper
def instrument_installed_apps():
    from apminsight.instrumentation import instrument_method

    for each_module, method_info in apps_module_info.items():
        act_module = get_module(each_module)
        if act_module:
            for each_info in method_info:
                instrument_method(each_module, act_module, each_info)
        agentlogger.info(each_module + " is instrumented")


@caught_exc_wrapper
def instrument_django_middlewares():
    from django.conf import settings
    from apminsight import get_agent

    wsgi_app = settings.WSGI_APPLICATION
    appname = wsgi_app.split(".")[0] if wsgi_app else None
    if appname and get_agent() and get_agent().get_config().get_app_name() == constants.DEFAULT_APM_APP_NAME:
        get_agent().get_config().set_app_name(appname)

    middleware = getattr(settings, constants.MIDDLEWARE, getattr(settings, constants.MIDDLEWARE_CLASSES, None))

    if middleware is None:
        return

    from apminsight.instrumentation import instrument_method

    methods = ["process_request", "process_view", "process_exception", "process_template_response", "process_response"]

    for each in middleware:
        module_path, class_name = each.rsplit(".", 1)
        act_module = get_module(module_path)
        for each_method in methods:
            method_info = {
                constants.class_str: class_name,
                constants.method_str: each_method,
                constants.component_str: constants.middleware,
            }
            instrument_method(module_path, act_module, method_info)


def wrap_get_response(original, module, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return original(*args, **kwargs)
        try:
            response = original(*args, **kwargs)
        except Exception as exc:
            raise exc
        try:
            get_cur_txn().set_status_code(response.status_code)
            request = args[1]
            license_key_from_req = request.headers.get(constants.LICENSE_KEY_FOR_DT_REQUEST)
            dtdata = handle_dt_headers(license_key_from_req)
            if dtdata is not None:
                response.headers[constants.DTDATA] = dtdata
        except:
            agentlogger.exception("while processing distributed trace headers")
        return response

    # special handling for flask route decorator
    wrapper.__name__ = original.__name__
    return wrapper


def wrap_get_application(original, module, method_info):
    def wrapper(*args, **kwargs):
        res = original(*args, **kwargs)
        try:
            from django.conf import settings

            app_name = getattr(settings, "WSGI_APPLICATION", getattr(settings, "ASGI_APPLICATION", None))
            if is_non_empty_string(app_name):
                app_name = app_name.split(".")[0]
                update_application_name(constants.django_comp + "-" + str(app_name))

            instrument_django_middlewares()
            instrument_installed_apps()
        except Exception as exc:
            agentlogger.info("Exception while updating app_name in django")
        return res

    return wrapper


def wrap_response_for_exception(original, module, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return original(*args, **kwargs)
        try:
            response = original(*args, **kwargs)
        except Exception as exc:
            raise exc
        if response is not None:
            try:
                cur_txn = get_cur_txn()
                cur_txn.set_status_code(int(response.status_code))
            except:
                agentlogger.exception("while capturing status code in django application")
        return response

    return wrapper


def wrap_async_send_response(original, module, method_info):
    async def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return await original(*args, **kwargs)
        try:
            cur_txn = get_cur_txn()
            if len(args) > 2:
                response = args[1]
                cur_txn.set_status_code(int(response.status_code))
        except:
            agentlogger.exception("while extracting status code")
        return await original(*args, **kwargs)

    return wrapper


module_info = {
    "django.core.handlers.asgi": [
        {
            constants.class_str: "ASGIHandler",
            constants.method_str: "__call__",
            constants.wrapper_str: asgi_wrapper,
            constants.component_str: constants.django_comp,
        },
        {
            constants.class_str: "ASGIHandler",
            constants.method_str: "send_response",
            constants.wrapper_str: wrap_async_send_response,
            constants.component_str: constants.django_comp,
        },
    ],
    "django.core.handlers.wsgi": [
        {
            constants.class_str: "WSGIHandler",
            constants.method_str: "__call__",
            constants.wrapper_str: wsgi_wrapper,
            constants.component_str: constants.django_comp,
        }
    ],
    "django.core.handlers.base": [
        {
            constants.class_str: "BaseHandler",
            constants.method_str: "get_response",
            constants.wrapper_str: wrap_get_response,
            constants.component_str: constants.django_comp,
        }
    ],
    "django.conf.urls": [
        {constants.method_str: "url", constants.wrap_args_str: 1, constants.component_str: constants.django_comp}
    ],
    "django.urls": [
        {constants.method_str: "path", constants.wrap_args_str: 1, constants.component_str: constants.django_comp}
    ],
    "django.template": [
        {constants.class_str: "Template", constants.method_str: "render", constants.component_str: constants.template}
    ],
    "django.core.wsgi": [
        {
            constants.method_str: "get_wsgi_application",
            constants.wrapper_str: wrap_get_application,
            constants.component_str: constants.django_comp,
        }
    ],
    "django.core.asgi": [
        {
            constants.method_str: "get_asgi_application",
            constants.wrapper_str: wrap_get_application,
            constants.component_str: constants.django_comp,
        }
    ],
}


def dispatch_wrapper(original, module, method_info):
    def wrapper(*args, **kwargs):
        def bind_request(instance, request, *args, **kwargs):
            return request

        try:
            if get_cur_txn() is None:
                return original(*args, **kwargs)
            request = bind_request(*args, **kwargs)
            view = args[0]
            request_method = request.method.lower()
            handler = None
            if request_method in view.http_method_names:
                handler = getattr(view, request_method, view.http_method_not_allowed)
            else:
                handler = view.http_method_not_allowed

            method_name = callable_name(handler)
            view.handle_exception = exception_wrapper(view.handle_exception)
            return default_wrapper(original, "", {"method": method_name})(*args, **kwargs)
        except Exception as exc:
            raise exc

    return wrapper


def exception_wrapper(exception_handler):
    def wrapper(*args, **kwargs):
        def bind_exception(exc):
            return exc

        exc = bind_exception(*args, **kwargs)
        tracker = get_cur_tracker()
        if tracker:
            tracker.set_exception(exc)
        return exception_handler(*args, **kwargs)

    return wrapper


apps_module_info = {
    "rest_framework.views": [
        {
            constants.class_str: "APIView",
            constants.method_str: "dispatch",
            constants.wrapper_str: dispatch_wrapper,
            constants.component_str: constants.django_comp,
        }
    ],
}
