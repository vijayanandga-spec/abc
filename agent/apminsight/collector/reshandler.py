from apminsight.logger import agentlogger
from apminsight.agentfactory import get_agent
from apminsight import constants


def handle_connect_response(res_data={}):
    try:
        if type(res_data) is not dict:
            return False

        data = res_data.get("data", None)

        if data is None or type(data) is not dict:
            return False

        res_code = data.get(constants.responsecode, None)
        instance_info = data.get(constants.instanceinfo, None)
        agent = get_agent()

        if res_code is not None:
            agentlogger.critical("received response code :" + str(res_code))

        if instance_info is None:
            agent.get_ins_info().update_status(res_code)
            return False

        instance_id = instance_info.get(constants.instanceid, None)

        if instance_id is None:
            return False

        agent.get_ins_info().update_instance_info(instance_id, res_code)
        agent.get_config().update_collector_info(data.get(constants.collectorinfo, None))
        agent.get_threshold().update(
            data.get(constants.custom_config_info, None), data.get(constants.agent_specific_info, None)
        )
        return True
    except Exception:
        agentlogger.exception("connect response handler")
        return False


def handle_data_response(res_data={}):
    try:
        if type(res_data) is not dict:
            return False

        data = res_data.get("data", None)

        if data is None:
            return False

        res_code = data.get(constants.responsecode, None)
        agent = get_agent()
        instance_info = agent.get_ins_info()

        if res_code is not None and res_code != instance_info.get_status():
            agentlogger.critical("received response code :" + str(res_code))

        instance_info.update_status(res_code)
        agent.get_config().update_collector_info(data.get(constants.collectorinfo, None))
        agent.get_threshold().update(
            data.get(constants.custom_config_info, None), data.get(constants.agent_specific_info, None)
        )
        return True
    except Exception:
        agentlogger.exception("data response handler")
        return False
