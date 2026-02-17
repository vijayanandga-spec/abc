from apminsight import constants
from apminsight.util import is_ext_comp, is_non_empty_string


class Component:

    def __init__(self, tracker):
        self.name = tracker.get_component()
        self.rt = tracker.get_rt()
        self.ext = is_ext_comp(tracker.get_component())
        self.count = 0
        self.errcount = 0
        self.http_err = 0
        self.host = tracker.get_info().get(constants.host_str, "")
        self.port = tracker.get_info().get(constants.port_str, "-1") or "-1"
        if tracker.is_error() or tracker.is_http_err():
            self.errcount += 1
        else:
            self.count += 1

    def get_name(self):
        return self.name

    def get_rt(self):
        return self.rt

    def is_ext(self):
        return self.ext

    def get_count(self):
        return self.count

    def get_error_count(self):
        return self.errcount

    def get_host(self):
        return self.host

    def get_port(self):
        return self.port

    def is_same_machine(self, anothercomp):
        if self.is_ext() != anothercomp.is_ext():
            return False

        if self.is_ext() and anothercomp.is_ext():
            return self.get_host() == anothercomp.get_host() and self.get_port() == anothercomp.get_port()

        return True

    def aggregate(self, another):
        self.name = another.get_name()
        self.rt += another.get_rt()
        self.count += another.get_count()
        self.errcount += another.get_error_count()

    def get_comp_index(self):
        if self.is_ext():
            return self.get_name() + self.get_host() + str(self.get_port())

        return self.get_name()

    def aggregate_to_global(self, comps_aggregated):
        comp_index = self.get_comp_index()
        comp_info = comps_aggregated.get(comp_index, None)
        if comp_info is not None:
            comp_info.aggregate(self)
        else:
            comps_aggregated[comp_index] = self

    def check_and_aggregate_component(self, collected_comps, cur_component, comp_index):
        comp_info = collected_comps.get(comp_index, None)
        if comp_info is not None:
            comp_info.aggregate(cur_component)
        else:
            collected_comps[comp_index] = cur_component

    def get_info_as_obj(self):
        info = {}
        info["name"] = self.name
        info["rt"] = self.rt
        info["ct"] = self.count
        info["isExt"] = 1 if self.is_ext() else 0
        if self.errcount > 0:
            info["error"] = self.get_error_count()

        port_number = int(self.port)
        if is_non_empty_string(self.host) and port_number > 0:
            info[constants.host_str] = self.host
            info[constants.port_str] = self.port

        return info
