import os
import apminsight
import platform
import json
import apminsight.constants as constants
from apminsight.logger import agentlogger
from .config_util import ConfigReader
from .auto_profiler import AutoProfilerConfig
from .host_env_identifier import HostIdentifier
from apminsight.util import is_empty_string, is_non_empty_string, get_local_interfaces, convert_tobase64
from .encryption import decrypt, encrypt, encoded_bytes_array


class Configuration:
    __license_key = None
    __app_name = None
    __app_port = None
    __app_port_set = None
    __collector_host = None
    __collector_host = None
    __proxy_server_host = None
    __proxy_server_port = None
    __proxy_username = None
    __proxy_password = None
    __agent_version = None
    __installed_path = None
    __exporter = None
    __exporter_status_port = None
    __exporter_data_port = None
    __exporter_host = None
    __conn_payload = None
    __ipv4 = []
    __process_cpu_threshold = None

    def __init__(self, info):
        self.__app_name = ConfigReader.get_app_name(info)
        self.__app_port = None
        self.__app_port_set = False
        self.__agent_version = apminsight.version
        self.__application_path = apminsight.application_path
        self.__installed_path = apminsight.installed_path
        self.__info_file_path = self.get_config_filepath()
        self.__license_key = self.read_license_key(info)
        self.__collector_host = ConfigReader.get_collector_host(self.__license_key, info)
        self.__collector_port = ConfigReader.get_collector_port(info)
        self.__proxy_server_host = ConfigReader.get_proxy_server_host(info)
        self.__proxy_server_port = ConfigReader.get_proxy_server_port(info)
        self.__proxy_username = ConfigReader.get_proxy_auth_username(info)
        self.__proxy_password = ConfigReader.get_proxy_auth_password(info)
        payload_config = os.getenv(constants.apm_print_payload, "")
        self.print_payload = False if is_empty_string(payload_config) else True
        self.host_info = HostIdentifier()
        self.__exporter = ConfigReader.using_exporter(info)
        self.__exporter_status_port = ConfigReader.get_exporter_status_port(info)
        self.__exporter_data_port = ConfigReader.get_exporter_data_port(info)
        self.__exporter_host = ConfigReader.get_exporter_host(info)
        self.__ipv4 = get_ipv4_address()
        self.__conn_payload = self.create_connection_payload()
        self.__process_cpu_threshold = ConfigReader.get_process_cpu_threshold()
        self.__update_agent_info()
        self.__encoded_text = None

    def read_license_key(self, info):

        license_key = None
        # reading encrypt data form profiler conf file or info file
        self.__encoded_text = AutoProfilerConfig.encrypted_value()

        if is_non_empty_string(self.__encoded_text):
            license_key = decrypt(*encoded_bytes_array(*self.__encoded_text.split("-")))
            if license_key and is_non_empty_string(license_key):
                return license_key

        # checking license key from environment
        env_lk = os.getenv(constants.license_key_env, None)
        if is_non_empty_string(env_lk):
            license_key = env_lk if env_lk != license_key else license_key
        else:
            # checking license key from info data
            info_lk = info.get("license_key", None)
            if is_non_empty_string(info_lk):
                license_key = info_lk if info_lk != license_key else license_key

        if license_key is not None:
            self.__encoded_text = encrypt(os.urandom(32), license_key, os.urandom(16))
            self.__update_agent_info()
        else:
            self.__encoded_text = ConfigReader.get_license_from_infofile(self.get_config_filepath())
            if is_non_empty_string(self.__encoded_text):
                license_key = decrypt(*encoded_bytes_array(*self.__encoded_text.split("-")))
                return license_key

        return license_key

    def __update_agent_info(self):
        if AutoProfilerConfig.is_auto_profiler_enabled():
            return
        
        if is_non_empty_string(self.__encoded_text):
            info_json = {"license_key": self.__encoded_text}
            ConfigReader.update_info_file(self.get_config_filepath(), info_json)

    def is_configured_properly(self):
        if is_empty_string(self.__license_key):
            return False

        return True

    def update_collector_info(self, collector_info):
        if collector_info is None:
            return

        try:
            self.__collector_host = collector_info.get(constants.host_str, self.__collector_host)
            self.__collector_port = collector_info.get(constants.port_str, self.__collector_port)
        except Exception:
            agentlogger.exception("while updating collector info")

    def get_license_key(self):
        return self.__license_key

    def get_app_name(self):
        if self.__app_name == constants.default_app_monitor_name:
            app_name = self.__application_path.split(os.path.sep)
            if len(app_name) > 1:
                return "-".join(app_name[-2:])
            return app_name
        return self.__app_name

    def set_app_name(self, appname):
        self.__app_name = appname

    def get_app_port(self, for_exporter=True):
        if self.__app_port is not None:
            if not for_exporter or not self.__exporter:
                return self.__app_port
            return int(self.__app_port)

    def set_app_port(self, app_port):
        self.__app_port = app_port
        self.__conn_payload["connect_info"]["agent_info"]["port"] = int(app_port)
        self.__app_port_set = True

    def app_port_set(self):
        return self.__app_port_set

    def get_collector_host(self):
        return self.__collector_host

    def get_collector_port(self):
        return self.__collector_port

    def get_agent_version(self):
        return self.__agent_version

    def get_installed_dir(self):
        return self.__installed_path

    def is_payload_print_enabled(self):
        return self.print_payload

    def get_fqdn(self):
        return self.host_info.get_fqdn()

    def get_host_name(self, for_exporter=True):
        if self.host_info.get_host_type() == constants.DOCKER:
            return self.host_info.get_host_name()

        if not for_exporter or not self.__exporter and len(self.host_info.get_host_type()) > 0:
            return self.host_info.get_host_name()

        return platform.node()

    def get_host_type(self, for_exporter=True):
        if self.host_info.get_host_type() == constants.DOCKER:
            return constants.DOCKER
        if not for_exporter or not self.__exporter and len(self.host_info.get_host_type()) > 0:
            return self.host_info.get_host_type()
        return platform.system()

    def get_proxy_details(self):
        if not self.__proxy_server_host or not self.__proxy_server_port:
            return False
        if self.__proxy_username and self.__proxy_password:
            proxy_details = {
                "http": "http://"
                + self.__proxy_username
                + ":"
                + self.__proxy_password
                + "@"
                + self.__proxy_server_host
                + ":"
                + self.__proxy_server_port,
                "https": "http://"
                + self.__proxy_username
                + ":"
                + self.__proxy_password
                + "@"
                + self.__proxy_server_host
                + ":"
                + self.__proxy_server_port,
            }
        else:
            proxy_details = {
                "http": "http://" + self.__proxy_server_host + ":" + self.__proxy_server_port,
                "https": "http://" + self.__proxy_server_host + ":" + self.__proxy_server_port,
            }
        return proxy_details

    def is_using_exporter(self):
        return self.__exporter

    def get_exporter_status_port(self):
        return self.__exporter_status_port

    def get_exporter_data_port(self):
        return self.__exporter_data_port

    def get_exporter_host(self):
        return self.__exporter_host

    def set_license_key(self, license_str):
        if is_non_empty_string(license_str):
            self.__license_key = license_str

    def get_ipv4(self):
        return self.__ipv4

    def get_process_cpu_threshold(self):
        return self.__process_cpu_threshold

    def get_user_setup_config(self):
        return (
            {
                constants.APP_NAME: self.get_app_name(),
                constants.HOST_NAME: self.get_host_name(),
                constants.APP_PORT: self.get_app_port(),
                constants.EXP_HOST: self.get_exporter_host(),
                constants.EXP_STATUS_PORT: self.get_exporter_status_port(),
                constants.EXP_DATA_PORT: self.get_exporter_data_port(),
                constants.PROXY_DETAILS: self.get_proxy_details(),
                constants.AGENT_VERSION: self.get_agent_version(),
            },
        )

    def get_license_key_for_dt(self):
        if self.is_configured_properly():
            license_key = self.__license_key
            license_key_for_dt = license_key[-12:]
            return license_key_for_dt
        return None

    def create_connection_payload(self):
        conn_payload = {
            "agent_info": {
                "application.type": constants.python_str,
                "agent.version": self.get_agent_version()[
                    : self.get_agent_version().index(".", self.get_agent_version().index(".") + 1)
                ],
                "agent.version.info": self.get_agent_version(),
                "application.name": self.get_app_name(),
                "port": self.get_app_port() or 8080,
                "host.type": self.get_host_type(),
                "hostname": self.get_host_name(),
                "fqdn": self.get_fqdn(),
                "process.uid" : AutoProfilerConfig.PROCESS_UID,
                "process.monitoring.rule.name" : AutoProfilerConfig.RULE_NAME,
            },
            "agent_specific_info": {
                "application.group.name": os.environ.get(constants.APM_GROUPS, "")
                # "tags":os.environ.get(constants.APM_TAGS,"")
            },
            "environment": {
                "IP": self.get_ipv4(),
                # "UserName": process.env.USER,
                "OSVersion": platform.release(),
                "MachineName": platform.node(),
                "AgentInstallPath": self.get_installed_dir(),
                "Python version": platform.python_version(),
                "OSArch": platform.machine(),
                "OS": platform.system(),
                "Python implementation": platform.python_implementation(),
            },
        }
        server_key = AutoProfilerConfig.get_server_monitor_key()
        if is_non_empty_string(server_key):
            conn_payload["agent_info"]["server.monitor.key"] = server_key

        if self.is_using_exporter():
            conn_payload = {"connect_info": conn_payload, "misc_info": {"license.key": self.__license_key}}

        return conn_payload

    def get_conn_payload(self, txn_name="Anonymous"):
        conn_payload = self.__conn_payload
        conn_payload["misc_info"]["txn.name"] = txn_name
        if self.is_using_exporter():
            conn_payload = json.dumps(conn_payload)
            conn_payload += "\n"
        return conn_payload

    def get_config_filepath(self):
        if AutoProfilerConfig.is_auto_profiler_enabled():
            return os.path.join(AutoProfilerConfig.PYTHON_LOG_PATH, self.get_app_name() + "_" + str(self.get_app_port()))
        else:
            logs_path = os.getenv(constants.apm_logs_dir, None)
            if logs_path and is_non_empty_string(logs_path):
                logs_path = os.path.join(logs_path, constants.base_dir)
            else:
                logs_path = os.path.join(self.__application_path, constants.base_dir)
            return logs_path

    def update_config_file(self, instance_info):
        config_file = self.get_config_filepath()
        ConfigReader.update_config_file(config_file, instance_info)

    def update_app_name(self, name):
        if self.__app_name == constants.DEFAULT_APM_APP_NAME:
            self.__app_name = name
            self.__conn_payload = self.create_connection_payload()


def get_ipv4_address():
    if os.name == "nt":  # check for windows os
        return []
    ip_dict = get_local_interfaces()
    if len(ip_dict):
        return list(ip_dict.values())
    return []
