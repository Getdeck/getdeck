import logging
from typing import List, Optional

from semantic_version import Version

from getdeck.configuration import ClientConfiguration
from getdeck.provider.abstract import AbstractK8sProvider
from getdeck.provider.types import K8sProviderType


logger = logging.getLogger("deck")


class KubectlCtx(AbstractK8sProvider):
    kubernetes_cluster_type = K8sProviderType.kubectlctx
    provider_type = "KubectlCtx"
    base_command = "kubectl"
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

    def get_kubeconfig(self, wait=10) -> Optional[str]:
        return None

    def exists(self) -> bool:
        return True

    def create(self):
        pass  # Creating a KubectlCtx is not possible for Deck

    def start(self):
        pass  # Starting a KubectlCtx is not possible for Deck

    def stop(self):
        pass  # Stopping a KubectlCtx is not possible for Deck

    def delete(self):
        pass  # Deleting a KubectlCtx is not possible for Deck

    def version(self) -> Version:
        return None

    def ready(self) -> bool:
        return True

    def install(self) -> bool:
        raise RuntimeError("Installing a KubectlCtx cluster is not possible for Deck")

    def update(self) -> bool:
        raise RuntimeError("Updating a KubectlCtx cluster is not possible for Deck")

    def get_ports(self) -> List[str]:
        return []


class KubectlCtxBuilder:
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
        instance = KubectlCtx(config=config, name=name, native_config=native_config)

        return instance
