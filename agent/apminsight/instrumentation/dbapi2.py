from apminsight import constants
from apminsight.instrumentation.wrapper import default_wrapper, async_default_wrapper
from apminsight.util import is_non_empty_string
from apminsight.logger import agentlogger
from apminsight.instrumentation.proxy import WrapperObject
from apminsight.constants import db_opn_regex
import re


def track_dbapi_query_opn(tracker, args=(), kwargs={}):

    query_arg = args[0]
    if tracker.get_component() == constants.postgres_comp and hasattr(query_arg, "_wrapped"):
        query_arg = query_arg._wrapped

    if is_non_empty_string(query_arg):
        query = query_arg
    elif isinstance(query_arg, (bytes, bytearray)):
        query = query_arg.decode("utf-8")
    else:
        query = None
        agentlogger.info(f"Unknown query string format {tracker.get_component()} and {type(args[0])}")

    if query:
        tracker.set_info({constants.query_str: query})
        opn_name = query.split(" ")[0]
        if opn_name.lower() in db_opn_regex:
            regex = db_opn_regex[opn_name.lower()]
            matchobj = re.match(regex, query, re.IGNORECASE)
            if matchobj is not None:
                tracker.set_info({"opn": matchobj.group(1).lower(), "obj": matchobj.group(2)})


class CursorProxy(WrapperObject):

    def __init__(self, cursor, conn):
        super(CursorProxy, self).__init__(cursor)
        self._apm_wrap_conn = conn

    def execute(self, *args, **kwargs):
        if hasattr(self.__original__, "execute"):
            wrapper = None
            try:
                actual = self.__original__.execute
                method_info = {
                    constants.method_str: "execute",
                    constants.component_str: self._apm_wrap_conn._apm_comp_name,
                    constants.extract_info_str: self._apm_extract_query,
                    constants.is_db_tracker_str: True,
                }
                wrapper = default_wrapper(actual, self.get_complete_class_name(), method_info)
            except:
                agentlogger.exception("while instrumenting execute function")
            if wrapper is not None:
                try:
                    return wrapper(*args, **kwargs)
                except Exception as exc:
                    raise exc
        return self.__original__.execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):

        if hasattr(self.__original__, "executemany"):
            wrapper = None
            try:
                actual = self.__original__.executemany
                method_info = {
                    constants.method_str: "executemany",
                    constants.component_str: self._apm_wrap_conn._apm_comp_name,
                    constants.extract_info_str: self._apm_extract_query,
                    constants.is_db_tracker_str: True,
                }
                wrapper = default_wrapper(actual, self.get_complete_class_name(), method_info)
            except:
                agentlogger.exception("while instrumenting executemany function")
            if wrapper is not None:
                try:
                    return wrapper(*args, **kwargs)
                except Exception as exc:
                    raise exc
        return self.__original__.executemany(*args, **kwargs)

    def _apm_extract_query(self, tracker, args=(), kwargs={}, return_value=None, error=None):
        try:
            tracker.set_info(self._apm_wrap_conn._apm_host_info)
            if isinstance(args, (list, tuple)) and len(args) > 0:
                track_dbapi_query_opn(tracker, args, kwargs)
        except:
            agentlogger.exception("while extracting query")

    def get_complete_class_name(self):
        class_name = str()
        try:
            class_name = self.__original__.__class__.__module__ + "." + self.__original__.__class__.__name__
            return class_name
        except:
            agentlogger.exception("while extracting class name for cursor")

        return "Cursor"


class ConnectionProxy(WrapperObject):

    def __init__(self, conn, comp, host_info):
        super(ConnectionProxy, self).__init__(conn)
        self._apm_comp_name = comp
        self._apm_host_info = host_info

    def cursor(self, *args, **kwargs):
        real_cursor = self.__original__.cursor(*args, **kwargs)
        try:
            cur = CursorProxy(real_cursor, self)
            return cur
        except:
            agentlogger.exception("While creating CursorProxy object")
            return real_cursor

    @staticmethod
    def get_host_info(method_info, args, conn_kwargs):
        host_info = {}
        try:
            if constants.host_str in conn_kwargs:
                host_info[constants.host_str] = conn_kwargs[constants.host_str]
            elif constants.default_host_str in method_info:
                host_info[constants.host_str] = method_info[constants.default_host_str]

            if constants.port_str in conn_kwargs:
                host_info[constants.port_str] = int(conn_kwargs[constants.port_str])
            elif constants.default_port_str in method_info:
                host_info[constants.port_str] = method_info[constants.default_port_str]
        except:
            agentlogger.exception("While extracting host_info")
        return host_info

    @staticmethod
    def instrument_conn(original, module, method_info):
        def conn_wrapper(*args, **kwargs):
            try:
                conn = original(*args, **kwargs)
            except Exception as exc:
                raise exc
            if conn is not None:
                try:
                    comp = method_info.get(constants.component_str, "")
                    proxy_class = method_info.get(constants.proxy_class_str, ConnectionProxy)
                    if constants.connect_details in method_info:
                        host_info = method_info.get(constants.connect_details)(args, kwargs)
                    else:
                        host_info = proxy_class.get_host_info(method_info, args, kwargs)
                    new_conn = proxy_class(conn, comp, host_info)
                    return new_conn
                except:
                    agentlogger.exception("while creating Proxy object")

            return conn

        return conn_wrapper


