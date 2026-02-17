from apminsight import constants
from apminsight.instrumentation.wrapper import default_wrapper


def instance_info(channel):
    host, port = None, 5672
    try:
        connection = channel.connection
        if not hasattr(connection, "params") and hasattr(connection, "_impl"):
            connection = connection._impl

        host = connection.params.host
        port = connection.params.port
    except Exception:
        host = None

    return host,port

def extract_info(tracker, args=(), kwargs={}, return_value=None, error=None):
    host, port = instance_info(args[0])
    tracker.set_info({constants.host_str: host, constants.port_str: port})


module_info = {
    "pika.channel": [{
            constants.class_str : "Channel",
            constants.method_str: "basic_publish",
            constants.component_str: constants.rabbitmq_comp,
            constants.wrapper_str: default_wrapper,
            constants.extract_info_str: extract_info
        },{
            constants.class_str : "Channel",
            constants.method_str: "basic_get",
            constants.component_str: constants.rabbitmq_comp,
            constants.wrapper_str: default_wrapper,
            constants.extract_info_str: extract_info
        # },{
        #     constants.class_str : "Channel",
        #     constants.method_str: "basic_consume",
        #     constants.component_str: constants.rabbitmq_comp,
        #     constants.wrapper_str: default_wrapper,
        }
    ]
}