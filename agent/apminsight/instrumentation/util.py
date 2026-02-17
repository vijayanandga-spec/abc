import os
import sys
import inspect
import functools
import random
import string
from apminsight.constants import (
    PARENT_CONTEXT,
    PARENT_TRACKER,
    CONTEXT,
    TRACE_ID_STR,
    SPAN_ID_STR,
    IS_ASYNC,
    ASYNC_PARENT_CONTEXT,
    component_str,
    is_db_tracker_str,
    method_str,
)
from apminsight.metric.tracker import Tracker
from apminsight.logger import agentlogger
from apminsight.context import get_cur_async_context
from apminsight.util import is_non_empty_string


def create_tracker_info(module, method_info, parent_tracker=None, async_root=False):
    tracker_info = None
    try:
        tracker_name = ((module + ".") if is_non_empty_string(module) else "") + method_info[method_str]
        tracker_info = {"name": tracker_name}
        if isinstance(parent_tracker, Tracker):
            tracker_info[PARENT_TRACKER] = parent_tracker
            tracker_info[PARENT_CONTEXT] = parent_tracker.get_context()
        tracker_info[CONTEXT] = {
            TRACE_ID_STR: parent_tracker.get_trace_id() if parent_tracker else None,
            SPAN_ID_STR: "".join(random.choices(string.ascii_letters + string.digits, k=16)),
        }
        if async_root:
            tracker_info[IS_ASYNC] = True
            tracker_info[ASYNC_PARENT_CONTEXT] = get_cur_async_context()
        if component_str in method_info:
            tracker_info[component_str] = method_info[component_str]

        if is_db_tracker_str in method_info:
            tracker_info[is_db_tracker_str] = True

    except Exception:
        agentlogger.exception("while creating tracker info")
    finally:
        return tracker_info


def get_module(module_path):
    try:
        from importlib import import_module

        return import_module(module_path)
    except Exception as exc:
        agentlogger.info(module_path + " is not present")
    return None


def caught_exc_wrapper(func):
    def wrapper(*args, **kwargs):
        method_name = func.__name__
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            agentlogger.info("Exception in " + method_name + " " + str(exc))
        return None

    return wrapper


# Object model terminology for quick reference.
#
# class:
#   __module__: name of module in which this class was defined
#
# method:
#   __name__: name with which this method was defined
#   __qualname__: qualified name with which this method was defined
#   im_class: class object that asked for this method
#   im_func or __func__: function object containing implementation of method
#   im_self or __self__: instance to which this method is bound, or None
#
# function:
#   __name__: name with which this function was defined
#   __qualname__: qualified name with which function was defined
#   func_name: (same as __name__)
#
# descriptor:
#   __objclass__: class object that the descriptor is bound to
#
# builtin:
#   __name__: original name of this function or method
#   __self__: instance to which a method is bound, or None


def _module_name(object):
    mname = None

    # For the module name we first need to deal with the special
    # case of getset and member descriptors. In this case we
    # grab the module name from the class the descriptor was
    # being used in which is held in __objclass__.

    if hasattr(object, "__objclass__"):
        mname = getattr(object.__objclass__, "__module__", None)

    # The standard case is that we can just grab the __module__
    # attribute from the object.

    if mname is None:
        mname = getattr(object, "__module__", None)

    # An exception to that is builtins or any types which are
    # implemented in C code. For that we need to grab the module
    # name from the __class__. In doing this though, we need to
    # ensure we check for case of a bound method. In that case
    # we need to grab the module from the class of the instance
    # to which the method is bound.

    if mname is None:
        self = getattr(object, "__self__", None)
        if self is not None and hasattr(self, "__class__"):
            mname = getattr(self.__class__, "__module__", None)

    if mname is None and hasattr(object, "__class__"):
        mname = getattr(object.__class__, "__module__", None)

    # Finally, if the module name isn't in sys.modules, we will
    # format it within '<>' to denote that it is a generated
    # class of some sort where a fake namespace was used. This
    # happens for example with namedtuple classes in Python 3.

    if mname and mname not in sys.modules:
        mname = "<%s>" % mname

    # If unable to derive the module name, fallback to unknown.

    if not mname:
        mname = "<unknown>"

    return mname


def _object_context_py3(object):

    if inspect.ismethod(object):

        # In Python 3, ismethod() returns True for bound methods. We
        # need to distinguish between class methods and instance methods.
        #
        # First, test for class methods.

        cname = getattr(object.__self__, "__qualname__", None)

        # If it's not a class method, it must be an instance method.

        if cname is None:
            cname = getattr(object.__self__.__class__, "__qualname__")

        path = "%s.%s" % (cname, object.__name__)

    else:
        # For functions, the __qualname__ attribute gives us the name.
        # This will be a qualified name including the context in which
        # the function is defined in, such as an outer function in the
        # case of a nested function.

        path = getattr(object, "__qualname__", None)

        # If there is no __qualname__ it should mean it is a type
        # object of some sort. In this case we use the name from the
        # __class__. That also can be nested so need to use the
        # qualified name.

        if path is None and hasattr(object, "__class__"):
            path = getattr(object.__class__, "__qualname__")

    # Now calculate the name of the module object is defined in.

    owner = None

    if inspect.ismethod(object):
        if object.__self__ is not None:
            cname = getattr(object.__self__, "__name__", None)
            if cname is None:
                owner = object.__self__.__class__  # bound method
            else:
                owner = object.__self__  # class method

    mname = _module_name(owner or object)

    return (mname, path)


def object_context(target):
    """Returns a tuple identifying the supplied object. This will be of
    the form (module, object_path).

    """

    # Check whether the target is a functools.partial so we
    # can actually extract the contained function and use it.

    if isinstance(target, functools.partial):
        target = target.func

    # If it wasn't cached we generate the name details and then
    # attempt to cache them against the object.

    details = _object_context_py3(target)

    return details


def callable_name(object, separator="."):
    """Returns a string name identifying the supplied object. This will be
    of the form 'module:object_path'.

    If object were a function, then the name would be 'module:function. If
    a class, 'module:class'. If a member function, 'module:class.function'.

    By default the separator between the module path and the object path is
    ':' but can be overridden if necessary. The convention used by the
    Python Agent is that of using a ':' so it is clearer which part is the
    module name and which is the name of the object.

    """

    # The details are the module name and path. Join them with
    # the specified separator.

    return separator.join(object_context(object))


def is_instrument_on_module_load():
    return os.environ.get("APM_INSTRUMENT_ON_MODULE_LOAD", "false").lower() in ["true", "on", "1"]


def is_async(method):
    return inspect.iscoroutinefunction(method)