class ConnectionProxySqlite(ConnectionProxy):

    def __init__(self, conn, comp, host_info):
        super(ConnectionProxySqlite, self).__init__(conn, comp, host_info)

    def execute(self, *args, **kwargs):

        if hasattr(self.__original__, "execute"):
            wrapper = None
            try:
                actual = getattr(self.__original__, "execute")
                method_info = {
                    constants.method_str: "execute",
                    constants.component_str: self._apm_comp_name,
                    constants.extract_info_str: self._apm_extract_query,
                    constants.is_db_tracker_str: True,
                }
                wrapper = default_wrapper(actual, self.get_complete_class_name(), method_info)
            except:
                agentlogger.exception("while instrumenting execute function")
            if wrapper is not None:
                try:
                    return wrapper(*args, **kwargs)
                except Exception as exc:
                    raise exc
        return self.__original__.execute(*args, **kwargs)

    def executemany(self, *args, **kwargs):

        if hasattr(self.__original__, "executemany"):
            wrapper = None
            try:
                actual = getattr(self.__original__, "executemany")
                method_info = {
                    constants.method_str: "executemany",
                    constants.component_str: self._apm_comp_name,
                    constants.extract_info_str: self._apm_extract_query,
                    constants.is_db_tracker_str: True,
                }
                wrapper = default_wrapper(actual, self.get_complete_class_name(), method_info)
            except:
                agentlogger.exception("while instrumenting executemany function")
            if wrapper is not None:
                try:
                    return wrapper(*args, **kwargs)
                except Exception as exc:
                    raise exc
        return self.__original__.executemany(*args, **kwargs)

    def _apm_extract_query(self, tracker, args=(), kwargs={}, return_value=None, error=None):
        try:
            tracker.set_info(self._apm_host_info)
            if isinstance(args, (list, tuple)) and len(args) > 0:
                track_dbapi_query_opn(tracker, args, kwargs)

        except:
            agentlogger.exception("while extracting query")

    def get_complete_class_name(self):
        class_name = str()
        try:
            class_name = self.__original__.__class__.__module__ + "." + self.__original__.__class__.__name__
            return class_name
        except:
            agentlogger.exception("while extracting class name for cursor")

        return "sqlite3.Connection"


class ConnectionProxyPyodbc(ConnectionProxy):

    def __init__(self, conn, comp, host_info):
        super(ConnectionProxyPyodbc, self).__init__(conn, comp, host_info)

    def get_complete_class_name(self):
        class_name = str()
        try:
            class_name = self.__original__.__class__.__module__ + "." + self.__original__.__class__.__name__
            return class_name
        except:
            agentlogger.exception("while extracting class name for cursor")

        return "Pyodbc.Connection"

    def get_database_port_details(driver):
        driver_string = driver.lower()
        if "sql server" in driver_string or "mssql" in driver_string:
            return 1433

        elif "mysql" in driver_string:
            return 3306

        elif "postgres" in driver_string:
            return 5432

        elif "cassandra" in driver_string:
            return 9042

    @classmethod
    def get_server_details(cls, conn_kwargs):
        server_details = {}
        if conn_kwargs.get("server"):
            host_details = conn_kwargs.get("server").split(",")
            if len(host_details) > 1:
                server_details[constants.host_str] = host_details[0]
                server_details[constants.port_str] = int(host_details[1])
                return server_details
            else:
                server_details[constants.host_str] = host_details[0]

        elif conn_kwargs.get(constants.host_str):
            server_details[constants.host_str] = conn_kwargs[constants.host_str]

        else:
            server_details[constants.host_str] = constants.localhost_str

        if conn_kwargs.get(constants.port_str):
            server_details[constants.port_str] = conn_kwargs[constants.port_str]

        elif conn_kwargs.get("driver"):
            server_details[constants.port_str] = cls.get_database_port_details(conn_kwargs.get("driver"))

        else:
            server_details[constants.port_str] = 0000

        return server_details

    @classmethod
    def get_host_info(cls, method_info, args, conn_kwargs):
        host_info = {}
        try:
            if args and isinstance(args[0], str):
                conn_string = args[0]
                for conn_arg in conn_string.split(";"):
                    key_val = conn_arg.split("=")
                    conn_kwargs[key_val[0].lower()] = key_val[1]
            host_info.update(cls.get_server_details(conn_kwargs))

        except:
            agentlogger.exception("While extracting host_info")
        return host_info


