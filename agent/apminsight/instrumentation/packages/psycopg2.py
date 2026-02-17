from apminsight import constants
from apminsight.instrumentation.dbapi2 import ConnectionProxy


def wrap_register_type(original, module, method_info):
    def wrapper(*args, **kwargs):
        def get_arguments(obj, scope=None):
            return obj, scope

        obj, conn_or_curs = get_arguments(*args, **kwargs)
        if conn_or_curs:
            return original(obj, conn_or_curs.__original__)
        else:
            return original(obj)

    return wrapper


def wrap_quote_ident(original, module, method_info):
    def wrapper(*args, **kwargs):
        def get_arguments(obj, scope=None):
            return obj, scope

        obj, conn_or_curs = get_arguments(*args, **kwargs)
        if conn_or_curs:
            return original(obj, conn_or_curs.__original__)
        else:
            return original(obj)

    return wrapper


module_info = {
    "psycopg2": [
        {
            constants.method_str: "connect",
            constants.component_str: constants.postgres_comp,
            constants.wrapper_str: ConnectionProxy.instrument_conn,
            constants.default_host_str: constants.localhost_str,
            constants.default_port_str: 5432,
            constants.proxy_class_str: ConnectionProxy,
        }
    ],
    "psycopg2.extensions": [
        {
            constants.method_str: "register_type",
            constants.component_str: constants.postgres_comp,
            constants.wrapper_str: wrap_register_type,
        },
        {
            constants.method_str: "quote_ident",
            constants.component_str: constants.postgres_comp,
            constants.wrapper_str: wrap_quote_ident,
        },
    ],
    "psycopg2._psycopg": [
        {
            constants.method_str: "register_type",
            constants.component_str: constants.postgres_comp,
            constants.wrapper_str: wrap_register_type,
        }
    ],
    "psycopg2._json": [
        {
            constants.method_str: "register_type",
            constants.component_str: constants.postgres_comp,
            constants.wrapper_str: wrap_register_type,
        }
    ],
}
