import logging
import sys
import subprocess
from typing import List, Dict, Optional

from getdeck.configuration import ClientConfiguration
from getdeck.provider.types import ProviderType
from getdeck.provider.utility_provider import UtilityProvider

logger = logging.getLogger("deck")


class K3d(UtilityProvider):
    kubernetes_cluster_type = ProviderType.K3D
    provider_type = "k3d"
    base_command = "k3d"
    _cluster = []

    def __init__(
        self,
        config: ClientConfiguration,
        name: str,
        native_config: dict,
        _debug_output: bool = False,
    ):
        self.initialize(
            config,
            name,
            native_config,
            self.provider_type,
            self.base_command,
            _debug_output,
        )

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

    def get_kubeconfig(self) -> Optional[str]:
        arguments = ["kubeconfig", "get", self.cluster_name]
        return self._get_kubeconfig(arguments)

    def create(self):
        arguments = ["cluster", "create", self.cluster_name]
        return self._create(arguments)

    def start(self):
        arguments = ["cluster", "start", self.cluster_name]
        p = self._execute(arguments)
        if p.returncode != 0:
            return False
        return True

    def stop(self):
        arguments = ["cluster", "stop", self.cluster_name]
        self._execute(arguments)
        return True

    def delete(self):
        logger.info(f"Deleting the k3d cluster with name {self.cluster_name}")
        arguments = ["cluster", "delete", self.cluster_name]
        self._execute(arguments)
        return True

    def install(self) -> bool:
        try:
            if sys.platform != "win32":
                subprocess.run(
                    "curl -s https://raw.githubusercontent.com/k3d-io/k3d/main/install.sh | bash",
                    shell=True,
                    check=True,
                )
            else:
                raise RuntimeError(
                    "Cannot automatically install k3d on Windows. Please install "
                    "it manually with 'choco install k3d' or follow the "
                    "documentation: https://k3d.io/stable/#installation"
                )
            return True
        except subprocess.CalledProcessError:
            raise RuntimeError("Could not install k3d")
        except KeyboardInterrupt:
            raise RuntimeError("Could not install k3d")


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
        instance = K3d(config=config, name=name, native_config=native_config)
        return instance
