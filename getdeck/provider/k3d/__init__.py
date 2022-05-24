import logging
import os
import re
import sys
import subprocess
import tempfile
import traceback
from typing import List, Dict, Optional

from semantic_version import Version

from getdeck.configuration import ClientConfiguration
from getdeck.provider.abstract import AbstractK8sProvider
from getdeck.provider.types import K8sProviderType
from getdeck.utils import CMDWrapper

logger = logging.getLogger("deck")


class K3d(AbstractK8sProvider, CMDWrapper):
    kubernetes_cluster_type = K8sProviderType.k3d
    provider_type = "k3d"
    base_command = "k3d"
    _cluster = []

    def __init__(
        self,
        config: ClientConfiguration,
        name: str,
        native_config: dict,
        _debug_output=False,
    ):

        # abstract kubernetes cluster
        AbstractK8sProvider.__init__(
            self,
            name=name,
        )
        self.config = config
        self.native_config = native_config
        # CMDWrapper
        self._debug_output = _debug_output

        # cluster name
        cluster_name = config.K3D_CLUSTER_PREFIX + self.name.lower()
        cluster_name = cluster_name.replace(" ", "-")
        self.k3d_cluster_name = cluster_name

    def _clusters(self) -> List[Dict[str, str]]:
        if len(self._cluster) == 0:
            arguments = ["cluster", "list", "--no-headers"]
            process = self._execute(arguments)
            list_output = process.stdout.read()
            clusters = []
            cluster_list = [item.strip() for item in list_output.split("\n")[:-1]]
            for entry in cluster_list:
                cluster = [item.strip() for item in entry.split(" ") if item != ""]
                # todo handle this output
                if len(cluster) != 4:
                    continue
                clusters.append(
                    {
                        "name": cluster[0],
                        "servers": cluster[1],
                        "agents": cluster[2],
                        "loadbalancer": cluster[3] == "true",
                    }
                )
            self._cluster = clusters
        return self._cluster

    def get_kubeconfig(self, wait=10) -> Optional[str]:
        arguments = ["kubeconfig", "get", self.k3d_cluster_name]
        process = self._execute(arguments)

        if process.returncode != 0:
            logger.error(f"Could not get kubeconfig for {self.k3d_cluster_name}")
        else:
            # we now need to write the kubekonfig to a file
            config = process.stdout.read().strip()
            if not os.path.isdir(
                os.path.join(
                    self.config.CLI_KUBECONFIG_DIRECTORY, self.k3d_cluster_name
                )
            ):
                os.mkdir(
                    os.path.join(
                        self.config.CLI_KUBECONFIG_DIRECTORY, self.k3d_cluster_name
                    )
                )
            config_path = os.path.join(
                self.config.CLI_KUBECONFIG_DIRECTORY,
                self.k3d_cluster_name,
                "kubeconfig.yaml",
            )
            file = open(config_path, "w+")
            file.write(config)
            file.close()
            return config_path

    def exists(self) -> bool:
        for cluster in self._clusters():
            if cluster["name"] == self.k3d_cluster_name:
                return True
        return False

    def create(self):
        import yaml

        arguments = ["cluster", "create", self.k3d_cluster_name]
        logger.info(f"Creating a k3d cluster with name {self.k3d_cluster_name}")
        logger.debug(f"K3d config is:  {str(self.native_config)}")
        if self.native_config:
            try:
                temp = tempfile.NamedTemporaryFile(delete=False)
                logger.debug("K3d config to: " + temp.name)
                content = yaml.dump(self.native_config, default_flow_style=False)
                temp.write(content.encode("utf-8"))
                temp.flush()
                temp.close()
                arguments.extend(["--config", temp.name])
                logger.debug(arguments)
                p = self._execute(
                    arguments,
                    print_output=True if logger.level == logging.DEBUG else False,
                )
                os.remove(temp.name)
                if p.returncode != 0:
                    raise RuntimeError(
                        f"Could not create cluster due to underlying errors with "
                        f"the provider {self.provider_type}. Please run 'deck' with "
                        f"the debug flag to find out what is causing the error"
                    )
            except Exception as e:
                temp.close()
                logger.debug(traceback.print_exc())
                raise e
        return True

    def start(self):
        arguments = ["cluster", "start", self.k3d_cluster_name]
        p = self._execute(arguments)
        if p.returncode != 0:
            return False
        # data.kubeconfig_path = self.get_kubeconfig()
        return True

    def stop(self):
        arguments = ["cluster", "stop", self.k3d_cluster_name]
        self._execute(arguments)
        return True

    def delete(self):
        logger.info(f"Deleting the k3d cluster with name {self.k3d_cluster_name}")
        arguments = ["cluster", "delete", self.k3d_cluster_name]
        self._execute(arguments)
        return True

    def version(self) -> Version:
        process = subprocess.run(
            [self.base_command, "--version"], capture_output=True, text=True
        )
        output = str(process.stdout).strip()
        version_str = re.search(r"(\d+\.\d+\.\d+)", output).group(1)
        return Version(version_str)

    def ready(self) -> bool:
        pass

    def install(self) -> bool:
        try:
            if sys.platform != "win32":
                subprocess.run(
                    "curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash",
                    shell=True,
                    check=True,
                )
            else:
                raise RuntimeError("Cannot automatically install k3d on Windows. Please install " 
                                   "it manually with 'choco install k3d' or follow the "
                                   "documentation: https://k3d.io/stable/#installation")
            return True
        except subprocess.CalledProcessError:
            raise RuntimeError("Could not install k3d")
        except KeyboardInterrupt:
            raise RuntimeError("Could not install k3d")

    def update(self) -> bool:
        return self.install()

    def get_ports(self) -> List[str]:
        try:
            ports = self.native_config["ports"]
            return [port["port"] for port in ports]
        except KeyError:
            return []


class K3dBuilder:
    def __init__(self):
        self._instances = {}

    def __call__(
        self,
        config: ClientConfiguration,
        name=None,
        native_config: dict = None,
        **_ignored,
    ):
        # create instance
        instance = K3d(config=config, name=name, native_config=native_config)

        return instance
