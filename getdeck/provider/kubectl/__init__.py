from typing import List, Optional

from semantic_version import Version

from getdeck.configuration import ClientConfiguration
from getdeck.provider.abstract import AbstractProvider
from getdeck.provider.types import ProviderType


class KubectlCtx(AbstractProvider):
    kubernetes_cluster_type = ProviderType.KUBECTLCTX
    provider_type = "kubectlctx"
    base_command = "kubectl"
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
        instance = KubectlCtx(config=config, name=name, native_config=native_config)
        return instance
