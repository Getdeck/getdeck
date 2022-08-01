import logging
from typing import List, Optional

import kubernetes.config

from getdeck.configuration import ClientConfiguration
from beiboot.configuration import ClientConfiguration as BeibootConfiguration
from getdeck.docker import Docker
from getdeck.provider.abstract import AbstractProvider
from getdeck.provider.errors import NotSupportedError
from getdeck.provider.types import ProviderType

from beiboot import api
from semantic_version import Version
from pydantic import BaseModel

logger = logging.getLogger("deck")


NOT_SUPPORTED_ERROR = f"Not supported by {ProviderType.BEIBOOT.value}."
DOCKER_IMAGE = "quay.io/getdeck/tooler:latest"


class PortNativeConfig(BaseModel):
    port: str


class NativeConfigBeiboot(BaseModel):
    context: str
    ports: Optional[List[PortNativeConfig]] = None


class Beiboot(AbstractProvider):
    kubernetes_cluster_type = ProviderType.BEIBOOT
    provider_type = "beiboot"
    base_command = None
    _cluster = []

    def __init__(
        self,
        config: ClientConfiguration,
        name: str,
        native_config: dict,
        _debug_output: bool = False,
    ):
        # abstract kubernetes cluster
        AbstractProvider.__init__(
            self,
            name=name,
        )
        self.config = config
        self.native_config = NativeConfigBeiboot(**native_config)
        self._bbt_conf = BeibootConfiguration()

        # cluster name
        cluster_name = config.CLUSTER_PREFIX + self.name.lower()
        cluster_name = cluster_name.replace(" ", "-")
        self.cluster_name = cluster_name

        # beiboot context
        context_name = self.native_config.context
        try:
            config._init_kubeapi(context=context_name)  # noqa
        except kubernetes.config.ConfigException:
            raise RuntimeError(
                f"You don't have the required kubeconf context. Please get {context_name} to use "
                f"this Deckfile."
            )

    def get_kubeconfig(self) -> str:
        kubeconfig_file = api.get_connection(cluster_name=self.cluster_name)
        return str(kubeconfig_file)

    def create(self) -> bool:
        # ports
        if self.native_config.ports:
            ports = [item.port for item in self.native_config.ports]
        else:
            ports = []

        api.create_cluster(
            cluster_name=self.cluster_name,
            ports=ports,
            connect=True,
        )

        while not Docker().check_running(DOCKER_IMAGE):
            continue

        kubeconfig_location = self.get_kubeconfig()
        logger.info(
            f"You can now set 'export KUBECONFIG={kubeconfig_location}' and work with the cluster."
        )

        return True

    def start(self) -> bool:
        if not Docker().check_running(DOCKER_IMAGE):
            api.establish_connection(cluster_name=self.cluster_name)

            while not Docker().check_running(DOCKER_IMAGE):
                continue

        kubeconfig_location = self.get_kubeconfig()
        logger.info(
            f"You can now set 'export KUBECONFIG={kubeconfig_location}' and work with the cluster."
        )

        return True

    def stop(self) -> bool:
        raise NotSupportedError(NOT_SUPPORTED_ERROR)

    def delete(self) -> bool:
        api.remove_cluster(cluster_name=self.cluster_name)
        return True

    def exists(self) -> bool:
        try:
            _ = api.get_connection(cluster_name=self.cluster_name)
            return True
        except Exception as e:
            logger.debug(e)
            return False

    def ready(self) -> bool:
        raise NotImplementedError

    def install(self) -> bool:
        raise NotSupportedError(NOT_SUPPORTED_ERROR)

    def update(self) -> bool:
        raise NotSupportedError(NOT_SUPPORTED_ERROR)

    def version(self) -> Version:
        import beiboot.configuration

        return Version(beiboot.configuration.__VERSION__)

    def get_ports(self) -> List[str]:
        try:
            ports = [item.port for item in self.native_config.ports]
            return ports
        except KeyError:
            return []


class BeibootBuilder:
    def __init__(self):
        self._instances = {}

    def __call__(
        self,
        config: ClientConfiguration,
        name=None,
        native_config: dict = None,
        **_ignored,
    ):
        instance = Beiboot(config=config, name=name, native_config=native_config)
        return instance
