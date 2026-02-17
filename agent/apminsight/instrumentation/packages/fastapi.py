from apminsight import constants
from apminsight.logger import agentlogger
from apminsight.context import is_no_active_txn
from apminsight.instrumentation.wrapper import asgi_wrapper, async_default_wrapper


def wrap_endpoint_function(original, module, method_info):
    async def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return await original(*args, **kwargs)
        name = None
        module_name = module
        try:
            dependant = kwargs["dependant"]
            name = dependant.call.__qualname__
            module_name = dependant.call.__module__
        except Exception:
            agentlogger.exception("Fastapi while extracting endpoint function name")
        if name is not None:
            method_info[constants.method_str] = name
            return await async_default_wrapper(original, module_name, method_info.copy())(*args, **kwargs)
        else:
            return await original(*args, **kwargs)

    return wrapper


module_info = {
    "fastapi.applications": [
        {
            constants.class_str: "FastAPI",
            constants.method_str: "__call__",
            constants.wrapper_str: asgi_wrapper,
            constants.component_str: constants.fastapi_comp,
        }
    ],
    "fastapi.routing": [
        {
            constants.method_str: "run_endpoint_function",
            constants.wrapper_str: wrap_endpoint_function,
            constants.component_str: constants.fastapi_comp,
        }
    ],
}
