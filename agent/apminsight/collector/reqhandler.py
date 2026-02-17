import json
from apminsight.logger import agentlogger
from apminsight.agentfactory import get_agent


def send_req(path_uri, payload):
    response = ""
    response_data = {}
    try:
        config = get_agent().get_config()
        url = "https://" + config.get_collector_host() + ":" + config.get_collector_port() + path_uri
        query_param = (
            "license.key=" + config.get_license_key() + "&instance_id=" + get_agent().get_ins_info().get_instance_id()
        )
        complete_url = url + "?" + query_param
        headers = {"content-type": "application/json"}
        payload_str = json.dumps(payload)
        agentlogger.info("sending request to " + url)
        if config.is_payload_print_enabled():
            agentlogger.info("payload :" + payload_str)
        proxy_details = config.get_proxy_details() if not False else {}
        response = {}  # requests.post(complete_url, data=payload_str, headers=headers, proxies=proxy_details)
        response_data = response.json()
        agentlogger.info("request details  " + str(complete_url) + " " + str(headers) + " " + str(proxy_details))
    except Exception:
        agentlogger.exception(path_uri + " req error " + str(response))

    agentlogger.info("response for " + path_uri + " request : " + json.dumps(response_data))
    return response_data
