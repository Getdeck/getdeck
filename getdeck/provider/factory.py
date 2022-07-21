import logging

from getdeck.configuration import ClientConfiguration
from getdeck.provider.k3d import K3dBuilder
from getdeck.provider.kubectl import KubectlCtxBuilder
from getdeck.provider.kind import KindBuilder
from getdeck.provider.types import ProviderType

logger = logging.getLogger("deck")


class ClusterFactory:
    def __init__(self):
        self._builders = {}

    def register_builder(self, provider_type: ProviderType, builder):
        self._builders[provider_type.value] = builder

    def __create(
        self,
        provider_type: ProviderType,
        config: ClientConfiguration,
        name: str,
        native_config: dict = None,
        **kwargs
    ):
        builder = self._builders.get(provider_type.value)
        if not builder:
            raise ValueError(provider_type)
        return builder(config, name, native_config, **kwargs)

    def get(
        self,
        provider_type: ProviderType,
        config: ClientConfiguration,
        name: str,
        native_config: dict = None,
        **kwargs
    ):
        return self.__create(provider_type, config, name, native_config, **kwargs)


kubernetes_cluster_factory = ClusterFactory()
kubernetes_cluster_factory.register_builder(ProviderType.K3D, K3dBuilder())
kubernetes_cluster_factory.register_builder(ProviderType.KIND, KindBuilder())
kubernetes_cluster_factory.register_builder(
    ProviderType.KUBECTLCTX, KubectlCtxBuilder()
)
