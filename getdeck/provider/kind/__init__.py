import sys
import subprocess
from typing import List, Dict, Optional

from getdeck.configuration import ClientConfiguration
from getdeck.provider.types import ProviderType
from getdeck.provider.utility_provider import UtilityProvider
import platform


class Kind(UtilityProvider):
    kubernetes_cluster_type = ProviderType.KIND
    provider_type = "kind"
    base_command = "kind"
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
            arguments = ["get", "clusters"]
            process = self._execute(arguments)
            list_output = process.stdout.read()
            clusters = []
            cluster_list = [item.strip() for item in list_output.split("\n")[:-1]]
            for entry in cluster_list:
                arguments = ["get", "nodes", "--name", entry]
                another_process = self._execute(arguments)
                output = another_process.stdout.read()
                cluster = [item.strip() for item in output.split("\n") if item != ""]
                if len(cluster) != 2:
                    continue
                clusters.append(
                    {
                        "name": entry,
                        "servers": cluster[1],
                        "agents": cluster[0],
                    }
                )
            self._cluster = clusters
        return self._cluster

    def get_kubeconfig(self) -> Optional[str]:
        arguments = ["get", "kubeconfig", "--name", self.cluster_name]
        return self._get_kubeconfig(arguments)

    def create(self):
        arguments = ["create", "cluster", "--name", self.cluster_name]
        return self._create(arguments)

    def start(self):
        base_command = "docker"
        clusters = self._clusters()
        for cluster in clusters:
            if cluster["name"] == self.cluster_name:
                arguments_servers = ["start", cluster["servers"]]
                arguments_agents = ["start", cluster["agents"]]
                p1 = self._execute(arguments_servers, base_command=base_command)
                p2 = self._execute(arguments_agents, base_command=base_command)
                if p1.returncode != 0 or p2.returncode != 0:
                    return False
        return True

    def stop(self):
        base_command = "docker"
        clusters = self._clusters()
        for cluster in clusters:
            if cluster["name"] == self.cluster_name:
                arguments_servers = ["stop", cluster["servers"]]
                arguments_agents = ["stop", cluster["agents"]]
                self._execute(arguments_servers, base_command=base_command)
                self._execute(arguments_agents, base_command=base_command)
        return True

    def delete(self):
        arguments = ["delete", "cluster", "--name", self.cluster_name]
        self._execute(arguments)
        return True

    def install(self) -> bool:
        try:
            current_platform = platform.uname()
            if sys.platform == "darwin":
                if current_platform.machine == "arm64":
                    subprocess.run(
                        "[ $(uname -m) = arm64 ] && "
                        "curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.14.0/kind-darwin-arm64;"
                        "chmod +x ./kind;"
                        "sudo mv ./kind /usr/local/bin/kind",
                        shell=True,
                        check=True,
                    )
                elif current_platform.machine == "x86_64":
                    subprocess.run(
                        "[ $(uname -m) = x86_64 ] && "
                        "curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.14.0/kind-darwin-amd64",
                        shell=True,
                        check=True,
                    )
            elif sys.platform == "linux":
                subprocess.run(
                    "curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.14.0/kind-linux-amd64;chmod +x ./kind;"
                    "sudo mv ./kind /usr/local/bin/kind",
                    shell=True,
                    check=True,
                )
            elif sys.platform == "win32":
                subprocess.run(
                    "curl.exe -Lo kind-windows-amd64.exe https://kind.sigs.k8s.io/dl/v0.14.0/kind-windows-amd64;"
                    "Move-Item .\\kind-windows-amd64.exe c:\\Desktop\\kind.exe",
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
            raise RuntimeError("Could not install kind")
        except KeyboardInterrupt:
            raise RuntimeError("Could not install kind")


class KindBuilder:
    def __init__(self):
        self._instances = {}

    def __call__(
        self,
        config: ClientConfiguration,
        name=None,
        native_config: dict = None,
        **_ignored,
    ):
        instance = Kind(config=config, name=name, native_config=native_config)
        return instance
