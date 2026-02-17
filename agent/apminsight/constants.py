CLASS = class_str = "class"
METHOD = method_str = "method"
wrapper_str = "wrapper"
COMPONENT = component_str = "component"
wrap_args_str = "wrap_args"
EXTRACT_INFO = extract_info_str = "extract_info"
connect_details = "connect_details"
HOST = host_str = "host"
PORT = port_str = "port"
default_host_str = "default_host"
default_port_str = "default_port"
is_db_tracker_str = "is_db_tracker"
LOCALHOST = localhost_str = "localhost"
path_info_str = "PATH_INFO"
query_string_str = "QUERY_STRING"
request_method_str = "REQUEST_METHOD"
server_name_str = "SERVER_NAME"
server_port_str = "SERVER_PORT"
transaction_info_str = "transaction_info"
method_info_str = "method_info"
level_str = "level"
QUERY = query_str = "query"
status_code_str = "status_code"
proxy_class_str = "proxy_class"
python_str = "PYTHON"
data_str = "data"
TRACE_ID_STR = "trace_id"
SPAN_ID_STR = "span_id"
CUSTOMPARAMS = "CustomParams"
CONTEXT = "context"
PARENT_CONTEXT = "parent_context"
PARENT_TRACKER = "parent"
ASYNC_PARENT_CONTEXT = "async_parent_context"
IS_ASYNC = "is_async"
LOGINFO = "loginfo"
EXP_STACK_TRACE = "exception_st"
OPERATION = "opn"
OBJECT = "obj"
DB_OPERATION = "db_opn"
STACKTRACE = "stacktrace"
HTTP_METHOD = "http_method"
URL = "url"
STATUS = "status"
DEFAULT_APM_APP_NAME = "Python-Application"
MIDDLEWARE = "MIDDLEWARE"
MIDDLEWARE_CLASSES = "MIDDLEWARE_CLASSES"
APPNAME = "appname"
APP_PORT = "app_port"
EXP_HOST = "exporter_host"
EXP_STATUS_PORT = "exporter_status_port"
EXP_DATA_PORT = "exporter_data_port"
LOG_FILE_SIZE = "log_file_size"
LOG_FILE_BACKUP_COUNT = "log_file_count"
DOCKER = "DOCKER"
AWS = "AWS"
GCP = "GCP"
AZURE = "AZURE"

APM_CUSTOM_INSTRUMENT_FILE_PATH = "APM_CUSTOM_INSTRUMENT_FILE_PATH"

HTTP_HOST = "HTTP_HOST"
HOST_NAME = "host_name"
APP_NAME = "app_name"
PROXY_DETAILS = "proxy_details"
AGENT_VERSION = "agent_version"
SETUP_CONFIG = "setup_config"
THRESHOLD_CONFIG = "threshold_config"

exporter_param_key_http_host = "http_host"
exporter_param_key_request_url = "t_name"
exporter_param_key_transaction_duration = "r_time"
exporter_param_key_request_method = "http_method_name"
exporter_param_key_bytes_in = "bytes_in"
exporter_param_key_bytes_out = "bytes_out"
exporter_param_key_transaction_type = "transaction_type"
exporter_param_key_distributed_count = "dt_count"
exporter_param_key_thread_id = "thread_id"
exporter_param_key_response_code = "httpcode"
exporter_param_key_collection_time = "s_time"
exporter_param_key_collection_end_time = "e_time"
exporter_param_key_cpu_time = "cputime"
exporter_param_key_memory_usage = "memory_usage"
exporter_param_key_method_count = "method_count"
exporter_param_key_trace_id = "trace_id"
exporter_param_key_instance_id = "instance_id"
exporter_param_key_request_headers = "request_headers"
exporter_param_key_custom_params = "custom_params"
exporter_param_key_query_string = "http_query_str"
exporter_param_key_application_type = "application_type"
exporter_param_key_application_name = "application_name"
exporter_param_key_bytes_in = "bytes_in"
exporter_param_key_bytes_out = "bytes_out"
exporter_param_key_memory_usage = "memalloc"
exporter_param_key_session_id = "session_id"
exporter_param_key_rum_appkey = "rum_appkey"
exporter_param_key_http_headers = "http_headers"
exporter_param_key_http_input_params = "http_input_params"
exporter_param_key_async = "async"

