import logging

from deck.configuration import ClientConfiguration
from deck.provider.k3d import K3dBuilder
from deck.provider.kubectl import KubectlCtxBuilder
from deck.provider.types import K8sProviderType

logger = logging.getLogger("deck")


class K8sClusterFactory:
    def __init__(self):
        self._builders = {}

    def register_builder(self, provider_type: K8sProviderType, builder):
        self._builders[provider_type.value] = builder

    def __create(
        self,
        provider_type: K8sProviderType,
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
        provider_type: K8sProviderType,
        config: ClientConfiguration,
        name: str,
        native_config: dict = None,
        **kwargs
    ):
        return self.__create(provider_type, config, name, native_config, **kwargs)


kubernetes_cluster_factory = K8sClusterFactory()
kubernetes_cluster_factory.register_builder(K8sProviderType.k3d, K3dBuilder())
kubernetes_cluster_factory.register_builder(
    K8sProviderType.kubectlctx, KubectlCtxBuilder()
)
