import functools
import inspect
import random
import string
from apminsight import constants
from apminsight.context import (
    is_txn_active,
    is_no_active_txn,
    clear_cur_context,
    get_cur_txn,
    get_cur_tracker,
    set_cur_tracker,
)
from apminsight.agentfactory import get_agent
from apminsight.util import is_non_empty_string
from apminsight.logger import get_logger

__api_enable_check = True
agentlogger = get_logger()


def check_agent_initialize_status(func):
    def wrapper(*args, **kwargs):
        global __api_enable_check
        agent = get_agent(external=True)
        if agent:
            return func(*args, **kwargs)
        elif __api_enable_check:
            print("[Error] APM Insight custom api called before initializing the agent ")
            __api_enable_check = False

    return wrapper


def check_active_txn_status(func):
    def wrapper(*args, **kwargs):
        if is_txn_active():
            return func(*args, **kwargs)

        agentlogger.info("No Active Txn to use custom api" + str(func))

    return wrapper


def get_tracker_info(tracker_name, parent_tracker=None):

    try:
        tracker_info = {"name": tracker_name}
        if parent_tracker:
            tracker_info[constants.PARENT_TRACKER] = parent_tracker
            tracker_info[constants.PARENT_CONTEXT] = parent_tracker.get_context()
        tracker_info[constants.CONTEXT] = {
            constants.TRACE_ID_STR: parent_tracker.get_trace_id() if parent_tracker else None,
            constants.SPAN_ID_STR: "".join(random.choices(string.ascii_letters + string.digits, k=16)),
        }
        return tracker_info
    except Exception:
        return None


class CustomApiProvider:

    def bg_wrapper(original, name: str = ""):
        @functools.wraps(original)
        def _wrapper(*args, **kwargs):
            agent = get_agent(external=True)
            if agent and is_no_active_txn():
                res = None
                txn_name = name if is_non_empty_string(name) else getattr(original, "__name__", "AnnonymusBgTxn")
                tracker_info = get_tracker_info(getattr(original, "__name__", txn_name + "_tracker"))
                cur_txn = agent.check_and_create_bgtxn(txn_name, tracker_info)
                try:
                    res = original(*args, **kwargs)
                    agent.end_txn(cur_txn, res)
                except Exception as exc:
                    agent.end_txn(cur_txn, err=exc)
                    raise exc
                finally:
                    clear_cur_context()
                return res
            else:
                return original(*args, **kwargs)

        return _wrapper

    def asycn_bg_wrapper(original, name: str = ""):
        @functools.wraps(original)
        async def async_wrapper(*args, **kwargs):
            agent = get_agent(external=True)
            if agent and is_no_active_txn():
                res = None
                txn_name = name if is_non_empty_string(name) else getattr(original, "__name__", "AnnonymusBgTxn")
                tracker_info = get_tracker_info(getattr(original, "__name__", txn_name + "_tracker"))
                cur_txn = agent.check_and_create_bgtxn(txn_name, tracker_info)
                try:
                    res = await original(*args, **kwargs)
                    agent.end_txn(cur_txn, res)
                except Exception as exc:
                    agent.end_txn(cur_txn, err=exc)
                    raise exc
                finally:
                    clear_cur_context()
                return res
            else:
                return await original(*args, **kwargs)

        return async_wrapper

    @staticmethod
    def background_transaction(name: str = ""):

        def wrapper(original):
            if inspect.iscoroutinefunction(original):
                return CustomApiProvider.asycn_bg_wrapper(original, name)
            else:
                return CustomApiProvider.bg_wrapper(original, name)

        if callable(name):
            func = name
            name = ""
            return wrapper(func)
        else:
            return wrapper

    @staticmethod
    @check_agent_initialize_status
    def start_background_transaction(name: str = "AnonymousBgTxn"):
        bg_txn = None
        agent = get_agent(external=True)

        if agent and is_no_active_txn():
            try:
                tracker_info = get_tracker_info("BGTxn_root_tracker")
                bg_txn = agent.check_and_create_bgtxn(name, tracker_info)
            except:
                agentlogger.exception("while creating BackGround Transaction " + name)
        return bg_txn

    @staticmethod
    def create_transaction(name: str = "AnonymousTxn"):
        return start_background_transaction(name)

    @staticmethod
    @check_agent_initialize_status
    @check_active_txn_status
    def end_transaction(txn=None):
        from apminsight.metric.txn import Transaction

        try:
            txn = txn if isinstance(txn, Transaction) else get_cur_txn()
            agent = get_agent(external=True)
            agent.end_txn(txn)
        except Exception:
            agentlogger.exception("while ending custom API transaction")
        finally:
            clear_cur_context()

    @check_active_txn_status
    def customize_transaction_name(name: str = "CustomName") -> None:
        get_cur_txn().set_custom_name(name)

    @check_active_txn_status
    def ignore_transaction():
        get_cur_txn().ignore_txn()

    @check_active_txn_status
    def add_custom_param(key: str, val: object) -> None:
        get_cur_txn().set_custom_params(key, str(val))

    @check_agent_initialize_status
    @check_active_txn_status
    def add_custom_exception(err: Exception = None) -> None:

        agent = get_agent(external=True)
        if err and isinstance(err, Exception):
            cur_tracker = get_cur_tracker()
            tracker_info = get_tracker_info("custom_exception", cur_tracker)
            cus_tracker = agent.check_and_create_tracker(tracker_info)
            if cus_tracker:
                cus_tracker.mark_exception(err)
                cus_tracker.end_tracker()

    def custom_tracker(name=None):

        def wrapper(original):
            if inspect.iscoroutinefunction(original):
                return CustomApiProvider.async_start_tracker(original, name)
            else:
                return CustomApiProvider.start_tracker(original, name)

        if callable(name):
            func = name
            name = None
            return wrapper(func)
        else:
            return wrapper

    def start_tracker(original, name: str = None):
        module = "" if name else getattr(original, "__module__", "")
        method = name if name else getattr(original, "__name__", "custom_tracker")

        @functools.wraps(original)
        def wrapper(*args, **kwargs):
            res = err = None
            agent = get_agent(external=True)
            if agent and is_txn_active():
                parent_tracker = get_cur_tracker()
                tracker_info = get_tracker_info(
                    (module + "." + method) if is_non_empty_string(module) else method, parent_tracker
                )
                cur_tracker = agent.check_and_create_tracker(tracker_info)
                try:
                    res = original(*args, **kwargs)
                except Exception as exc:
                    err = exc
                    raise exc
                finally:
                    if cur_tracker:
                        cur_tracker.end_tracker(err)
                    set_cur_tracker(parent_tracker)
                return res
            else:
                return original(*args, **kwargs)

        return wrapper

    def async_start_tracker(original, name: str = None):
        module = "" if name else getattr(original, "__module__", "")
        method = name if name else getattr(original, "__name__", "custom_tracker")

        @functools.wraps(original)
        async def wrapper(*args, **kwargs):
            res = err = None
            agent = get_agent(external=True)
            if agent and is_txn_active():
                parent_tracker = get_cur_tracker()
                tracker_info = get_tracker_info(
                    (module + "." + method) if is_non_empty_string(module) else method, parent_tracker
                )
                cur_tracker = agent.check_and_create_tracker(tracker_info)
                try:
                    res = await original(*args, **kwargs)
                except Exception as exc:
                    err = exc
                    raise exc
                finally:
                    if cur_tracker:
                        cur_tracker.end_tracker(err)
                    set_cur_tracker(parent_tracker)
                return res
            else:
                return await original(*args, **kwargs)

        return wrapper


