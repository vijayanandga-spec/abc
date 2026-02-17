import inspect
from apminsight import constants
from apminsight.instrumentation.wrapper import (
    async_background_wrapper,
    background_wrapper,
)
from apminsight.logger import agentlogger


def wrap_cron_task(original, module, method_info):

    def bind_args(instance, job_func, *args, **kwargs):
        return instance, job_func, args, kwargs

    def wrapper(*args, **kwargs):
        wrapped_func = None
        instance, job_func, func_args, func_kwargs = bind_args(*args, **kwargs)
        try:
            task_name = getattr(args[0], "name", "")
            info = {constants.method_str: getattr(job_func, "__name__", task_name)}
            wrapper = async_background_wrapper if inspect.iscoroutine(job_func) else background_wrapper
            wrapped_func = wrapper(job_func, task_name, None, info)
        except Exception as exc:
            wrapped_func = job_func
            agentlogger.info("Exception in wrap_cron_task", str(exc))

        return original(instance, wrapped_func, *func_args, **func_kwargs)

    return wrapper


module_info = {
    "async_cron.job": [
        {
            constants.class_str: "CronJob",
            constants.method_str: "go",
            constants.wrapper_str: wrap_cron_task,
            constants.component_str: constants.async_cron,
        }
    ],
}
