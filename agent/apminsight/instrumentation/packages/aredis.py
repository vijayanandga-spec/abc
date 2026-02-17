from apminsight import constants
from apminsight.instrumentation.wrapper import async_default_wrapper
from apminsight.util import is_non_empty_string
from apminsight.logger import agentlogger


def extract_info(tracker, args=(), kwargs={}, return_value=None, error=None):
    if isinstance(args, (list, tuple)) and len(args) > 1:
        if is_non_empty_string(args[1]):
            tracker.set_info({"opn": args[1]})
        elif isinstance(args[1], (bytes, bytearray)):
            operation = args[1].decode("utf-8")
            opn = operation.split()[0].upper()
            tracker.set_info({"opn": opn})
        try:
            command_name = args[1]
            client = args[0]
            conn = client.connection_pool.get_connection(command_name, **kwargs)
            tracker.set_info({constants.host_str: conn.host, constants.port_str: conn.port})
        except:
            agentlogger.exception("while extracting address info of the aioredis call")


module_info = {
    "aredis.client": [
        {
            constants.class_str: "StrictRedis",
            constants.method_str: "execute_command",
            constants.extract_info_str: extract_info,
            constants.component_str: constants.redis_comp,
            constants.wrapper_str: async_default_wrapper,
        }
    ],
}
