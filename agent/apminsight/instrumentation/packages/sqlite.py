from apminsight import constants
from apminsight.instrumentation.dbapi2 import ConnectionProxySqlite

module_info = {
    "sqlite3": [
        {
            constants.method_str: "connect",
            constants.component_str: constants.sqlite_comp,
            constants.wrapper_str: ConnectionProxySqlite.instrument_conn,
            constants.proxy_class_str: ConnectionProxySqlite,
        }
    ],
    "sqlite3.dbapi2": [
        {
            constants.method_str: "connect",
            constants.component_str: constants.sqlite_comp,
            constants.wrapper_str: ConnectionProxySqlite.instrument_conn,
            constants.proxy_class_str: ConnectionProxySqlite,
        }
    ],
}
