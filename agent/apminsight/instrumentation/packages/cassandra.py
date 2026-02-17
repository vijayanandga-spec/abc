from apminsight import constants
from apminsight.util import is_non_empty_string
from apminsight.logger import agentlogger
from apminsight.constants import db_opn_regex
import re


def track_cassandra_query_opn(tracker, args, kwargs):
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
                tracker.set_info({"opn": matchobj.group(1).lower(), "obj": matchobj.group(2)})


def extract_query(tracker, args=(), kwargs={}, return_value=None, error=None):

    if isinstance(args, (list, tuple)) and len(args) > 1:
        track_cassandra_query_opn(tracker, args, kwargs)

    try:
        (host, port) = str(return_value.response_future.coordinator_host).split(":")
        port = int(port)
        tracker.set_info({constants.host_str: host, constants.port_str: port})

    except:
        agentlogger.exception("Extracting the Host for CASSANDRA query")


module_info = {
    "cassandra.cluster": [
        {
            constants.class_str: "Cluster",
            constants.method_str: "connect",
            constants.component_str: constants.cassandra_comp,
        },
        {
            constants.class_str: "Cluster",
            constants.method_str: "shutdown",
            constants.component_str: constants.cassandra_comp,
        },
        {
            constants.class_str: "Session",
            constants.method_str: "execute",
            constants.component_str: constants.cassandra_comp,
            constants.extract_info_str: extract_query,
            constants.is_db_tracker_str: True,
        },
    ],
}
