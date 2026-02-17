import copy
import random
import string
import json
from apminsight.collector.connhandler import init_connection
from apminsight.metric.txn import Transaction, BackGroundTxn, WebTxn
from apminsight.metric.tracker import Tracker
from apminsight.metric.dbtracker import DbTracker
from apminsight.metric.metricstore import Metricstore
from apminsight.config.configuration import Configuration
from apminsight.collector.ins_info import Instanceinfo
from apminsight.config.threshold import Threshold
from apminsight.config.cpu_usage import CPUUtilization
from apminsight import context
from apminsight import constants
from apminsight.logger import agentlogger
from apminsight import agentfactory
from apminsight.context import get_cur_txn
from apminsight.collector.metric_dispatcher import MetricDispatcher
from apminsight.collector.rescodes import get_rescode_message
from .common.scheduler import Scheduler

class Agent:

    @staticmethod
    def initialize(options={}):
        agentfactory.agent_instance = Agent(options)
        agent_instance = agentfactory.agent_instance
        if not agent_instance.get_config().is_configured_properly():
            raise RuntimeError("Please configure a valid license key")
        if not agent_instance.get_config().is_using_exporter():
            init_connection()
        return agent_instance

    def __init__(self, info):
        self.__config = Configuration(info)
        self.ins_info = Instanceinfo(info)
        self.threshold = Threshold() if not self.__config.is_using_exporter() else None
        self.metricstore = Metricstore() if not self.__config.is_using_exporter() else None
        self.__metric_queue = [] if not self.__config.is_using_exporter() else None
        self.__metric_dispatcher = MetricDispatcher(self.__config) if self.__config.is_using_exporter() else None
        self.__instance_info = None
        self._cpu_usage = CPUUtilization(self.__config.get_process_cpu_threshold())
        self._scheduler = Scheduler()
        self._scheduler.add_task(60, self.get_proc_cpu_percent, True)
        self._scheduler.start()

    def __update_app_port(self, app_port):
        self.__config.set_app_port(app_port)

    def push_to_queue(self, txn):
        self.__metric_queue.append(txn)

    def __get_metric_queue_for_processing(self):
        txn_list = copy.copy(self.__metric_queue)
        self.__metric_queue = []
        return txn_list

    def is_data_collection_allowed(self, txn_config):
        if txn_config is None:
            return False
        cur_status = txn_config.get("instance.status")
        if cur_status in [constants.manage_agent, constants.agent_config_updated]:
            return True
        else:
            agentlogger.info(
                "data collection stopped due to response code %s %s",
                str(cur_status),
                get_rescode_message(cur_status),
            )

        return False

    def is_cpu_threshold_breached(self):
        if self._cpu_usage is None:
            self._cpu_usage = CPUUtilization(self.get_config().get_process_cpu_threshold())

        return self._cpu_usage.get_cpu_threshold_status()

    def update_threshold_config(self, txn_name=None):
        response = {}
        try:
            payload_to_exporter = self.__config.get_conn_payload(txn_name)
            response = self.__metric_dispatcher.send_connect_data(payload_to_exporter)
            if response:
                response = json.loads(response.decode("utf-8"))
                instance_info = {key: val for key, val in response.items() if "transaction" not in key}
                if instance_info != self.__instance_info:
                    self.get_ins_info().set_status(response.get("instance.status"))
                    self.get_ins_info().set_instanceid(response.get("instance.id"))
                    license_key = response.get("license.key", "")
                    if license_key:
                        self.get_config().set_license_key(license_key)
                    self.get_config().update_config_file(self.__get_info_for_conf_file(instance_info))
                    self.__instance_info = instance_info
                agentlogger.info("Recieved the instance and threshold info from DataExporter successfully")
            else:
                agentlogger.info("No response from DataExporter")
        except:
            agentlogger.exception("while getting instance and threshold info from DataExporter")
        return response

    def __get_info_for_conf_file(self, response):
        if response:
            response.pop("license.key", None)
            info_for_conf_file = {
                constants.SETUP_CONFIG: self.get_config().get_user_setup_config(),
                constants.THRESHOLD_CONFIG: response,
            }
            return info_for_conf_file
        return response

    def check_and_create_webtxn(self, wsgi_environ, root_tracker_info):
        try:
            if not isinstance(wsgi_environ, dict):
                return

            txn_config = None
            if not self.get_config().app_port_set():
                if not wsgi_environ.get(constants.server_port_str).isnumeric():
                    agentlogger.info("Auto detection of port failed due to absense of SERVER PORT details in environ")
                    return
                self.__update_app_port(wsgi_environ[constants.server_port_str])

            if self.get_config().is_using_exporter():
                txn_name = wsgi_environ.get(constants.path_info_str, "")
                txn_config = self.update_threshold_config(txn_name)
                if not txn_config:
                    return
                if not self.__metric_dispatcher.has_started():
                    self.__metric_dispatcher.start_dispatching()
                if self.is_cpu_threshold_breached():
                    agentlogger.info(f"Process CPU threshold check failed: Transaction Dropped {txn_name}")
                    return

            if not self.is_data_collection_allowed(txn_config):
                return

            if type(root_tracker_info) is not dict:
                return

            context.clear_cur_context()
            root_tracker_info[constants.CONTEXT][constants.TRACE_ID_STR] = "".join(
                random.choices(string.ascii_letters + string.digits, k=32)
            )
            txn = WebTxn(wsgi_environ, root_tracker_info, txn_config)
            context.set_cur_context(txn, txn.get_trace_id(), txn.get_root_tracker().get_span_id())
            # handle cross app response
            return txn
        except Exception:
            agentlogger.exception("while creating WebTxn obj")

    def check_and_create_bgtxn(self, txn_name, root_tracker_info):
        try:
            txn_config = None
            if not self.get_config().app_port_set():
                agentlogger.info("Application port is not detected yet. using 8080 as a default port for now")

            if self.get_config().is_using_exporter():
                txn_config = self.update_threshold_config(txn_name)
                if not txn_config:
                    return
                if not self.__metric_dispatcher.has_started():
                    self.__metric_dispatcher.start_dispatching()
                if self.is_cpu_threshold_breached():
                    agentlogger.info(f"Process CPU threshold check failed : Transaction Dropped {txn_name}")
                    return

            if not self.is_data_collection_allowed(txn_config):
                return

            context.clear_cur_context()
            root_tracker_info[constants.CONTEXT][constants.TRACE_ID_STR] = "".join(
                random.choices(string.ascii_letters + string.digits, k=32)
            )
            txn = BackGroundTxn(txn_name, root_tracker_info, txn_config)
            context.set_cur_context(txn, txn.get_trace_id(), txn.get_root_tracker().get_span_id())
            # handle cross app response
            return txn
        except Exception:
            agentlogger.exception("while creating WebTxn obj")

    def check_and_create_tracker(self, tracker_info):
        track = None
        cur_txn = get_cur_txn()
        try:
            if type(tracker_info) is not dict:
                return None

            if context.is_txn_active() is not True:
                return None

            if constants.PARENT_TRACKER not in tracker_info:
                tracker_info[constants.PARENT_TRACKER] = context.get_cur_tracker()

            if constants.is_db_tracker_str in tracker_info:
                track = DbTracker(tracker_info)
            else:
                track = Tracker(tracker_info)
            cur_txn.add_tracker(track)
            cur_txn.increment_method_count(1)

            context.set_cur_tracker(track)
        except:
            agentlogger.exception("While creating Tracker")

        return track

    def end_txn(self, txn, res=None, err=None):
        try:
            if txn is None:
                return

            if isinstance(txn, Transaction):
                # Handling cases where end_transaction api called in between the txn
                if not txn.is_completed():
                    while context.get_cur_tracker_span_id():
                        tracker = context.get_cur_tracker()
                        parent = tracker.get_parent()
                        tracker.end_tracker()
                        context.set_cur_tracker(parent)
                txn.end_txn(res, err)
        except Exception:
            agentlogger.exception("tracking end txn")

    def end_tracker(self, tracker, err=None):
        if isinstance(tracker, Tracker) is not True:
            return

        cur_txn = context.get_cur_txn()
        if isinstance(cur_txn, Transaction):
            tracker.end_tracker(err)
            cur_txn.handle_end_tracker(tracker)

    def get_config(self):
        return self.__config

    def get_threshold(self):
        return self.threshold

    def get_ins_info(self):
        return self.ins_info

    def get_metric_store(self):
        for txn in self.__get_metric_queue_for_processing():
            self.metricstore.add_txn(txn)
        return self.metricstore

    def get_metric_dispatcher(self, external=None):
        if external:
            self.__metric_dispatcher.start_dispatching()
        return self.__metric_dispatcher

    def get_proc_cpu_percent(self):
        self._cpu_usage.get_proc_cpu_percent()

