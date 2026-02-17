
"""
Instrumenting methods by wrapping method using modules address

Default instrumentation:
    Supported modules will automatically by loading modules using __import_module
    This will happen when you initialize apminsight package

On demand instrument module:
    By wrapping inbuilt method import, we can get the name of the module
    imported during runtime, then we can wrap method at run time

wrapt module patches.py: it follows default instrumentation
    resolve_path  will load module and get address from sys.modules dict
    setattr will create a attribute if not present and value for a object
    wrap object method replaces the original method with new wrapper method
"""
import sys
from importlib import import_module
from apminsight import constants
from apminsight.logger import agentlogger
from apminsight.util import is_callable
from apminsight.constants import class_str, method_str, wrapper_str, wrap_args_str
from .wrapper import default_wrapper, args_wrapper
from .packages import inbuilt_modules_info, modules_info, on_module_load_info
from .util import is_instrument_on_module_load

def check_and_instrument(module_name, act_module, modules_info):
    if not module_name:
        return

    if hasattr(act_module, constants.APM_INSTRUMENTED):
        return

    if module_name in modules_info.keys():
        methods_info = modules_info.get(module_name)
        for each_method_info in methods_info:
            instrument_method(module_name, act_module, each_method_info)

        setattr(act_module, constants.APM_INSTRUMENTED, True)
        agentlogger.info(module_name + " instrumented")


def instrument_method(module_name, act_module, method_info):
    parent_ref = act_module
    class_name = ""

    if type(method_info) is not dict:
        return

    if class_str in method_info:
        class_name = method_info.get(class_str)
        if hasattr(act_module, class_name):
            parent_ref = getattr(act_module, class_name)
            module_name = module_name + "." + class_name

    instrument_methods = method_info.get(method_str, "")
    if isinstance(instrument_methods, str):
        method_list = []
        method_list.append(instrument_methods)
    else:
        method_list = instrument_methods

    for method in method_list:
        if hasattr(parent_ref, method):
            original = getattr(parent_ref, method)
            if not is_callable(original):
                return
            method_info[method_str] = method

            # use default wrapper if there is no wrapper attribute
            wrapper_factory = default_wrapper
            if wrap_args_str in method_info:
                wrapper_factory = args_wrapper
            elif wrapper_str in method_info:
                wrapper_factory = method_info.get(wrapper_str)

            """
            we are changing the same method info object to append method_str,
            it will change existing method info object
            """
            wrapper = wrapper_factory(original, module_name, method_info.copy())
            setattr(parent_ref, method, wrapper)


initialized = False


def instrument_modules(modules_info):
    for module_name in modules_info:
        try:
            if module_name in sys.modules:
                agentlogger.info(f"{module_name} is already imported so we are trying to instrument it")
                act_module = sys.modules[module_name]
                check_and_instrument(module_name, act_module, modules_info)
        except Exception:
            agentlogger.info(module_name +' is not present')


def wrap_import(original):
    def wrapper(*args, **kwargs):
        module_name = None
        if len(args)>=1:
            module_name = args[0]
        if module_name in on_module_load_info:
            res =  original(*args, **kwargs)
            try:
                check_and_instrument(module_name, res, modules_info)
            except:
                agentlogger.exception('while instrumenting '+module_name+' module')
            return res
        return original(*args, **kwargs)
    return wrapper

def patch_importlib():
    builtins = import_module('importlib._bootstrap')
    original = getattr(builtins, '_find_and_load')
    setattr(builtins, '_find_and_load', wrap_import(original))


def init_instrumentation():
    try:
        on_module_load_info.update(modules_info)
        patch_importlib()
        instrument_modules(inbuilt_modules_info)
        instrument_modules(modules_info)
    except:
        agentlogger.exception('while instrumenting BUILTINS module')
