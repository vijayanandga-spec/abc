from apminsight import constants
from apminsight.context import (
    is_no_active_txn,
    has_no_async_context,
    get_cur_async_context,
    get_cur_context,
    get_cur_txn,
    set_async_context,
)
from apminsight.logger import agentlogger


def wrap_submit(original, module_name, method_info):
    def wrapper(*args, **kwargs):
        cur_context = None
        if is_no_active_txn():
            if has_no_async_context():
                return original(*args, **kwargs)
            else:
                cur_context = get_cur_async_context()
        else:
            cur_context = get_cur_context()
            get_cur_txn().set_async_index(1)

        if "fn" in kwargs:
            fn = kwargs.pop("fn")
            executer_insance, *fn_args = args
            return original(executer_insance, new_thread_func, cur_context, fn, *fn_args, **kwargs)
        if len(args) >= 2:
            executer_insance, fn, *fn_args = args
            return original(executer_insance, new_thread_func, cur_context, fn, *fn_args, **kwargs)
        return original(*args, **kwargs)

    return wrapper


def new_thread_func(cur_context, original, *args, **kwargs):

    if not cur_context:
        return original(*args, **kwargs)
    try:
        set_async_context(cur_context)
    except:
        agentlogger.exception("while setting the propagated context in the new asynchronous thread")
    res = original(*args, **kwargs)
    return res


module_info = {
    "concurrent.futures": [
        {
            constants.class_str: "ThreadPoolExecutor",
            constants.method_str: "submit",
            constants.wrapper_str: wrap_submit,
            constants.component_str: constants.python_comp,
        }
    ],
}
