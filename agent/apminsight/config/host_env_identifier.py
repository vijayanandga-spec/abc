import os
import socket
import urllib.request
import apminsight.constants as constansts
from apminsight.logger import agentlogger
from apminsight.util import is_non_empty_string

AWS_URL = "http://169.254.169.254/latest/meta-data/instance-id"
AWS_TOKEN_URL = "http://169.254.169.254/latest/api/token"
AWS_METADATA_URL = "http://169.254.170.2/v2/metadata"
AZURE_URL = "http://169.254.169.254/metadata/v1/maintenance"
GCP_URL = "http://metadata.google.internal/computeMetadata/v1/instance/id"


class HostIdentifier:
    def __init__(self):
        self.host_type = ""
        self.host_name = socket.gethostname()
        self.is_cloud = True
        self.get_host_environment()

    def get_host_type(self):
        return self.host_type

    def get_host_name(self):
        return self.host_name

    def is_cloud(self):
        if self.host_type == constansts.DOCKER:
            return False
        return self.is_cloud

    def get_fqdn(self):
        try:
            return socket.getfqdn()
        except Exception:
            agentlogger.info("while fetching fqdn")
        return ""

    def get_host_environment(self):
        if self.is_kubernetes():
            self.host_type = constansts.DOCKER
            agentlogger.info("Agent hosted in KUBERNETES")
        elif self.is_docker():
            agentlogger.info("Agent hosted in Docker environment")
            self.host_type = constansts.DOCKER
            # elif self.is_aws():
            #     agentlogger.info("Agent hosted in AWS environment")
            #     self.host_type = constansts.AWS
            # elif self.is_gcp():
            #     agentlogger.info("Agent hosted in GCP environment")
            #     self.host_type = constansts.GCP
            # elif self.is_azure():
            #     agentlogger.info("Agent hosted in Azure environment")
            #     self.host_type = constansts.AZURE
        else:
            agentlogger.info("Agent not hosted in cloud environment")
            self.is_cloud = False
        self.host_name = os.getenv("APMINSIGHT_HOSTNAME", self.host_name)

    def is_docker(self):
        if os.name == "nt":
            return False
        try:
            docker_env_path = os.path.join(os.sep, ".dockerenv")
            if os.path.exists(docker_env_path):
                with open("/proc/self/cgroup", "r") as cgroup:
                    cgroup_info = cgroup.read()
                    if isinstance(cgroup_info, str) and is_non_empty_string(cgroup_info):
                        line_with_id = [info for info in cgroup_info.split("\n") if "docker/" in info]
                        if line_with_id:
                            os.environ["APMINSIGHT_HOSTNAME"] = line_with_id[0].split("docker/").pop()
                            return True

                with open("/proc/self/mountinfo") as mount:
                    for line in mount:
                        if "/docker/containers/" in line:
                            os.environ["APMINSIGHT_HOSTNAME"] = line.split("/docker/containers/")[-1].split("/")[0]
                            agentlogger.info(f"hostname from the file {line.split('/docker/containers/')[-1].split('/')[0]}")
                            return True
                        
            if os.getenv("ECS_AGENT_URI",None) is not None:
                with open("/proc/self/cgroup", "r") as cgroup:
                    cgroup_info = cgroup.read()
                    if isinstance(cgroup_info, str) and "/ecs/" in cgroup_info:
                        return True
                    
                with open("/proc/self/mountinfo") as mount:
                    for line in mount:
                        if "/ecs/" in line:
                            return True        
        except Exception as exc:
            agentlogger.info(f"Exception checking docker environment {exc}")
        return False

    def is_kubernetes(self):
        if "KUBERNETES_SERVICE_HOST" in os.environ and os.getenv("KUBERNETES_SERVICE_HOST", None):
            os.environ["APMINSIGHT_HOSTNAME"] = socket.gethostname()
            return True
        return False

    def is_aws(self):
        """Check if running on AWS by querying the metadata service."""
        response = None
        try:
            request = urllib.request.Request(AWS_URL)
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status == 200:
                    self.host_name = response.read().decode("utf-8")
                    return True
        except Exception as exc:
            pass

        try:
            token_req = urllib.request.Request(AWS_TOKEN_URL, method="PUT")
            token_req.add_header("X-aws-ec2-metadata-token-ttl-seconds", "30")
            with urllib.request.urlopen(token_req) as response:
                token = response.read().decode("utf-8")
                request.add_header("X-aws-ec2-metadata-token", token)
                with urllib.request.urlopen(request) as response:
                    if response.status == 200:
                        self.host_name = response.read().decode("utf-8")
                        return True
        except Exception as exc:
            pass

        try:
            url = os.getenv("ECS_CONTAINER_METADATA_URI", AWS_METADATA_URL)
            request = urllib.request.Request(url)
            with urllib.request.urlopen(request, timeout=5) as response:
                if response.status == 200:
                    return True
        except Exception:
            pass

        return False

    def is_gcp(self):
        """Check if running on GCP by querying the metadata service."""
        try:
            request = urllib.request.Request(GCP_URL)
            request.add_header("Metadata-Flavor", "Google")
            response = urllib.request.urlopen(request, timeout=5)
            return response.status == 200
        except Exception:
            pass

        return False

    def is_azure(self):
        """Check if running on Azure by querying the metadata service."""
        if os.getenv("WEBSITE_SITE_NAME", None) != None and os.getenv("KUDU_APPPATH", None) != None:
            return True

        try:
            request = urllib.request.Request(AZURE_URL)
            request.add_header("Metadata", "true")
            response = urllib.request.urlopen(request, timeout=5)
            return response.status == 200
        except Exception:
            pass

        return False
