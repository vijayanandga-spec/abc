from apminsight import constants
from apminsight.util import is_non_empty_string


def extract_info(tracker, args=(), kwargs={}, return_value=None, error=None):
    if isinstance(args, (list, tuple)) and len(args) > 1:
        if is_non_empty_string(args[1]):
            tracker.set_info({constants.OPERATION: args[1]})
        elif isinstance(args[1], (bytes, bytearray)):
            opn = args[1].decode("utf-8")
            tracker.set_info({constants.OPERATION: opn})

        if hasattr(args[0], "server"):
            server = args[0].server
            if isinstance(server, (list, tuple)) and len(server) == 2:
                tracker.set_info({constants.host_str: server[0], constants.port_str: server[1]})


module_info = {
    "pymemcache.client.base": [
        {
            constants.class_str: "Client",
            constants.method_str: "_fetch_cmd",
            constants.component_str: constants.memcache_comp,
            constants.extract_info_str: extract_info,
        },
        {
            constants.class_str: "Client",
            constants.method_str: "_store_cmd",
            constants.component_str: constants.memcache_comp,
            constants.extract_info_str: extract_info,
        },
        {
            constants.class_str: "Client",
            constants.method_str: "_misc_cmd",
            constants.component_str: constants.memcache_comp,
            constants.extract_info_str: extract_info,
        },
    ]
}
