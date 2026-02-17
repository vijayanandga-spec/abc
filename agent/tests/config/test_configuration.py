import unittest
import os
from apminsight import constants
from apminsight.config.configuration import Configuration
from apminsight.config.configuration import get_app_name, get_collector_host, get_collector_port, get_license_key, get_app_port, get_proxy_auth_password, get_proxy_auth_username, get_proxy_server_host, get_cloud_details, get_proxy_server_port, is_aws, is_azure
import requests
import responses

class TestConfiguration(unittest.TestCase):

    config = Configuration({})

    def test_is_configured_properly(self):
        os.environ[constants.license_key_env] = ''
        config = Configuration({})
        self.assertFalse(config.is_configured_properly())
        os.environ[constants.license_key_env] = 'c-three-o'
        config = Configuration({})
        self.assertTrue(config.is_configured_properly())

    def test_get_collector_host(self):
        info = {}
        os.environ[constants.apm_collector_host] = 'plusinsight.site24x7.unit_test_1'
        self.assertEqual('plusinsight.site24x7.unit_test_1', get_collector_host('', info))
        
        os.environ.pop(constants.apm_collector_host)
        info = {'apm_collector_host' : 'plusinsight.site24x7.unit_test_2'}
        self.assertEqual('plusinsight.site24x7.unit_test_2', get_collector_host('', info))
        self.assertEqual('plusinsight.site24x7.unit_test_2', get_collector_host('us_chan', info))
        
        info = {}
        self.assertEqual('plusinsight.site24x7.com', get_collector_host('us_chan', info))
        self.assertEqual('plusinsight.site24x7.eu', get_collector_host('eu_chan', info))
        self.assertEqual('plusinsight.site24x7.in', get_collector_host('in_chan', info))
        self.assertEqual('plusinsight.site24x7.cn', get_collector_host('cn_chan', info))
        self.assertEqual('plusinsight.site24x7.net.au', get_collector_host('au_chan', info))
        
        self.assertEqual('', get_collector_host('', info))

    def test_get_license_key(self):
        info = {}

        os.environ.pop(constants.license_key_env)
        self.assertEqual('', get_license_key(info))

        os.environ[constants.license_key_env] = 'UNIT_TEST_LICENSE_KEY_1'
        self.assertEqual('UNIT_TEST_LICENSE_KEY_1', get_license_key(info))

        info = {'license_key' : 'UNIT_TEST_LICENSE_KEY_2'}
        self.assertEqual('UNIT_TEST_LICENSE_KEY_1', get_license_key(info))

        os.environ.pop(constants.license_key_env)
        self.assertEqual('UNIT_TEST_LICENSE_KEY_2', get_license_key(info))
        
    def test_get_app_name(self):
        info = {}
        self.assertEqual('Python-Application', get_app_name(info))

        os.environ[constants.apm_app_name] = 'UNIT_TEST_APP_1'
        self.assertEqual('UNIT_TEST_APP_1', get_app_name(info))

        info = {'appname' : 'UNIT_TEST_APP_2'}
        self.assertEqual('UNIT_TEST_APP_1', get_app_name(info))

        os.environ.pop(constants.apm_app_name)
        self.assertEqual('UNIT_TEST_APP_2', get_app_name(info))
        

    def test_get_app_port(self):
        info = {}
        self.assertEqual('8080', get_app_port(info))

        os.environ[constants.apm_app_port] = '1234'
        info = {'app_port' : '4321'}
        self.assertEqual('1234', get_app_port(info))

        os.environ.pop(constants.apm_app_port)
        self.assertEqual('4321', get_app_port(info))

    def test_get_collector_port(self):
        info = {}
        self.assertEqual('443', get_collector_port(info))

        os.environ[constants.apm_collector_port] = '8443'
        info  = {'apm_collector_port' : '567'}
        self.assertEqual('8443', get_collector_port(info))

        os.environ.pop(constants.apm_collector_port)
        self.assertEqual('567', get_collector_port(info))

    def test_get_proxy_server_host(self):
        info = {}
        self.assertEqual(None, get_proxy_server_host(info))

        os.environ['PROXY_SERVER_HOST'] = 'PROXY_HOST_ENVIRON'
        info  = {'proxy_server_host' : 'PROXY_HOST_INFO'}
        self.assertEqual('PROXY_HOST_ENVIRON', get_proxy_server_host(info))

        os.environ.pop('PROXY_SERVER_HOST')
        self.assertEqual('PROXY_HOST_INFO', get_proxy_server_host(info))

    def test_get_proxy_server_port(self):
        info = {}
        self.assertEqual(None, get_proxy_server_port(info))

        os.environ['PROXY_SERVER_PORT'] = 'PROXY_PORT_ENVIRON'
        info  = {'proxy_server_port' : 'PROXY_PORT_INFO'}
        self.assertEqual('PROXY_PORT_ENVIRON', get_proxy_server_port(info))

        os.environ.pop('PROXY_SERVER_PORT')
        self.assertEqual('PROXY_PORT_INFO', get_proxy_server_port(info))    

    def test_get_proxy_auth_username(self):
        info = {}
        self.assertEqual(None, get_proxy_auth_username(info))

        os.environ['PROXY_AUTH_USERNAME'] = 'PROXY_USERNAME_ENVIRON'
        info  = {'proxy_auth_username' : 'PROXY_USERNAME_INFO'}
        self.assertEqual('PROXY_USERNAME_ENVIRON', get_proxy_auth_username(info))

        os.environ.pop('PROXY_AUTH_USERNAME')
        self.assertEqual('PROXY_USERNAME_INFO', get_proxy_auth_username(info))         

    def test_get_proxy_auth_password(self):
        info = {}
        self.assertEqual(None, get_proxy_auth_password(info))

        os.environ['PROXY_AUTH_PASSWORD'] = 'PROXY_PASSWORD_ENVIRON'
        info  = {'proxy_auth_password' : 'PROXY_PASSWORD_INFO'}
        self.assertEqual('PROXY_PASSWORD_ENVIRON', get_proxy_auth_password(info))

        os.environ.pop('PROXY_AUTH_PASSWORD')
        self.assertEqual('PROXY_PASSWORD_INFO', get_proxy_auth_password(info))

    def test_is_azure(self):
        return 

    @responses.activate  
    def test_is_aws(self):
        info = {}
        responses.add(**{
        'method'         : responses.GET,
        'url'            : constants.aws_url,
        'body'           : 'AWS_Instanceid',
        'status'         : 200,
        'content_type'   : 'text',
        })
        config = Configuration(info)
        self.assertEqual( config.get_cloud_instance_id(), "AWS_Instanceid")
        self.assertEqual( config.get_cloud_type(), "AWS")

    @responses.activate  
    def test_is_azure(self):
        info = {}
        responses.add(**{
        'method'         : responses.GET,
        'url'            : constants.azure_url,
        'body'           : '{"ID":"AZURE_Instanceid","UD":0,"FD":0}',
        'status'         : 200,
        'adding_headers' : {'content-type': 'application/json'},

        })
        config = Configuration(info)
        self.assertEqual( config.get_cloud_instance_id(), "AZURE_Instanceid")
        self.assertEqual( config.get_cloud_type(), "AZURE")

    def test_config_get_license_key(self):
        self.assertTrue(type(self.__config.get_license_key()) is str)

    def test_config_get_app_name(self):
        self.assertTrue(type(self.__config.get_app_name()) is str)

    def test_config_get_app_port(self):
        self.assertTrue(type(self.__config.get_app_port()) is str)

    def test_config_get_collector_host(self):
        self.assertTrue(type(self.__config.get_collector_host()) is str)

    def test_config_get_collector_port(self):
        self.assertTrue(type(self.__config.get_collector_port()) is str)

    def test_get_agent_version(self):
        self.assertTrue(type(self.__config.get_agent_version()) is str)

    def test_get_installed_dir(self):
        self.assertTrue(type(self.__config.get_installed_dir()) is str)

    def test_is_payload_print_enabled(self):
        self.assertTrue(type(self.__config.is_payload_print_enabled()) is bool)