RESPONSE_HEADERS = "response_headers"
REQUEST_HEADERS = "request_headers"

SH_ASYNC_ROOT = "ar"
SH_EXT_COMP = "ex"
SH_IS_FAULT = "if"
SH_IS_ERROR = "ie"
SH_HOST_NAME = "hn"
SH_PORT_NUMBER = "pn"
SH_STACK_TRACE = SH_START_TIME = "st"
SH_END_TIME = "et"
SH_FUN_NAME = "fn"
SH_COMP_NAME = "cn"
SH_SPAN_ID = "si"
SH_PAR_SPAN_ID = "psi"
SH_QUERY_STR = "qs"
SH_DIST_TRACE = "dt"
SH_ERR_MSG = SH_STRING = "str"
SH_ERR_CLS = "err_clz"
SH_ERR_INFO = "ei"
SH_ERR_STACK_TRACE = "mst"
SH_SPAN_PRIORITY = "pr"

TRACKER_NAME = "tracker_name"
TIME = RESPONSE_TIME = "time"
CHILD_OVERHEAD = "child_overhead"
CHILD_TRACKER_COUNT = "child_tracker_count"
PROCESS_ID = "processid"

arh_connect = "/arh/connect"
arh_data = "/arh/data"
arh_trace = "/arh/trace"
webtxn_prefix = "transaction/http"
webtxn_type = 1
bgtxn_prefix = "transaction/bckgrnd"
bgtxn_type = 0
DEFAULT_EXP_STATUS_PORT = default_exp_status_port = 20021
DEFAULT_EXP_DATA_PORT = default_exp_data_port = 20022
default_app_monitor_name = "Python-Application"
default_app_port = 8080

aws_url = "http://169.254.169.254/latest/meta-data/instance-id"
azure_url = "http://169.254.169.254/metadata/v1/InstanceInfo"

instanceinfo = "instance-info"
responsecode = "response-code"
instanceid = "instanceid"
collectorinfo = "collector-info"

manage_agent = 911
license_expired = 701
license_instance_exceeded = 702
instance_add_failed = 703
delete_agent = 900
invalid_agent = 901
unmanage_agent = 910
agent_license_updated = 915
agent_config_updated = 920
shutdown = 0

LOG_FILE_MODE = "a"
DEFAULT_LOG_FILE_SIZE = 5 * 1024 * 1024
DEFAULT_LOG_FILE_BACKUP_COUNT = 10
LOG_FILE_ENCODEING = None
LOG_FILE_DELAY = 0

conf_file_name = "apminsight_conf.json"
info_file_name = "apminsight.json"
base_dir = "apminsightdata"
logs_dir = "logs"
log_name = "apminsight-agent-log.txt"
agent_logger_name = "apminsight-agent"
log_format = "%(asctime)s %(processid)s %(levelname)s %(message)s"
AGENT_CONFIG_INFO_FILE_NAME = "apminsight_info.json"

