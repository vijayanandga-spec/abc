from apminsight import constants
from apminsight.util import is_non_empty_string
from apminsight.agentfactory import get_agent
from apminsight.logger import agentlogger
from apminsight.constants import db_opn_regex
from apminsight.instrumentation.dbapi2 import AsyncpgConnectionProxy
import re


def extract_query(tracker, args=(), kwargs={}, return_value=None, error=None):
    threshold = get_agent().get_threshold()
    if threshold.is_sql_capture_enabled() is not True:
        return

    if isinstance(args, (list, tuple)) and len(args) > 1:
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


def wrap_connect(original, module, method_info):
    async def wrapper(*args, **kwargs):
        res = await original(*args, **kwargs)
        try:
            host = kwargs.get("host")
            port = kwargs.get("port")
            setattr(res, "host_apm", host)
            setattr(res, "port_apm", port)
        except:
            agentlogger.exception("while getting host name and port number for the asyncpg query")
        return res

    return wrapper


module_info = {
    "asyncpg": [
        {
            constants.method_str: "connect",
            constants.component_str: constants.postgres_comp,
            constants.wrapper_str: AsyncpgConnectionProxy.instrument_conn,
            constants.default_host_str: constants.localhost_str,
            constants.default_port_str: 5432,
            constants.proxy_class_str: AsyncpgConnectionProxy,
        }
    ],
}
