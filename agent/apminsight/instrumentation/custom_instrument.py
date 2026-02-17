"""
Read the custom instrumentation file and instrument the code

Format of custom instrumentation ini file:
[module_name]
class_name.method_name = component_name

Example:
[cheroot.server]
HTTPRequest.send_headers = cheroot
[cheroot.wsgi]
Gateway.respond = cheroot

Use enivornment variable to set the custom instrument ini file path:
export APM_CUSTOM_INSTRUMENT_FILE_PATH=/path/to/custom_instrument.ini

"""

import os
import sys
import configparser

from apminsight import constants
from apminsight.logger import agentlogger as logger
from .patch import resolve_path, apply_patch
from .wrapper import custom_wrapper

class CustomInstrumentation:

    def __init__(self):
        self.file_path = os.getenv(constants.APM_CUSTOM_INSTRUMENT_FILE_PATH, None)
        self.instrumented_methods = {}
        self.config = None
        self.status = False


    def load_config(self) -> bool:
        """Load the custom instrumentation configuration from the ini file."""
        if not self.file_path:
            logger.info("No custom instrumentation file path set.")
            return False
        
        if not os.path.exists(self.file_path):
            logger.warning(f"Custom instrumentation file not found: {self.file_path}")
            return False
        
        try:
            self.config = configparser.ConfigParser()
            self.config.read(self.file_path)
            logger.info(f"Loaded custom instrumentation config from: {self.file_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to parse custom instrumentation file: {str(e)}")
            return False
        
    def get_modules_info(self):
        if not self.load_config():
            return None
        if self.config is not None:
            modules_info = {}
            for module_name in self.config.sections():
                info_list = []
                for method_path, component_name in self.config.items(module_name):
                    info = {}
                    info["method"] = method_path,
                    info["component"] = component_name
                    info["wrapper"] = custom_wrapper
                    method_path_list = method_path.split('.')
                    if len(method_path_list) > 1:
                        info["method"] = method_path_list[1]
                        info["class"] = method_path_list[0]
                    else:
                        info["method"] = method_path_list[0]
                    info_list.append(info)
                modules_info[module_name] = info_list

            return modules_info

    def instrument(self):
        """Instrument the methods based on the configuration."""
        if not self.load_config():
            return

        sys.path.append(os.getcwd())
        logger.info("Added Current working dir to sys path for custom instrumentation")    

        for module_name in self.config.sections():
            for method_path, component_name in self.config.items(module_name):
                try:
                    info = {
                        "method": method_path,
                        "component": component_name
                    }
                    (parent, attribute, original) = resolve_path(module_name, method_path)
                    wrapper = custom_wrapper(original, module_name, info)
                    apply_patch(parent, attribute, wrapper)
                    self.instrumented_methods[module_name+"."+method_path] = component_name
                except ImportError:
                    logger.warning("Unable to find the %s for instrumentation",module_name)
                except Exception as e:
                    logger.error("Error instrumenting %s:%s  Exception:%s", module_name, method_path, str(e))
        
        sys.path.pop()

    def uninstrument(self):
        pass
