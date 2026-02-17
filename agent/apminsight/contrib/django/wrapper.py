from importlib import import_module
from apminsight.instrumentation import instrument_method
from apminsight.logger import agentlogger
from apminsight import constants


def instrument_middlewares():
    methods = ["process_request", "process_view", "process_exception", "process_template_response", "process_response"]
    try:
        from django.conf import settings

        middleware = getattr(settings, "MIDDLEWARE", None) or getattr(settings, "MIDDLEWARE_CLASSES", None)

        if middleware is None:
            return

        for each in middleware:
            module_path, class_name = each.rsplit(".", 1)
            act_module = import_module(module_path)
            for each_method in methods:
                method_info = {
                    constants.class_str: class_name,
                    constants.method_str: each_method,
                    constants.component_str: constants.middleware,
                }
                instrument_method(module_path, act_module, method_info)

    except Exception as exc:
        agentlogger("django middleware instrumentation error" + exc)
