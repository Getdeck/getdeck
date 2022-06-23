import logging
import os
import re
import subprocess
import tempfile
import traceback
from typing import List, Optional

from semantic_version import Version

from getdeck.configuration import ClientConfiguration
from getdeck.provider.abstract import AbstractK8sProvider
from getdeck.provider.types import K8sProviderType
from getdeck.utils import CMDWrapper

logger = logging.getLogger("deck")


class UtilityProvider(AbstractK8sProvider, CMDWrapper):
    kubernetes_cluster_type = K8sProviderType.k3d
    _cluster = []

    def initialize(
        self,
        config: ClientConfiguration,
        name: str,
        native_config: dict,
        provider_type: str,
        base_command: str,
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
        self.provider_type = provider_type
        self.base_command = base_command

        # cluster name
        cluster_name = config.K3D_CLUSTER_PREFIX + self.name.lower()
        cluster_name = cluster_name.replace(" ", "-")
        self.k3d_cluster_name = cluster_name

    def _get_kubeconfig(self, arguments, wait=10) -> Optional[str]:
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

    def _create(self, arguments):
        import yaml

        logger.info(
            f"Creating a {self.provider_type} cluster with name {self.k3d_cluster_name}"
        )
        logger.debug(
            f"{self.provider_type.capitalize()} config is:  {str(self.native_config)}"
        )
        if self.native_config:
            try:
                temp = tempfile.NamedTemporaryFile(delete=False)
                logger.debug(
                    f"{self.provider_type.capitalize()} config to: {temp.name}"
                )
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
                logger.debug(traceback.format_exc())
                raise e
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

    def update(self) -> bool:
        return self.install()

    def get_ports(self) -> List[str]:
        try:
            ports = self.native_config["ports"]
            return [port["port"] for port in ports]
        except KeyError:
            return []
