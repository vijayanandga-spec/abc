import json
import os
from apminsight.collector.rescodes import get_retry_counter, is_valid_rescode, is_retry_limit_exceeded
from apminsight.util import current_milli_time, is_non_empty_string, is_empty_string, check_and_create_base_dir
from apminsight.constants import instanceid, info_file_name, manage_agent, conf_file_name
from apminsight.logger import agentlogger


class Instanceinfo:

    def __init__(self, info={}):
        self.instanceid = info.get(instanceid, "")
        self.status = info.get("status", None)
        self.modified_time = info.get("time", current_milli_time())
        self.last_reported = None
        self.retry_counter = get_retry_counter(self.status, self.modified_time)
        self.apm_info_file_path = Instanceinfo.get_info_file_path(info)

    def get_instance_id(self):
        return self.instanceid

    def get_status(self):
        return self.status

    def set_status(self, status_code):
        if isinstance(status_code, int):
            self.status = status_code

    def set_instanceid(self, instanceid):
        self.instanceid = instanceid

    def update_instance_info(self, instanceid, rescode):
        self.update_last_reported()
        if is_non_empty_string(instanceid) and (self.instanceid is not instanceid) or (self.status is not rescode):
            self.status = rescode if rescode is not None else manage_agent
            self.instanceid = instanceid
            self.retry_counter = 1
            self.write_info_to_file()

    def update_status(self, rescode):
        self.update_last_reported()
        if is_valid_rescode(rescode) is not True:
            return

        self.retry_counter = self.retry_counter + 1 if self.status == rescode else 1
        if is_non_empty_string(self.instanceid) and self.retry_counter == 1:
            self.status = rescode
            self.modified_time = current_milli_time()
            self.write_info_to_file()
            return

        if is_retry_limit_exceeded(rescode, self.retry_counter):
            agentlogger.critical(
                " Retry limit exceeded for response code :" + str(rescode) + " so Agent goes to shutdown state"
            )
            self.status = 0
            info = {"status": 0, "time": current_milli_time()}
            self.write_info_to_file(info=info)

    def get_as_json(self):
        return {"instanceId": self.instanceid, "status": self.status, "time": self.modified_time}

    @staticmethod
    def get_info_file_path(info={}):
        agent_base_dir = info.get("agentbasedir", None)
        if is_empty_string(agent_base_dir):
            return

        return os.path.join(agent_base_dir, info_file_name)

    @staticmethod
    def get_conf_file_path(info={}):
        try:
            agent_base_dir = info.get("agentbasedir", check_and_create_base_dir)
            conf_file_path = os.path.join(agent_base_dir, "conf")
            if not os.path.exists(conf_file_path):
                os.makedirs(conf_file_path)
            return os.path.join(conf_file_path, conf_file_name)
        except Exception:
            print("Error while creating agent conf dir in " + os.getcwd())
        return ""

    def write_info_to_file(self, info=None):
        if is_empty_string(self.apm_info_file_path):
            return

        try:
            content = self.get_as_json() if info is None else info
            content_str = json.dumps(content)
            with open(self.apm_info_file_path, "w") as apm_info_file:
                apm_info_file.write(content_str)

        except Exception:
            agentlogger.exception("write info to file")

    def write_conf_info(self, info=None):
        if is_empty_string(self.conf_file_path):
            return

        try:
            content = self.get_as_json() if info is None else info
            content_str = json.dumps(content)
            with open(self.conf_file_path, "w") as conf_file_path:
                conf_file_path.write(content_str)

        except Exception:
            agentlogger.exception("write info to file")

    def get_instance_id(self):
        return self.instanceid

    def get_status(self):
        return self.status

    def update_last_reported(self):
        self.last_reported = current_milli_time()

    def get_modiefied_time(self):
        return self.modified_time

    def get_retry_counter(self):
        return self.retry_counter

    def get_last_reported(self):
        return self.last_reported
