from apminsight.logger import agentlogger
from apminsight.util import current_milli_time


name = "name"
time_interval = "timeinterval"
req_interval = "reqinterval"
exhaust = "exhaust"
shutdown = "shutdown"

res_codes_info = {
    701: {
        name: "LICENSE_EXPIRED",
        time_interval: [10, 30, 60, 3 * 24 * 60],
        req_interval: [1, 2, 5, 15],
        exhaust: 60,
        shutdown: 15 * 24 * 60,
    },
    702: {
        name: "LICENSE_INSTANCES_EXCEEDED",
        time_interval: [10, 30, 60, 3 * 24 * 60],
        req_interval: [1, 2, 5, 15],
        exhaust: 60,
        shutdown: 15 * 24 * 60,
    },
    703: {name: "INSTANCE_ADD_FAILED", time_interval: [10, 20, 30], req_interval: [1, 2, 5], exhaust: 15},
    704: {name: "INSUFFICIENT_CREDITS", shutdown: -1},
    900: {
        name: "MARKED_FOR_DELETE",
        time_interval: [10, 20, 30],
        req_interval: [1, 2, 5],
        exhaust: 15,
        shutdown: 3 * 24 * 60,
    },
    901: {
        name: "INVALID_AGENT",
        time_interval: [10, 20, 30],
        req_interval: [1, 2, 5],
        exhaust: 15,
        shutdown: 3 * 24 * 60,
    },
    910: {
        name: "UNMANAGE_AGENT",
    },
    911: {name: "MANAGE_AGENT"},
    0: {name: "SHUTDOWN"},
}


def is_valid_rescode(rescode):
    res_info = res_codes_info.get(rescode, None)
    if res_info is None:
        return False

    return True


def get_rescode_message(rescode):
    res_info = res_codes_info.get(rescode, None)
    if res_info is None:
        agentlogger.warning("Unknown response code :" + str(rescode))
        return f"Unknown Code {str(rescode)}"

    return res_info[name]


def is_allowed_to_send_request(rescode, retry_counter):
    res_info = res_codes_info.get(rescode, None)
    if res_info is None or type(retry_counter) is not int:
        agentlogger.critical("invalid rescode :" + str(rescode) + " counter: " + str(retry_counter))
        return True

    time_interval = res_info.get("timeinterval", None)
    if time_interval is None:
        agentlogger.info("No time limit restriction for rescode:" + str(rescode))
        return True

    for index in range(0, len(time_interval)):
        time_limit = time_interval[index]
        if retry_counter < time_limit:
            return retry_counter % res_info["reqinterval"][index] == 0

    if retry_counter > time_limit:
        return retry_counter % res_info["exhaust"] == 0

    return True


def is_retry_limit_exceeded(rescode, retry_counter):
    if rescode is None or type(retry_counter) is not int:
        return False

    res_info = res_codes_info[rescode]
    if res_info is None:
        agentlogger.critical("Unknown response code :" + str(rescode))
        return False

    if "shutdown" not in res_info:
        return False

    shutdown_limit = res_info.get("shutdown")
    if retry_counter < shutdown_limit:
        return False

    return True


def get_retry_counter(rescode, occured_time):
    if rescode is None or occured_time is None:
        return 1

    res_info = res_codes_info.get(rescode, None)
    if res_info is None:
        agentlogger.critical("Unknown response code :" + str(rescode))
        return 1

    time_interval = res_info.get("timeinterval", None)
    if time_interval is not None:
        cur_time = current_milli_time()
        diff = (cur_time - occured_time) / (60 * 1000)
        return int(diff)

    return 1
