from apminsight import constants
from apminsight.util import is_non_empty_string
from apminsight.logger import agentlogger
from apminsight.constants import db_opn_regex
from apminsight.instrumentation.dbapi2 import ConnectionProxy
import re


def track_mysql_query_opn(tracker, args, kwargs):
    query = ""
    if is_non_empty_string(args[1]):
        query = args[1]

    elif isinstance(args[1], (bytes, bytearray)):
        query = args[1].decode("utf-8")

    if query:
        tracker.set_info({constants.query_str: query})
        opn_name = query.split(" ")[0]
        if opn_name.lower() in db_opn_regex:
            regex = db_opn_regex[opn_name.lower()]
            matchobj = re.match(regex, query, re.IGNORECASE)
            if matchobj is not None:
                tracker.set_info({constants.OPERATION: matchobj.group(1).lower(), constants.OBJECT: matchobj.group(2)})


def extract_query(tracker, args=(), kwargs={}, return_value=None, error=None):

    if isinstance(args, (list, tuple)) and len(args) > 1:
        track_mysql_query_opn(tracker, args, kwargs)
        try:
            host = args[0].connection.host
            port = args[0].connection.port
            tracker.set_info({constants.host_str: host, constants.port_str: port})
        except:
            agentlogger.exception("Extracting host info from MYSQL query")


module_info = {
    "pymysql": [
        {
            constants.method_str: "connect",
            constants.component_str: constants.mysql_comp,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.proxy_class_str: ConnectionProxy,
        },
        {
            constants.method_str: "Connection",
            constants.component_str: constants.mysql_comp,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.proxy_class_str: ConnectionProxy,
        },
        {
            constants.method_str: "Connect",
            constants.component_str: constants.mysql_comp,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.proxy_class_str: ConnectionProxy,
        }
    ],
    "MySQLdb.connections": [
        {
            constants.method_str: "connect",
            constants.component_str: constants.mysql_comp,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.proxy_class_str: ConnectionProxy,
        },
        {
            constants.method_str: "Connection",
            constants.component_str: constants.mysql_comp,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.proxy_class_str: ConnectionProxy,
        },
        {
            constants.method_str: "Connect",
            constants.component_str: constants.mysql_comp,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.proxy_class_str: ConnectionProxy,
        }
    ],
}
