from deck.provider.k3d import K3dBuilder
from deck.provider.types import K8sProviderType


class K8sClusterFactory:
    def __init__(self):
        self._builders = {}

    def register_builder(self, provider_type: K8sProviderType, builder):
        self._builders[provider_type.value] = builder

    def __create(self, provider_type: K8sProviderType, **kwargs):
        builder = self._builders.get(provider_type.value)
        if not builder:
            raise ValueError(provider_type)
        return builder(**kwargs)

    def get(self, provider_type: K8sProviderType, **kwargs):
        return self.__create(provider_type, **kwargs)


kubernetes_cluster_factory = K8sClusterFactory()
kubernetes_cluster_factory.register_builder(K8sProviderType.k3d, K3dBuilder())
