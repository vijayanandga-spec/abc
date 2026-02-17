import os
import base64
import configparser

from apminsight.constants import AutoProfilerConstants

class AutoProfilerConfig:
    CONF_FILEPATH = os.getenv(AutoProfilerConstants.CONF_FILEPATH, None)
    HOMEPATH = os.getenv(AutoProfilerConstants.HOMEPATH, os.getcwd())
    PYTHON_LOG_PATH = os.path.join(HOMEPATH, "PYTHON") if HOMEPATH else None
    PROCESS_UID = os.getenv(AutoProfilerConstants.PROCESS_UID, None)
    RULE_NAME = os.getenv(AutoProfilerConstants.RULE_NAME, None)
    
    @classmethod
    def is_auto_profiler_enabled(cls):
        if cls.CONF_FILEPATH and os.path.exists(cls.CONF_FILEPATH):
            return True
        return False

    @classmethod
    def encrypted_value(cls):
        if not cls.is_auto_profiler_enabled():
            return None
        try:
            config = configparser.ConfigParser()
            config.read(cls.CONF_FILEPATH)
            
            if AutoProfilerConstants.SECTION in config:
                section = config[AutoProfilerConstants.SECTION]
                text = section.get(AutoProfilerConstants.KEY)
                agent_id = base64.b64encode(section.get(AutoProfilerConstants.AGENT_ID).encode('utf-8')).decode("utf-8")
                start_time = base64.b64encode(section.get(AutoProfilerConstants.START_TIME).encode('utf-8')).decode("utf-8")
                cls.SERVER_MONITOR_KEY = section.get(AutoProfilerConstants.SERVER_MONITOR_KEY, None)
                return "-".join((start_time, text, agent_id))
        except Exception as e:
            print(f"Failed to read autoprofiler config: {e}")
        return None

    @classmethod
    def get_server_monitor_key(cls):
        if not cls.is_auto_profiler_enabled():
            return None

        if hasattr(cls, 'SERVER_MONITOR_KEY'):
            return cls.SERVER_MONITOR_KEY

        try:
            config = configparser.ConfigParser()
            config.read(cls.CONF_FILEPATH)

            if AutoProfilerConstants.SECTION in config:
                section = config[AutoProfilerConstants.SECTION]
                return section.get(AutoProfilerConstants.SERVER_MONITOR_KEY, None)
        except Exception as e:
            print(f"Failed reading Server key from autoprofiler config: {e}")
        return None