class AsyncpgConnectionProxy(WrapperObject):

    def __init__(self, conn, comp, host_info):
        super(AsyncpgConnectionProxy, self).__init__(conn)
        self._apm_comp_name = comp
        self._apm_host_info = host_info

    async def execute(self, *args, **kwargs):

        if hasattr(self.__original__, "execute"):
            wrapper = None
            try:
                actual = getattr(self.__original__, "execute")
                method_info = {
                    constants.method_str: "execute",
                    constants.component_str: self._apm_comp_name,
                    constants.extract_info_str: self._apm_extract_query,
                    constants.is_db_tracker_str: True,
                }
                wrapper = async_default_wrapper(actual, self.get_complete_class_name(), method_info)
            except:
                agentlogger.exception("while instrumenting execute function")
            if wrapper is not None:
                try:
                    return await wrapper(*args, **kwargs)
                except Exception as exc:
                    raise exc
        return await self.__original__.execute(*args, **kwargs)

    async def executemany(self, *args, **kwargs):

        if hasattr(self.__original__, "executemany"):
            wrapper = None
            try:
                actual = getattr(self.__original__, "executemany")
                method_info = {
                    constants.method_str: "executemany",
                    constants.component_str: self._apm_comp_name,
                    constants.extract_info_str: self._apm_extract_query,
                    constants.is_db_tracker_str: True,
                }
                wrapper = async_default_wrapper(actual, self.get_complete_class_name(), method_info)
            except:
                agentlogger.exception("while instrumenting executemany function")
            if wrapper is not None:
                try:
                    return await wrapper(*args, **kwargs)
                except Exception as exc:
                    raise exc
        return await self.__original__.executemany(*args, **kwargs)

    @staticmethod
    def get_host_info(method_info, args, conn_kwargs):
        host_info = {}
        try:
            if constants.host_str in conn_kwargs:
                host_info[constants.host_str] = conn_kwargs[constants.host_str]
            elif constants.default_host_str in method_info:
                host_info[constants.host_str] = method_info[constants.default_host_str]

            if constants.port_str in conn_kwargs:
                host_info[constants.port_str] = int(conn_kwargs[constants.port_str])
            elif constants.default_port_str in method_info:
                host_info[constants.port_str] = method_info[constants.default_port_str]
        except:
            agentlogger.exception("While extracting host_info")
        return host_info

    def _apm_extract_query(self, tracker, args=(), kwargs={}, return_value=None, error=None):
        try:
            tracker.set_info(self._apm_host_info)
            if isinstance(args, (list, tuple)) and len(args) > 0:
                track_dbapi_query_opn(tracker, args, kwargs)
        except:
            agentlogger.exception("while extracting query")

    def get_complete_class_name(self):
        class_name = str()
        try:
            class_name = self.__original__.__class__.__module__ + "." + self.__original__.__class__.__name__
            return class_name
        except:
            agentlogger.exception("while extracting class name for cursor")

        return "asyncpg.Connection"

    @staticmethod
    def instrument_conn(original, module, method_info):
        async def conn_wrapper(*args, **kwargs):
            try:
                conn = await original(*args, **kwargs)
            except Exception as exc:
                raise exc
            if conn is not None:
                try:
                    comp = method_info.get(constants.component_str, "")
                    proxy_class = method_info.get(constants.proxy_class_str, AsyncpgConnectionProxy)
                    host_info = proxy_class.get_host_info(method_info, args, kwargs)
                    new_conn = proxy_class(conn, comp, host_info)
                    return new_conn
                except:
                    agentlogger.exception("while creating Proxy object")

            return conn

        return conn_wrapper
