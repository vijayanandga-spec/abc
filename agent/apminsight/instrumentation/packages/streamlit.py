from apminsight import constants
from apminsight import get_agent
from apminsight.logger import agentlogger
from apminsight.context import clear_cur_context, get_cur_txn, get_cur_tracker
from apminsight.instrumentation.wrapper import create_tracker_info, handle_tracker_end


def get_script_path(scriptrunner, rerun_data):
    try:
        from streamlit import source_util

        main_script_path = scriptrunner._main_script_path
        pages = source_util.get_pages(main_script_path)
        main_page_info = list(pages.values())[0]
        current_page_info = None

        if rerun_data.page_script_hash:
            current_page_info = pages.get(rerun_data.page_script_hash, None)
        elif not rerun_data.page_script_hash and rerun_data.page_name:
            current_page_info = next(
                filter(
                    lambda p: p and (p["page_name"] == rerun_data.page_name),
                    pages.values(),
                ),
                None,
            )
        else:
            current_page_info = main_page_info

        script_path = current_page_info["script_path"] if current_page_info else main_script_path

        if "pages" in script_path:
            return script_path.split("pages/")[-1]
    except Exception as exc:
        agentlogger.info(f"Exception at getting stremlit script details {exc}")
    return "/"


def get_txn_params(method, path, host_name, port):
    """
    REQUEST_METHOD
    PATH_INFO
    SERVER_NAME
    SERVER_PORT
    SERVER_PROTOCOL

    """
    return {"REQUEST_METHOD": method, "PATH_INFO": path, "SERVER_NAME": host_name, "SERVER_PORT": port}


def get_request_details(path):
    try:
        from streamlit.config import get_option

        port = get_option("server.port")
        host = get_option("server.address") or get_option("browser.serverAddress")
        method = "GET"
        return get_txn_params(method, path, host, port)
    except Exception as exc:
        agentlogger.info("Error while fetching streamlit host details")
        return None


def wrap_run_script(original, module, method_info):
    def wrap(*args, **kwargs):
        cur_txn = res = cur_tracker = err = None
        agent = get_agent()
        try:
            try:
                script_path = get_script_path(*args, **kwargs)
                tracker_info = create_tracker_info(module, method_info)
                if get_cur_txn():
                    parent_tracker = get_cur_tracker()
                    tracker_info = create_tracker_info(module, method_info, parent_tracker=parent_tracker)
                    cur_tracker = agent.check_and_create_tracker(tracker_info)
                else:
                    txn_params = get_request_details(script_path)
                    cur_txn = agent.check_and_create_webtxn(txn_params, tracker_info)
            except:
                agentlogger.exception("in wsgi wrapper")
            res = original(*args, **kwargs)
            if cur_tracker:
                handle_tracker_end(cur_tracker, method_info, args, kwargs, res, err)
            else:
                agent.end_txn(cur_txn, res)
        except Exception as exc:
            if cur_tracker:
                handle_tracker_end(cur_tracker, method_info, args, kwargs, res, err=exc)
            else:
                agent.end_txn(cur_txn, err=exc)
            raise exc
        finally:
            clear_cur_context()
        return res

    return wrap


def inst_run_script(original, module, method_info):

    def wrapper(*args, **kwargs):
        method_addr = getattr(args[0], "_run_script", None)
        if method_addr:
            method_info["method"] = "_run_script"
            wrap = wrapper(method_addr, module, method_info)
            setattr(args[0], "_run_script", wrap)
        res = original(*args, **kwargs)
        return res


module_info = {
    "streamlit.runtime.scriptrunner.script_runner": [
        {
            constants.class_str: "ScriptRunner",
            constants.method_str: "_run_script",
            constants.component_str: constants.STREAMLIT,
            constants.wrapper_str: wrap_run_script,
        },
    ],
}
