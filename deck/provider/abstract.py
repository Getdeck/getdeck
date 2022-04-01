from abc import ABC, abstractmethod
from typing import List

from semantic_version import Version


class IK8sProvider(ABC):
    @abstractmethod
    def get_kubeconfig(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def create(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def start(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def stop(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def delete(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def exists(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def ready(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def install(self) -> bool:
        """
        Install this K8s provider on the local system
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def update(self) -> bool:
        """
        Update this K8s provider on the local system
        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def version(self) -> Version:
        """
        Best return a type that allows working comparisons between versions of the same provider.
        E.g. (1, 10) > (1, 2), but "1.10" < "1.2"
        """
        raise NotImplementedError

    @abstractmethod
    def get_ports(self) -> List[str]:
        """
        Return the published ports
        """
        raise NotImplementedError


class AbstractK8sProvider(IK8sProvider):
    provider_type = None

    def __init__(
        self,
        name: str = None,
    ) -> None:
        self.name = name

    @property
    def display_name(self):
        name = self.name
        if name:
            return name
        return name

    @property
    def k8s_provider_type(self):
        return self.provider_type