class TrackerContext:

    def __init__(self, name: str = ""):
        self.name = name
        self.agent = get_agent(external=True)
        self.active_txn = is_txn_active()
        self.tracker = None

    def __enter__(self):
        agent = get_agent(external=True)
        if agent and is_txn_active():
            cur_tracker = get_cur_tracker()
            tracker_info = get_tracker_info(self.name, cur_tracker)
            self.tracker = agent.check_and_create_tracker(tracker_info)

        return self

    def __exit__(self, exc, value, tb):
        if self.tracker:
            if exc is not None:
                self.tracker.mark_exception(exc)
            parent = self.tracker.get_parent()
            self.tracker.end_tracker()
            set_cur_tracker(parent)


class TransactionContext:

    def __init__(self, name: str = "AnnonymousBgtxn", tracker_name: str = "Context_root_tracker"):
        self.name = name
        self.tracker_name = tracker_name
        self.txn = None

    def __enter__(self):
        if is_no_active_txn():
            agent = get_agent(external=True)
            tracker_info = get_tracker_info(self.tracker_name)
            self.txn = agent.check_and_create_bgtxn(self.name, tracker_info) if agent else None

    def __exit__(self, exc, value, tb):
        agent = get_agent(external=True)
        if agent and self.txn:
            tracker = get_cur_tracker()
            if exc is not None:
                tracker.mark_exception(exc)
            agent.end_txn(self.txn, res=None, err=exc)
            clear_cur_context()


background_transaction = CustomApiProvider.background_transaction
add_custom_exception = CustomApiProvider.add_custom_exception
custom_tracker = CustomApiProvider.custom_tracker
add_custom_param = CustomApiProvider.add_custom_param
customize_transaction_name = CustomApiProvider.customize_transaction_name
ignore_transaction = CustomApiProvider.ignore_transaction
start_background_transaction = CustomApiProvider.start_background_transaction
end_transaction = CustomApiProvider.end_transaction
