agent_instance = None


def get_agent(config={}, external=None):
    global agent_instance
    if external:
        return agent_instance
    if agent_instance is None:
        try:
            from apminsight.agent import Agent

            agent_instance = Agent.initialize(options=config)
            print("APM Insight agent initialized successfully")
        except Exception as exc:
            from apminsight.logger import agentlogger

            print("[ERROR] APM Insight agent initialization failed %s " % str(exc))
            agentlogger.exception(f"[ERROR] APM Insight agent initialization failed {exc}")

    return agent_instance


def initialize_agent(config={}):
    from .logger import create_agentlogger

    create_agentlogger(config)
    from .instrumentation.instrument import init_instrumentation

    init_instrumentation()
    get_agent(config)
