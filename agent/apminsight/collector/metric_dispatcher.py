import json
import socket
import threading
from queue import Queue
from apminsight import get_agent
from apminsight.logger import agentlogger
from apminsight.util import current_milli_time, is_non_empty_string, convert_tobase64, json_normalize


class MetricDispatcher:
    def __init__(self, config):
        self.__dispatcher_queue = Queue()
        self.__started = False
        self.__agent_last_communicated = None
        self.__event = threading.Event()

    def __push_to_dispatcher_queue(self, txn):
        self.__dispatcher_queue.put(txn)
        agentlogger.info("Successfully pushed data to Dispatcher queue")

    def has_started(self):
        return self.__started

    def __set_event(self):
        self.__event.set()

    def clear_event(self):
        self.__event.clear()

    def get_agent_last_communicated(self):
        return self.__agent_last_communicated

    def start_dispatching(self):
        try:
            if self.__started is True:
                return
            metric_dispatcher_thread = threading.Thread(
                target=self.__background_task, args=(60,), kwargs={}, daemon=True
            )
            metric_dispatcher_thread.start()
            self.__started = True
        except Exception:
            agentlogger.exception("Error while starting background task")

    def __background_task(self, timeout):
        while True:
            try:
                if not self.__dispatcher_queue.empty():
                    txn_payload = self.__dispatcher_queue.get(block=False)
                    self.__send_metric_data(txn_payload)
                else:
                    self.__event.clear()
                    event_set = self.__event.wait(timeout)
                    if event_set:
                        continue
                    else:
                        pass
                        # get_agent().update_threshold_config()
            except:
                agentlogger.exception("in background task")

    def _push_data_to_exporter(self, host, port, payload, receive_data=False):
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        data = None
        try:
            client_socket.connect((host, port))
            client_socket.sendall(bytes(payload, encoding="utf-8"))
            if receive_data:
                data = client_socket.recv(1024)
        except ConnectionRefusedError:
            agentlogger.info("Socket Connection failed, please check if the exporter is running")
        except Exception as exc:
            agentlogger.exception(f"Socket Connection error {exc}")
        finally:
            self.__agent_last_communicated = current_milli_time()
            if client_socket:
                client_socket.close()
        return data

    def __send_metric_data(self, metric_payload):
        try:
            config = get_agent().get_config()
            host = config.get_exporter_host()  # The server's hostname or IP address
            port = int(config.get_exporter_data_port())  # The port used by the server
            self._push_data_to_exporter(host, port, metric_payload)
        except Exception as exc:
            agentlogger.exception(f"while sending metric data : {exc}")
        finally:
            self.__event.clear()

    def send_connect_data(self, payload):
        try:
            config = get_agent().get_config()
            host = config.get_exporter_host()  # The server's hostname or IP address
            port = int(config.get_exporter_status_port())  # The port used by the server
            return self._push_data_to_exporter(host, port, payload, receive_data=True)
        except Exception as exc:
            agentlogger.exception(f"Error sending Connect_data :{exc}")

    async def construct_payload(self, metric_constructor, external=None):
        try:
            payload = self.__create_json_to_send(metric_constructor())
            if external:
                agentlogger.info("Successfully constructed payload recieved from S247" + external + "agent")
            else:
                agentlogger.info("Successfully constructed tansaction payload")
            self.__push_to_dispatcher_queue(payload)
            self.__set_event()
        except:
            agentlogger.exception("while constructing data payload to exporter")

    def __create_json_to_send(self, payload):
        
        json_payload = None
        try:
            json_payload = json.dumps(payload)
        except Exception:
            agentlogger.exception("while creating json payload")
            agentlogger.info(payload)
            json_payload = json.dumps(json_normalize(payload))
        
        json_to_exporter = convert_tobase64(json_payload)
        if is_non_empty_string(json_to_exporter):
            json_to_exporter += "\n"
        return json_to_exporter
