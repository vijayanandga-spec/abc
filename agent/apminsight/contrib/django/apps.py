from django.apps import AppConfig
from django.conf import settings
from apminsight.agentfactory import initialize_agent
from .wrapper import instrument_middlewares
from apminsight import constants


class ApminsightConfig(AppConfig):
    name = "apminsight"

    def __init__(self, *args, **kwargs):
        super(ApminsightConfig, self).__init__(*args, **kwargs)
        self.client = initialize_agent(
            {
                constants.APPNAME: (
                    settings.APM_APP_NAME
                    if hasattr(settings, constants.apm_app_name)
                    else ApminsightConfig.get_app_name()
                ),
                constants.APP_PORT: str(settings.APM_APP_PORT) if hasattr(settings, constants.apm_app_port) else "8000",
                constants.EXP_HOST: getattr(settings, constants.APM_EXP_HOST, constants.localhost_str),
                constants.EXP_STATUS_PORT: (
                    str(settings.APM_EXPORTER_STATUS_PORT)
                    if hasattr(settings, constants.APM_EXP_STATUS_PORT)
                    else "20021"
                ),
                constants.EXP_DATA_PORT: (
                    str(settings.APM_EXPORTER_DATA_PORT) if hasattr(settings, constants.APM_EXP_DATA_PORT) else "20022"
                ),
                # 'license_key' : settings.APM_LICENSE_KEY if hasattr(settings, 'APM_LICENSE_KEY') else None,
                # 'apm_collector_host' : settings.APM_COLLECTOR_HOST if hasattr(settings, 'APM_COLLECTOR_HOST') else None,
                # 'apm_collector_port' : settings.APM_COLLECTOR_PORT if hasattr(settings, 'APM_COLLECTOR_PORT') else None,
                # 'proxy_server_host' : settings.APM_PROXY_SERVER_HOST if hasattr(settings, 'APM_PROXY_SERVER_HOST') else None,
                # 'proxy_server_port' : settings.APM_PROXY_SERVER_PORT if hasattr(settings, 'APM_PROXY_SERVER_PORT') else None,
                # 'proxy_auth_username' : settings.APM_PROXY_AUTH_USERNAME if hasattr(settings, 'APM_PROXY_AUTH_USERNAME') else None,
                # 'proxy_auth_password' : settings.APM_PROXY_AUTH_PASSWORD if hasattr(settings, 'APM_PROXY_AUTH_PASSWORD') else None
            }
        )

    def ready(self):
        instrument_middlewares()

    @staticmethod
    def get_app_name():
        appname = ""
        try:
            wsgi_app = settings.WSGI_APPLICATION
            appname = wsgi_app.split(".")[0]
        except Exception:
            pass

        return appname
