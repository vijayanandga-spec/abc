from apminsight import constants
from apminsight.instrumentation.dbapi2 import ConnectionProxy

module_info = {
    "pymssql": [
        {
            constants.method_str: "connect",
            constants.component_str: constants.mssql_comp,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.default_host_str: constants.localhost_str,
            constants.default_port_str: 1433,
            constants.proxy_class_str: ConnectionProxy,
        }
    ]
}
