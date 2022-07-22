import logging
from typing import List

from getdeck.configuration import ClientConfiguration
from getdeck.provider.abstract import AbstractProvider
from getdeck.provider.types import ProviderType

from kubernetes.config import kube_config
from beiboot import api
from semantic_version import Version

logger = logging.getLogger("deck")


class NotSupportedError(Exception):
    pass


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
        self.native_config = native_config

    def get_kubeconfig(self) -> bool:
        name = "test"
        _, active_context = kube_config.list_kube_config_contexts()

        if active_context.name == name:
            return active_context

        # select config

    def create(self) -> bool:
        api.create_cluster()

    def start(self) -> bool:
        raise NotSupportedError("Not supported by beiboot.")

    def stop(self) -> bool:
        raise NotSupportedError("Not supported by beiboot.")

    def delete(self) -> bool:
        api.delete_cluster()

    def exists(self) -> bool:
        raise NotImplementedError

    def ready(self) -> bool:
        raise NotImplementedError

    def install(self) -> bool:
        raise NotSupportedError

    def update(self) -> bool:
        raise NotSupportedError

    def version(self) -> Version:
        raise NotSupportedError("Not implemented in beiboot client.")

    def get_ports(self) -> List[str]:
        """
        Return the published ports
        """
        raise NotImplementedError


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