S247_LICENSE_KEY = license_key_env = "S247_LICENSE_KEY"
APM_APP_NAME = apm_app_name = "APM_APP_NAME"
APM_PYTHON_AGENT_VERSION = "APM_PYTHON_AGENT_VERSION"
APM_APP_PORT = apm_app_port = "APM_APP_PORT"
APM_PRINT_PAYLOAD = apm_print_payload = "APM_PRINT_PAYLOAD"
APM_COLLECTOR_HOST = apm_collector_host = "APM_COLLECTOR_HOST"
APM_COLLECTOR_PORT = apm_collector_port = "APM_COLLECTOR_PORT"
APM_PORXY = apm_proxy = "APM_PROXY"
PROXY_SERVER_HOST = "PROXY_SERVER_HOST"
PROXY_SERVER_PORT = "PROXY_SERVER_PORT"
PROXY_AUTH_USERNAME = "PROXY_AUTH_USERNAME"
PROXY_AUTH_PASSWORD = "PROXY_AUTH_PASSWORD"
APM_LOGS_DIR = apm_logs_dir = "APM_LOGS_DIR"
APM_CONFIG_DIR = "APM_CONFIG_DIR"
APM_SSL_PORT = ssl_port = "443"
APM_EXPORTER = "APM_EXPORTER"
APM_EXP_HOST = "APM_EXPORTER_HOST"
APM_EXP_STATUS_PORT = "APM_EXPORTER_STATUS_PORT"
APM_EXP_DATA_PORT = "APM_EXPORTER_DATA_PORT"
APM_LOG_FILE_SIZE = "APM_LOG_FILE_SIZE"
APM_LOG_FILE_BACKUP_COUNT = "APM_LOG_FILE_COUNT"
PROCESS_CPU_THRESHOLD = "APM_PROCESS_CPU_THRESHOLD"
PROCESS_CPU_THRESHOLD_VAL = 60.0
APM_TAGS = "APMINSIGHT_TAGS"
APM_GROUPS = "APMINSIGHT_MONITOR_GROUP"

APMINSIGHT_INSTALL_DIR = "APMINSIGHT_INSTALL_DIR"
APMINSIGHT_RUN_COMMAND_DIR = "APMINSIGHT_RUN_COMMAND_DIR"
APMINSIGHT_RUN_EXECUTABLE_COMMAND = "APMINSIGHT_RUN_EXECUTABLE_COMMAND"

INFO_KEYS = {
    "appname": APM_APP_NAME,
    "license_key": S247_LICENSE_KEY,
    "logs_dir": APM_LOGS_DIR,
    "exporter": APM_EXPORTER,
    "exporter_host": APM_EXP_HOST,
    "exporter_status_port": APM_EXP_STATUS_PORT,
    "exporter_data_port": APM_EXP_DATA_PORT,
    "app_port": APM_APP_PORT,
    "apm_collector_port": APM_COLLECTOR_HOST,
    "proxy_server_host": PROXY_SERVER_HOST,
    "porxy_server_port": PROXY_SERVER_PORT,
    "proxy_auth_username": PROXY_AUTH_USERNAME,
    "proxy_auth_password": PROXY_AUTH_PASSWORD,
    "cpu_threshold": PROCESS_CPU_THRESHOLD,
    "log_file_size": APM_LOG_FILE_SIZE,
    "log_file_count": APM_LOG_FILE_BACKUP_COUNT,
}


us_collector_host = "plusinsight.site24x7.com"
eu_collector_host = "plusinsight.site24x7.eu"
cn_collector_host = "plusinsight.site24x7.cn"
ind_collector_host = "plusinsight.site24x7.in"
aus_collector_host = "plusinsight.site24x7.net.au"
jp_collector_host = "plusinsight.site24x7.jp"

custom_config_info = "custom_config_info"
agent_specific_info = "agent_specific_info"
log_level = "apminsight.log.level"
apdexth = "apdex.threshold"
sql_capture = "sql.capture.enabled"
sql_parametrize = "transaction.trace.sql.parametrize"
last_modified_time = "last.modified.time"
trace_threshold = "transaction.trace.threshold"
trace_enabled = "transaction.trace.enabled"
sql_stacktrace = "transaction.trace.sql.stacktrace.threshold"
web_rum_appkey = "webtransaction.rum.key"
webtxn_naming_use_requesturl = "webtransaction.naming.use.requesturl"
web_txn_sampling_factor = "transaction.tracking.request.interval"
auto_upgrade = "autoupgrade.enabled"
txn_skip_listening = "transaction.skip.listening"
txn_tracker_drop_th = "webtransaction.tracker.drop.threshold"
txn_trace_ext_count_th = "webtransaction.trace.external.components.count.threshold"


