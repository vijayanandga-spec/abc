import os
import sys
import time
import logging
from logging.handlers import RotatingFileHandler
from apminsight.constants import (
    agent_logger_name,
    logs_dir,
    base_dir,
    log_name,
    log_format,
    apm_logs_dir,
    PROCESS_ID,
    LOG_FILE_BACKUP_COUNT,
    LOG_FILE_SIZE,
    APM_LOG_FILE_BACKUP_COUNT,
    APM_LOG_FILE_SIZE,
    LOG_FILE_MODE,
    LOG_FILE_DELAY,
    LOG_FILE_ENCODEING,
    DEFAULT_LOG_FILE_BACKUP_COUNT,
    DEFAULT_LOG_FILE_SIZE,
)
from .config.auto_profiler import AutoProfilerConfig


def current_milli_time():
    return int(round(time.time() * 1000))


def is_non_empty_string(string):
    if not isinstance(string, str) or string.strip() == "":
        return False
    return True


class ApmLogger:

    __instance = None
    __custom_dir = os.getenv(apm_logs_dir, None)
    __file_size = os.getenv(APM_LOG_FILE_SIZE, DEFAULT_LOG_FILE_SIZE)
    __backup_count = os.getenv(APM_LOG_FILE_BACKUP_COUNT, DEFAULT_LOG_FILE_BACKUP_COUNT)

    def __new__(cls, log_config):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
            cls.file_name = log_name
            cls._logs_path = cls.check_and_create_dirs()

            cls.__log_file_config = [
                os.path.join(cls._logs_path, cls.file_name),
                LOG_FILE_MODE,
                log_config.get(LOG_FILE_SIZE, cls.__file_size),
                log_config.get(LOG_FILE_BACKUP_COUNT, cls.__backup_count),
                LOG_FILE_ENCODEING,
                LOG_FILE_DELAY,
            ]
            cls.__logger = cls.create_logger()

        return cls.__instance

    @classmethod
    def update_handler(cls, app_name=""):
        if AutoProfilerConfig.is_auto_profiler_enabled():
            logger = logging.getLogger(agent_logger_name)
            try:
                logs_path = os.path.join(cls._logs_path, app_name)
                if not os.path.exists(logs_path):
                    os.makedirs(logs_path)
                cls.__log_file_config[0] = os.path.join(logs_path, cls.file_name)
                for handler in logger.handlers[:]:
                    if isinstance(handler, RotatingFileHandler):
                        logger.removeHandler(handler)
                        handler.close()  # Don't forget to close the handler
                formatter = logging.Formatter(log_format)
                cls.handler = RotatingFileHandler(*cls.__log_file_config)
                cls.handler.setFormatter(formatter)
                logger.addHandler(cls.handler)
                cls.__logger = logger
            except Exception as e:
                print("apminsight agent log file initialization error", e)

        return logger

    @classmethod
    def check_and_create_dirs(cls):
        cus_logs_dir = os.getenv(apm_logs_dir, None)
        if AutoProfilerConfig.is_auto_profiler_enabled():
            cus_logs_dir = AutoProfilerConfig.PYTHON_LOG_PATH
        elif not is_non_empty_string(cus_logs_dir):
            cus_logs_dir = os.path.join(os.getcwd(), base_dir)
        else:
            cus_logs_dir = os.path.join(cus_logs_dir, base_dir)

        logs_path = os.path.join(cus_logs_dir, logs_dir)
        if not os.path.exists(logs_path):
            os.makedirs(logs_path)

        return logs_path

    @classmethod
    def create_logger(cls):
        try:
            logger = logging.getLogger(agent_logger_name)
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter(log_format)
            cls.handler = RotatingFileHandler(*cls.__log_file_config)
            cls.handler.setFormatter(formatter)
            logger.addHandler(cls.handler)
            extra_field = {PROCESS_ID: os.getpid()}
            logger = logging.LoggerAdapter(logger, extra_field)
            return logger
        except Exception as e:
            print("apminsight agent log file initialization error", e)
            return cls.log_to_sysout()

    @classmethod
    def log_to_sysout(cls):
        global agentlogger
        try:
            logger = logging.getLogger("agent_logger_name")
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter(log_format)
            cls.handler = logging.StreamHandler(sys.stdout)
            cls.handler.setFormatter(formatter)
            logger.addHandler(cls.handler)
            extra_field = {PROCESS_ID: os.getpid()}
            logger = logging.LoggerAdapter(logger, extra_field)
            return logger
        except Exception as e:
            print("not able to print apminsight agent logs to sysout", e)

    @classmethod
    def get_logger(cls, log_config={}):
        if cls.__instance is None:
            cls(log_config)
        return cls.__logger

    def set_log_level(level):
        logger = ApmLogger.get_logger()
        logger.setLevel(level)


agentlogger = ApmLogger.log_to_sysout()


def create_agentlogger(log_config):
    global agentlogger
    agentlogger = ApmLogger.get_logger(log_config)
    return agentlogger


def get_logger():
    global agentlogger
    if agentlogger is None:
        agentlogger = ApmLogger.get_logger()

    return agentlogger


def update_handler_file_name(name):
    global agentlogger
    agentlogger = ApmLogger.update_handler(name)
    return agentlogger
