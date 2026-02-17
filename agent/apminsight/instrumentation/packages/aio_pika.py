
from urllib.parse import urlparse
from apminsight import constants
from apminsight.logger import agentlogger
from apminsight.instrumentation.wrapper import async_default_wrapper

def set_connection_details_from_url(tracker, url):
    try:
        if url is not None:
            parsed = urlparse(str(url))
            host = parsed.hostname or "localhost"
            port = parsed.port or 5672
        else:
            host = 'localhost'
            port = 5672

        tracker.set_info({constants.host_str: host, constants.port_str: port})

    except Exception as exc:
        agentlogger.info("Error In fetching host and port details in aio_pika")

def set_connection_details_from_channel(tracker, channel):
    try:
        connection = getattr(channel, '_connection', None)
        if connection:
            url = getattr(connection, 'url', None)
            set_connection_details_from_url(tracker, url)
    except Exception as exc:
        agentlogger.info("Error In fetching connection details from channel in aio_pika" + str(exc))

def extract_connection_info(tracker, args=(), kwargs={}, return_value=None, error=None):
    url = args[0] if (args and len(args) > 0) else None
    set_connection_details_from_url(tracker, url)

def extract_publish_details(tracker, args=(), kwargs={}, return_value=None, error=None):
    try:
        channel = getattr(args[0], 'channel', None)
        if channel is not None:
            set_connection_details_from_channel(tracker, channel)

        routing_key = args[2] if len(args) > 2 else kwargs.get('routing_key', '')
        exchange_name = getattr(args[0], 'name', '') or 'default'
        if isinstance(routing_key, str) and len(routing_key) > 0 and isinstance(exchange_name, str) and len(exchange_name) > 0:
            tracker.set_tracker_name(f"publish/{routing_key}/{exchange_name}: {tracker.get_tracker_name()}")
    except Exception as exc:
        agentlogger.info("Error In extracting publish details in aio_pika" + str(exc))

def extract_consumer_details(tracker, args=(), kwargs={}, return_value=None, error=None):
    try:
        channel = getattr(args[0], 'channel', None)
        if channel is not None:
            set_connection_details_from_channel(tracker, channel)
        queue_name = getattr(args[0], 'name', '') or ''
        if isinstance(queue_name, str) and len(queue_name) > 0:
            tracker.set_tracker_name(f"consume/{queue_name}: {tracker.get_tracker_name()}")
    except Exception as exc:
        agentlogger.info("Error In extracting consumer details in aio_pika" + str(exc))

def extract_declare_queue_details(tracker, args=(), kwargs={}, return_value=None, error=None):
    try:
        channel = args[0]
        if channel is not None:
            set_connection_details_from_channel(tracker, channel)

        queue_name = args[1] if len(args) > 1 else kwargs.get('name', '')
        if isinstance(queue_name, str) and len(queue_name) > 0:
            tracker.set_tracker_name(f"declare_queue/{queue_name}: {tracker.get_tracker_name()}")
    except Exception as exc:
        agentlogger.info("Error In extracting declare queue details in aio_pika" + str(exc))

module_info = {
    "aio_pika":[
        {
            constants.method_str: "connect",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_connection_info
        },
        {
            constants.method_str: "connect_robust",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_connection_info
        },
    ],
    "aio_pika.channel":[
        {
            constants.class_str: "Channel",
            constants.method_str: "declare_queue",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_declare_queue_details
        },
        {
            constants.class_str: "Channel",
            constants.method_str: "declare_exchange",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_declare_queue_details
        }
    ],
    "aio_pika.robust_channel":[
        {
            constants.class_str: "RobustChannel",
            constants.method_str: "declare_queue",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_declare_queue_details
        },{
            constants.class_str: "RobustChannel",
            constants.method_str: "declare_exchange",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_declare_queue_details
        }
    ],
    "aio_pika.exchange":[
        {
            constants.class_str: "Exchange",
            constants.method_str: "publish",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_publish_details
        }],
    "aio_pika.robust_exchange":[
        {
            constants.class_str: "RobustExchange",
            constants.method_str: "publish",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_publish_details
        }],
    "aio_pika.queue":[
        {
            constants.class_str: "Queue",
            constants.method_str: "consume",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_consumer_details
        },{
            constants.class_str: "Queue",
            constants.method_str: "get",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_consumer_details
        }],
    "aio_pika.robust_queue":[
        {
            constants.class_str: "RobustQueue",
            constants.method_str: "consume",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_consumer_details
        },{
            constants.class_str: "RobustQueue",
            constants.method_str: "get",
            constants.wrapper_str: async_default_wrapper,
            constants.component_str: constants.rabbitmq_comp,
            constants.extract_info_str: extract_consumer_details
        }],
}