import os
from .agentfactory import initialize_agent, get_agent
from .custom_api import (
    background_transaction,
    start_background_transaction,
    end_transaction,
    customize_transaction_name,
    ignore_transaction,
    custom_tracker,
    add_custom_exception,
    add_custom_param,
    TransactionContext,
    TrackerContext,
)

name = "apminsight"

version = "1.8.1"
os.environ["APM_PYTHON_AGENT_VERSION"] = version
installed_path = os.environ["APM_INSTALLED_DIR"] = os.path.dirname(__file__)
application_path = os.getcwd()

__all__ = [
    "name",
    "version",
    "installed_path",
    "get_agent",
    "initialize_agent",
    "background_transaction",
    "start_background_transaction",
    "end_transaction",
    "customize_transaction_name",
    "ignore_transaction",
    "custom_tracker",
    "add_custom_exception",
    "add_custom_param",
    "TransactionContext",
    "TrackerContext",
]
