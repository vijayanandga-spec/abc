from apminsight import constants
from apminsight.context import get_cur_tracker
from apminsight.logger import agentlogger


def extract_host_details(tracker, args=(), kwargs={}, return_value=None, error=None):
    try:
        from pymongo.server import Server

        if isinstance(return_value, Server):
            (host, port) = return_value._description._address
            tracker.set_info({constants.host_str: host, constants.port_str: port})
    except Exception as exc:
        agentlogger.info("Error while fetching mongo db connection details " + str(exc))


def wrap_topology(original, method, method_info):
    def wrapper(*args, **kwargs):
        err = None
        res = None
        try:
            res = original(*args, **kwargs)
        except Exception as exc:
            err = exc
            raise exc
        finally:
            tracker = get_cur_tracker()
            if tracker:
                extract_host_details(tracker, args, kwargs, res, err)
        return res

    return wrapper


def extract_query(tracker, args=(), kwargs={}, return_value=None, error=None):
    try:
        operation = tracker.get_tracker_name().split(".")[-1]
        obj = args[0].database.name + "." + args[0].name
        tracker.set_info(
            {
                constants.query_str: "NoSQL: " + operation + " from " + obj + " WHERE " + str(args[1]),
                constants.OPERATION: operation,
                constants.OBJECT: obj,
            }
        )
        tracker.set_tracker_name(operation + obj)
    except:
        agentlogger.exception("while extracting mongodb query details")


_pymongo_database_methods = (
    "get_collection",
    "create_colleclist_databasestion",
    "aggregate",
    "command",
    "drop_collection",
    "list_collections",
    "list_collection_names",
)

_pymongo_collection_methods = (
    "insert_one",
    "insert_many",
    "replace_one",
    "update_one",
    "update_many",
    "drop",
    "delete_one",
    "delete_many",
    "find_one",
    "find",
    "find_raw_batches",
    "estimated_document_count",
    "count_documents",
    "create_indexes",
    "create_index",
    "drop_indexes",
    "drop_index",
    "list_indexes",
    "index_information",
    "options",
    "aggregate",
    "aggregate_raw_batches",
    "rename",
    "find_one_and_delete",
    "find_one_and_replace",
    "find_one_and_update",
)

module_info = {
    "pymongo.mongo_client": [
        {
            constants.class_str: "MongoClient",
            constants.method_str: "__init__",
            constants.component_str: constants.MONGO_COMP,
        },
        {
            constants.class_str: "MongoClient",
            constants.method_str: "list_databases",
            constants.component_str: constants.MONGO_COMP,
        },
        {
            constants.class_str: "MongoClient",
            constants.method_str: "drop_database",
            constants.component_str: constants.MONGO_COMP,
        },
    ],
    "pymongo.topology": [
        {
            constants.class_str: "Topology",
            constants.method_str: "_select_server",
            constants.wrapper_str: wrap_topology,
        },
    ],
    "pymongo.database": [
        {
            constants.class_str: "Database",
            constants.method_str: "__init__",
            constants.component_str: constants.MONGO_COMP,
            # constants.is_db_tracker_str : True
        },
        {
            constants.class_str: "Database",
            constants.method_str: _pymongo_database_methods,
            constants.component_str: constants.MONGO_COMP,
            constants.extract_info_str: extract_query,
            # constants.extract_info_str : apm_extract_query,
            constants.is_db_tracker_str: True,
        },
    ],
    "pymongo.collection": [
        {
            constants.class_str: "Collection",
            constants.method_str: "__init__",
            constants.component_str: constants.MONGO_COMP,
            # constants.extract_info_str : extract_query,
            # constants.is_db_tracker_str : True
        },
        {
            constants.class_str: "Collection",
            constants.method_str: _pymongo_collection_methods,
            constants.component_str: constants.MONGO_COMP,
            constants.extract_info_str: extract_query,
            constants.is_db_tracker_str: True,
        },
    ],
}
