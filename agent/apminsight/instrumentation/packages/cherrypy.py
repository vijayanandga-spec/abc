from apminsight import constants
from apminsight.context import get_cur_txn, is_no_active_txn
from apminsight.logger import agentlogger
from apminsight.util import is_callable, is_non_empty_string
from apminsight.instrumentation.wrapper import wsgi_wrapper, copy_attributes, default_wrapper, update_application_name


def wrap_finalize_request(original, module, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn() or not get_cur_txn().get_dt_response_headers():
            return original(*args, **kwargs)

        cur_txn = get_cur_txn()
        try:
            response = args[0]
            response.headers[constants.DTDATA] = cur_txn.get_dt_response_headers()
        except:
            agentlogger.exception("while adding response headers for distributed trace")

        return original(*args, **kwargs)

    return wrapper


def view_wrapper(original, module, method_info):
    def wrapper(*args, **kwargs):
        try:
            res = original(*args, **kwargs)
        except Exception as exc:
            raise exc

        if isinstance(res, tuple) and len(res) == 2:
            view = res[0]
            if is_callable(view):
                try:
                    module = view.__module__
                    method_info = {"method": view.__name__}
                    new_method = default_wrapper(view, module, method_info)
                    copy_attributes(view, new_method)
                    new_result = list(res)
                    new_result[0] = new_method
                    res = tuple(new_result)

                except:
                    agentlogger.exception("Error in CherryPy view wrapper")
        return res

    return wrapper


def get_status_code(original, module, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return original(*args, **kwargs)

        cur_txn = get_cur_txn()
        try:
            res = original(*args, **kwargs)
        except Exception as exc:
            raise exc
        try:
            if res:
                status_code = res.status
                cur_txn.set_status_code(int(status_code.split(" ")[0]))
        except:
            agentlogger.exception("while getting Status Code in CherryPy application")
        return res

    return wrapper


def get_application_name(original, module, method_info):
    def bind_args(instance, root, script_name="", *args, **kwargs):
        return root, script_name

    def wrapper(*args, **kwargs):
        res = original(*args, **kwargs)
        try:
            import cherrypy

            app_name = cherrypy.config.get("app_name", None)
            root, script_name = bind_args(*args, **kwargs)
            if not is_non_empty_string(app_name):
                if root is not None:
                    app_name = getattr(root, "app_name", getattr(root, "name", None))
                if not is_non_empty_string(app_name):
                    from ..util import callable_name

                    class_name = callable_name(root) if root else None
                    app_name = class_name if is_non_empty_string(class_name) else str(script_name)
            if is_non_empty_string(app_name):
                app_name = constants.cherrypy_comp + "-" + app_name
                update_application_name(app_name)
        except Exception as exc:
            agentlogger.info("exception at cherrypy ", str(exc))
        return res

    return wrapper


module_info = {
    "cherrypy._cptree": [
        {
            constants.class_str: "Application",
            constants.method_str: "__init__",
            constants.component_str: "CHERRYPY",
            constants.wrapper_str: get_application_name,
        },
    ],
    "cherrypy._cpwsgi": [
        {
            constants.class_str: "CPWSGIApp",
            constants.method_str: "__call__",
            constants.component_str: "CHERRYPY",
            constants.DT_LK_KEY: constants.LICENSE_KEY_FOR_DT_REQUEST_HTTP,
            constants.wrapper_str: wsgi_wrapper,
        },
    ],
    "cherrypy._cprequest": [
        {
            constants.class_str: "Request",
            constants.method_str: "run",
            constants.component_str: "CHERRYPY",
            constants.wrapper_str: get_status_code,
        },
        {
            constants.class_str: "Response",
            constants.method_str: "finalize",
            constants.component_str: "CHERRYPY",
            constants.wrapper_str: wrap_finalize_request,
        },
    ],
    "cherrypy._cpdispatch": [
        {
            constants.class_str: "Dispatcher",
            constants.method_str: "find_handler",
            constants.component_str: "CHERRYPY",
            constants.wrapper_str: view_wrapper,
        }
    ],
}
