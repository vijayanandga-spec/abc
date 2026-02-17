import ast
from apminsight import constants
from apminsight.logger import agentlogger
from apminsight.context import get_cur_tracker
from apminsight.metric.tracker import Tracker


def handle_dt_response_headers(return_value):
    if return_value:
        try:
            if return_value.headers.get(constants.DTDATA):
                cur_tracker = get_cur_tracker()
                if isinstance(cur_tracker, Tracker):
                    dtdata = ast.literal_eval(return_value.headers[constants.DTDATA])
                    dtdata[constants.DT_TXN_NAME] = constants.webtxn_prefix + dtdata[constants.DT_TXN_NAME]
                    dtdata[constants.DT_ST_TIME] = int(dtdata[constants.DT_ST_TIME])
                    cur_tracker.set_info({constants.DTDATA: dtdata})
                    cur_tracker.set_dt_trace()
        except:
            agentlogger.exception("while extracting response headers for distributed trace")
