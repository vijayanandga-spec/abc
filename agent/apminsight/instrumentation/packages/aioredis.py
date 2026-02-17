import copy
from apminsight import constants
from apminsight.util import is_non_empty_string
from apminsight.logger import agentlogger
from apminsight.context import get_cur_tracker, is_no_active_txn, set_cur_tracker
from apminsight.agentfactory import get_agent
from apminsight.instrumentation.util import create_tracker_info
from apminsight.instrumentation.wrapper import handle_tracker_end


async def execute_command(self, *args, **options):
    from aioredis.exceptions import ConnectionError, TimeoutError

    """Execute a command and return a parsed response"""
    await self.initialize()
    pool = self.connection_pool
    command_name = args[0]
    conn = self.connection or await pool.get_connection(command_name, **options)

    try:
        conn_object = copy.copy(conn)
        if isinstance(args, (list, tuple)) and len(args) > 0:
            tracker = get_cur_tracker()
            if is_non_empty_string(args[0]):
                tracker.set_info({"opn": args[0]})
            elif isinstance(args[0], (bytes, bytearray)):
                operation = args[0].decode("utf-8")
                opn = operation.split()[0].upper()
                tracker.set_info({"opn": opn})
            tracker.set_info({constants.host_str: conn_object.host, constants.port_str: conn_object.port})
    except:
        agentlogger.exception("while extracting details of redis call")

    try:
        await conn.send_command(*args)
        return await self.parse_response(conn, command_name, **options)
    except (ConnectionError, TimeoutError) as e:
        await conn.disconnect()
        if not (conn.retry_on_timeout and isinstance(e, TimeoutError)):
            raise
        await conn.send_command(*args)
        return await self.parse_response(conn, command_name, **options)
    finally:
        if not self.connection:
            await pool.release(conn)


def wrap_execute_command(original, module, method_info):
    async def wrapper(*args, **kwargs):
        if is_no_active_txn():
            return await original(*args, **kwargs)

        res = None
        err = None
        agent = get_agent()

        parent_tracker = get_cur_tracker()
        tracker_info = create_tracker_info(module, method_info, parent_tracker)
        cur_tracker = agent.check_and_create_tracker(tracker_info)
        try:
            res = await execute_command(*args, **kwargs)
        except Exception as exc:
            err = exc
            raise exc
        finally:
            if not cur_tracker:
                return res
            if not cur_tracker.get_info().get(constants.host_str):
                cur_tracker.get_info()[constants.host_str] = method_info.get(constants.default_host_str)
            if not cur_tracker.get_info().get(constants.port_str):
                cur_tracker.get_info()[constants.port_str] = method_info.get(constants.default_port_str)
            handle_tracker_end(cur_tracker, method_info, args, kwargs, res, err)
            set_cur_tracker(parent_tracker)

        return res

    # special handling for flask route decorator
    wrapper.__name__ = original.__name__
    return wrapper


module_info = {
    "aioredis.client": [
        {
            constants.class_str: "Redis",
            constants.method_str: "execute_command",
            constants.component_str: constants.redis_comp,
            constants.default_host_str: constants.localhost_str,
            constants.default_port_str: 6379,
            constants.wrapper_str: wrap_execute_command,
        }
    ],
}
