import logging
import os
import re
import subprocess
from time import sleep
from typing import List, Dict, Optional

from semantic_version import Version

from deck.configuration import ClientConfiguration
from deck.provider.abstract import AbstractK8sProvider
from deck.provider.types import K8sProviderType
from deck.utils import CMDWrapper

logger = logging.getLogger("deck")


class K3d(AbstractK8sProvider, CMDWrapper):
    kubernetes_cluster_type = K8sProviderType.k3d

    base_command = "k3d"
    _cluster = []

    def __init__(
        self,
        config: ClientConfiguration,
        id,
        name: str = None,
        _debug_output=False,
    ):

        # abstract kubernetes cluster
        AbstractK8sProvider.__init__(
            self,
            id=id,
            name=name,
        )
        self.config = config
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
        # this is a nasty busy wait, but we don't have another chance
        for i in range(1, wait):
            process = self._execute(arguments)
            if process.returncode == 0:
                break
            else:
                logger.info(f"Waiting for the cluster to be ready ({i}/{wait}).")
                sleep(2)

        if process.returncode != 0:
            logger.error(
                "Something went completely wrong with the cluster spin up (or we got a timeout)."
            )
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

    @staticmethod
    def _get_random_unused_port() -> int:
        import socket

        tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp.bind(("", 0))
        addr, port = tcp.getsockname()
        tcp.close()
        return port

    def exists(self) -> bool:
        for cluster in self._clusters():
            if cluster["name"] == self.k3d_cluster_name:
                return True
        return False

    def create(self):
        # todo
        arguments = []
        self._execute(arguments)
        return True

    def start(self):
        arguments = ["cluster", "start", self.k3d_cluster_name]
        p = self._execute(arguments)
        if p.returncode != 0:
            return False
        data = self.storage.get()
        data.kubeconfig_path = self.get_kubeconfig()
        self.storage.set(data)
        return True

    def stop(self):
        arguments = ["cluster", "stop", self.k3d_cluster_name]
        self._execute(arguments)
        return True

    def delete(self):
        arguments = ["cluster", "delete", self.k3d_cluster_name]
        self._execute(arguments)
        self.storage.delete()
        return True

    def version(self) -> Version:
        process = subprocess.run(
            [self.base_command, "--version"], capture_output=True, text=True
        )
        output = str(process.stdout).strip()
        version_str = re.search(r"(\d+\.\d+\.\d+)", output).group(1)
        return Version(version_str)


class K3dBuilder:
    def __init__(self):
        self._instances = {}

    def __call__(
        self,
        config: ClientConfiguration,
        id,
        name=None,
        **_ignored,
    ):
        # get instance from cache
        instance = self._instances.get(id, None)
        if instance:
            return instance

        # create instance
        instance = K3d(
            config=config,
            id=id,
            name=name,
        )
        self._instances[id] = instance

        return instance
