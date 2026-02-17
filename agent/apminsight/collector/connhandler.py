"""
    initate connect request and schedule 1min task
"""

import platform
import time
import json
from apminsight import constants
from apminsight.agentfactory import get_agent
from apminsight.constants import arh_connect
from apminsight.logger import agentlogger
from apminsight.collector.reqhandler import send_req
from apminsight.collector.reshandler import handle_connect_response
from apminsight.collector.datahandler import process_collected_data


task_spawned = False
conn_payload = None


def init_connection():
    global task_spawned
    try:
        if task_spawned is True:
            return

        import threading

        t = threading.Thread(target=background_task, args=(), kwargs={})
        t.setDaemon(True)
        t.start()
        task_spawned = True

    except Exception:
        agentlogger.exception("Error while spawing thread")


def background_task():
    conn_success = False
    while True:
        try:
            if conn_success is False:
                conn_success = send_connect()
            else:
                process_collected_data()
        except Exception:
            agentlogger.exception("apm task error")
        finally:
            # get_agent().get_metric_store().cleanup()
            time.sleep(60)


def send_connect():
    global conn_payload
    conn_payload = getconn_payload() if conn_payload is None else conn_payload
    res_data = send_req(arh_connect, conn_payload)
    return handle_connect_response(res_data)


def getconn_payload(wsgi_environ=None):
    config = get_agent().get_config()
    conn_payload = {
        "connect_info": {
            "agent_info": {
                "application.type": constants.python_str,
                "agent.version": config.get_agent_version(),
                "application.name": config.get_app_name(),
                "port": config.get_app_port(),
                "host.type": config.get_host_type(),
                "hostname": config.get_host_name(),
                "fqdn": config.get_fqdn(),
            },
            "environment": {
                # "UserName": process.env.USER,
                "OSVersion": platform.release(),
                "MachineName": platform.node(),
                "AgentInstallPath": config.get_installed_dir(),
                "Python version": platform.python_version(),
                "OSArch": platform.machine(),
                "OS": platform.system(),
                "Python implementation": platform.python_implementation(),
            },
        },
        "misc_info": {},
    }
    if wsgi_environ is not None:
        txn_name = wsgi_environ.get(constants.path_info_str, "")
        conn_payload["misc_info"]["txn.name"] = txn_name
    if config.is_using_exporter():
        conn_payload = json.dumps(conn_payload)
        conn_payload += "\n"
    return conn_payload
