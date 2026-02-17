from apminsight import constants
from apminsight.instrumentation.dbapi2 import ConnectionProxy, ConnectionProxyPyodbc

module_info = {
    "pyodbc": [
        {
            constants.method_str: "connect",
            constants.component_str: constants.pyodbc_comp,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.proxy_class_str: ConnectionProxyPyodbc,
        }
    ],
}