bgtxn_tracking_enabled = "bgtransaction.tracking.enabled"
bgtxn_trace_enabled = "bgtransaction.trace.enabled"
bgtxn_traceth = "bgtransaction.trace.threshold"
bgtxn_sampling_factor = "bgtransaction.tracking.request.interval"

LICENSE_KEY_FOR_DT_REQUEST = "S247-license"
LICENSE_KEY_FOR_DT_REQUEST_HTTP = "HTTP_S247_LICENSE"
DT_LK_KEY = "DT_LK_KEY"
DTDATA = "dtdata"
DT_TXN_NAME = "t_name"
DT_ST_TIME = "s_time"
DT_INS_ID = "instance_id"

apdex_metric = "metricstore.metric.bucket.size"
db_metric = "metricstore.dbmetric.bucket"
bg_metric = "metricstore.bgmetric.bucket.size"
trace_size = "transaction.tracestore.size"

select_query_matcher = r"\s*(select)\s+.*from\s+(\S+)?.*"
insert_query_matcher = r"\s*(insert)\s+into\s+(\S+)?[(]?.*"
update_query_matcher = r"\s*(update)\s+(\S+)?.*"
delete_query_matcher = r"\s*(delete)\s+.*from\s+(\S+)?.*"
create_query_matcher = r"\s*(create)\s+(?:table|procedure|database|keyspace)\s+(?:if not exists\s+)?(\S+)?[(]?.*"
drop_query_matcher = r"\s*(drop)\s+(?:table|procedure|database|keyspace)\s+(?:if exists\s+)?(\S+)?.*"
alter_query_matcher = r"\s*(alter)\s+(?:table|procedure|database|keyspace)\s+(\S+)?.*"
call_sp_matcher = r"\s*(call)\s+([`\w]+)[\s()]*.*"
exec_sp_matcher = r"\s*(exec)\s+([`\w]+)[\s()]*.*"
show_query_matcher = r"\s*(show)\s+(\w+)(\s+)?.*"


db_opn_regex = {
    "select": select_query_matcher,
    "insert": insert_query_matcher,
    "update": update_query_matcher,
    "delete": delete_query_matcher,
    "create": create_query_matcher,
    "drop": drop_query_matcher,
    "alter": alter_query_matcher,
    "show": show_query_matcher,
    "call": call_sp_matcher,
    "exec": exec_sp_matcher,
}


max_trackers = 1000
max_exc_per_trace = 20
django_comp = "DJANGO"
flask_comp = "FLASK"
bottle_comp = "BOTTLE"
pyramid_comp = "PYRAMID"
cherrypy_comp = "CHERRYPY"
sqlite_comp = "SQLITE"
postgres_comp = "POSTGRES"
mysql_comp = "MYSQL"
redis_comp = "REDIS"
memcache_comp = "MEMCACHED"
middleware = "MIDDLEWARE"
template = "TEMPLATE"
jinja_comp = "JINJA"
mako_comp = "MAKO"
genshi_comp = "GENSHI"
cassandra_comp = "CASSANDRA"
ORACLE_DSN_FORMAT = r"(?:([^:\/]+)\/?(?:([^@]+))?@)?([^:\/]+)\:?(\d*)?\/?(.*)?"
ORACLE_DEFAULT_PORT = 1521
ORACLE_COMP = oracle_comp = "ORACLE"
pyodbc_comp = "PYODBC"
HTTP = http_comp = "HTTP"
MONGO_COMP = mongo_comp = "MONGODB"
python_comp = "PYTHON"
mssql_comp = "MSSQL"
REQUESTS = "REQUESTS"
REQUEST_URL = "request_url"
APM_INSTRUMENTED = "apminsight_instrumented"
fastapi_comp = "FastAPI"
starlette_comp = "STARLETTE"
tornado_comp = tornado = "TORNADO"
DEFAULT_TORNADO_PORT = 8888
streamlit_comp = STREAMLIT = "STREAMLIT"
async_cron = "ASYNC_CRON"
celery = "CELERY"
gunicorn_comp = "GUNICORN"
waitress_comp = "WAITRESS"
cheroot_comp = "CHEROOT"
wsgiref_comp = "WSGIREF"
werkzeug_comp = 'WERKZEUG'
rabbitmq_comp = "RABBITMQ"
falcon_comp = "FALCON"


