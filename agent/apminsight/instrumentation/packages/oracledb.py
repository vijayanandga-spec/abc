from apminsight import constants
from apminsight.instrumentation.dbapi2 import ConnectionProxy
from apminsight.logger import agentlogger
from apminsight.instrumentation.proxy import WrapperObject

import re

pattern = re.compile(constants.ORACLE_DSN_FORMAT)


def get_host_info(args, kwargs):
    host_info = {}
    try:
        dsn = kwargs.get("dsn", args[0] if len(args) else "")
        if isinstance(dsn, (bytes, bytearray)):
            dsn = dsn.decode("utf-8")
        match = pattern.search(dsn)
        host_info[constants.host_str] = match.group(3)
        host_info[constants.port_str] = int(match.group(4) or constants.ORACLE_DEFAULT_PORT)
    except Exception as exc:
        agentlogger.info("Exception in parsing dsn for oracle connect info " + dsn)
    return host_info


class SessionPoolProxy(WrapperObject):
    def __init__(self, pool, comp, host_info):
        super(SessionPoolProxy, self).__init__(pool)
        self._apm_comp_name = comp
        self._apm_host_info = host_info

    def acquire(self, *args, **kwargs):
        conn = self.__original__.acquire(*args, **kwargs)
        if conn is not None:
            return ConnectionProxy(conn, self._apm_comp_name, self._apm_host_info)
        return conn

    def drop(self, connection, *args, **kwargs):
        if isinstance(connection, ConnectionProxy):
            connection = connection.__original__
        return self.__original__.drop(connection, *args, **kwargs)

    def release(self, connection, *args, **kwargs):
        if isinstance(connection, ConnectionProxy):
            connection = connection.__original__
        return self.__original__.release(connection, *args, **kwargs)

    @staticmethod
    def insturment_pool(original, module, method_info):
        def pool_wrapper(*args, **kwargs):
            try:
                pool = original(*args, **kwargs)
            except Exception as exc:
                raise exc
            if pool is not None:
                try:
                    comp = method_info.get(constants.component_str, "")
                    proxy_class = method_info.get(constants.proxy_class_str, SessionPoolProxy)
                    host_info = get_host_info(args, kwargs)
                    new_conn = proxy_class(pool, comp, host_info)
                    return new_conn
                except:
                    agentlogger.exception("while creating Proxy object")

            return pool

        return pool_wrapper


module_info = {
    "cx_Oracle": [
        {
            constants.method_str: "connect",
            constants.component_str: constants.ORACLE_COMP,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.proxy_class_str: ConnectionProxy,
            constants.connect_details: get_host_info,
        },
        {
            constants.method_str: "SessionPool",
            constants.component_str: constants.ORACLE_COMP,
            constants.wrapper_str: SessionPoolProxy.insturment_pool,
            constants.proxy_class_str: SessionPoolProxy,
            constants.connect_details: get_host_info,
        },
    ],
    "oracledb": [
        {
            constants.method_str: "connect",
            constants.component_str: constants.ORACLE_COMP,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.proxy_class_str: ConnectionProxy,
            constants.connect_details: get_host_info,
        },
        {
            constants.method_str: "create_pool",
            constants.component_str: constants.ORACLE_COMP,
            constants.wrapper_str: SessionPoolProxy.insturment_pool,
            constants.proxy_class_str: SessionPoolProxy,
            constants.connect_details: get_host_info,
        },
    ],
}
