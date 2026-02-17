from apminsight import constants
from apminsight.instrumentation.wrapper import copy_attributes
from apminsight.context import get_cur_txn, is_no_active_txn
from apminsight.instrumentation.wrapper import wsgi_wrapper
from apminsight.context import get_cur_txn, is_no_active_txn
from apminsight.logger import agentlogger
from apminsight.util import is_callable


def wrap_wsgi(original, module_name, method_info):
    def wrapper(*args, **kwargs):
        args_index = 2
        if is_callable(args[args_index]):
            try:
                act_method = args[args_index]
                temp = list(args)
                module_name = act_method.__module__
                args_method_info = {constants.method_str: act_method.__name__}
                new_method = wrap_start_response(act_method, module_name, args_method_info)
                copy_attributes(act_method, new_method)
                temp[args_index] = new_method
                args = temp
            except Exception:
                agentlogger.exception("error in args wrapper")

        return original(*args, **kwargs)

    return wrapper


def wrap_start_response(original, module_name, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn() or not get_cur_txn().get_dt_response_headers():
            return original(*args, **kwargs)
        cur_txn = get_cur_txn()
        try:
            args[1].append((constants.DTDATA, cur_txn.get_dt_response_headers()))
        except:
            agentlogger.exception("while adding response headers for distruted trace")

        return original(*args, **kwargs)

    # special handling for flask route decorator
    wrapper.__name__ = original.__name__
    return wrapper


def get_status_code(original, module_name, method_info):
    def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return original(*args, **kwargs)
        try:
            cur_txn = get_cur_txn()
            status_code = 500
            if isinstance(args, tuple) and len(args) >= 3:
                status_code = int(args[2])
            cur_txn.set_status_code(status_code)
        except:
            agentlogger.exception("Exception occured while getting Status Code")
        return original(*args, **kwargs)

    return wrapper


def get_application_name():
    """
    In Bottle we can stack multiple application of bottle instances
    to a single instance, we cant read class fullpath or reading app_name
    from config for ideintifying application name is not correct,
    In this case we are reading it as application directory
    """
    pass


module_info = {
    "bottle": [
        {
            constants.class_str: "Bottle",
            constants.method_str: "__call__",
            constants.wrapper_str: wsgi_wrapper,
            constants.DT_LK_KEY: constants.LICENSE_KEY_FOR_DT_REQUEST_HTTP,
            constants.component_str: constants.bottle_comp,
        },
        {
            constants.class_str: "Route",
            constants.method_str: "__init__",
            constants.wrap_args_str: 4,
            constants.component_str: constants.bottle_comp,
        },
        {constants.class_str: "MakoTemplate", constants.method_str: "render", constants.component_str: "MAKOTEMPLATE"},
        {
            constants.class_str: "CheetahTemplate",
            constants.method_str: "render",
            constants.component_str: "CheetahTemplate",
        },
        {
            constants.class_str: "Jinja2Template",
            constants.method_str: "render",
            constants.component_str: "Jinja2Template",
        },
        {
            constants.class_str: "SimpleTemplate",
            constants.method_str: "render",
            constants.component_str: "SimpleTemplate",
        },
        {
            constants.class_str: "BaseResponse",
            constants.method_str: "__init__",
            constants.component_str: constants.bottle_comp,
            constants.wrapper_str: get_status_code,
        },
        {
            constants.class_str: "Bottle",
            constants.method_str: "wsgi",
            constants.wrapper_str: wrap_wsgi,
            constants.component_str: constants.bottle_comp,
        },
    ],
}