int_components = [
    django_comp,
    flask_comp,
    middleware,
    jinja_comp,
    mako_comp,
    genshi_comp,
    cherrypy_comp,
    bottle_comp,
    pyramid_comp,
    fastapi_comp,
    starlette_comp,
    tornado_comp,
    streamlit_comp,
    async_cron,
    celery,
    gunicorn_comp,
    waitress_comp,
    cheroot_comp,
    wsgiref_comp,
    werkzeug_comp,
    falcon_comp
]
ext_components = [
    mysql_comp,
    redis_comp,
    memcache_comp,
    postgres_comp,
    cassandra_comp,
    http_comp,
    sqlite_comp,
    mongo_comp,
    oracle_comp,
    mssql_comp,
    pyodbc_comp,
    rabbitmq_comp,
]


class AutoProfilerConstants:
    CONF_FILEPATH = "APMINSIGHT_AUTOPROFILER_CONF_FILEPATH"
    HOMEPATH = "APMINSIGHT_AGENT_HOMEPATH"
    SECTION = "apminsight_auto_profiler"
    KEY = "APMINSIGHT_LICENSEKEY"
    AGENT_ID = "APMINSIGHT_AGENT_ID"
    START_TIME = "APMINSIGHT_AGENT_START_TIME"
    SERVER_MONITOR_KEY = "SERVER_MONITOR_KEY"
    PROCESS_UID = "APMINSIGHT_PROCESS_UID"
    RULE_NAME = "APMINSIGHT_PROCESS_MONITORING_RULE_NAME"


class SpanConstants:
    ASYNC_ROOT = SH_ASYNC_ROOT = "ar"
    EXT_COMP = SH_EXT_COMP = "ex"
    IS_FAULT = SH_IS_FAULT = "if"
    IS_ERROR = SH_IS_ERROR = "ie"
    HOST_NAME = SH_HOST_NAME = "hn"
    PORT_NUMBER = SH_PORT_NUMBER = "pn"
    START_TIME = STACK_TRACE = SH_STACK_TRACE = SH_START_TIME = "st"
    END_TIME = SH_END_TIME = "et"
    FUN_NAME = SH_FUN_NAME = "fn"
    COMP_NAME = SH_COMP_NAME = "cn"
    SPAN_ID = SH_SPAN_ID = "si"
    PAR_SPAN_ID = SH_PAR_SPAN_ID = "psi"
    QUERY_STR = SH_QUERY_STR = "qs"
    DIST_TRACE = SH_DIST_TRACE = "dt"
    ERR_MSG = SH_ERR_MSG = SH_STRING = "str"
    ERR_CLS = SH_ERR_CLS = "err_clz"
    ERR_INFO = SH_ERR_INFO = "ei"
    ERR_STACK_TRACE = SH_ERR_STACK_TRACE = "mst"
    SPAN_PRIORITY = SH_SPAN_PRIORITY = "pr"
    REQUEST_HEADERS = "erqh"
    RESPONSE_HEADERS = "ersh"
    STATUS = "esc"

class InstanceSpecificConfig:
    INSTANCE_ID = "instance.id"
    APP_ID = "app.id"
    INSTANCE_STATUS = "instance.status"
    LOG_LEVEL = "apminsight.log.level"    

class TxnSpecificConfig:
    NORMALIZED_URL = "normalised.txn.name"
    SQL_ST_THRESHOLD = "transaction.trace.sql.stacktrace.threshold"
    TRACKER_DROP_THRESHOLD = "webtransaction.tracker.drop.threshold"
    RUM_APPKEY = "webtransaction.rum.key"
    TXN_NAME_USE_REQUESTURL = "webtransaction.naming.use.requesturl"

