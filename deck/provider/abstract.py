from abc import ABC, abstractmethod

from semantic_version import Version


class IK8sProvider(ABC):
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
    def version(self) -> Version:
        """
        Best return a type that allows working comparisons between versions of the same provider.
        E.g. (1, 10) > (1, 2), but "1.10" < "1.2"
        """
        raise NotImplementedError


class AbstractK8sProvider(IK8sProvider):
    provider_type = None

    def __init__(
        self,
        id: str,
        name: str = None,
    ) -> None:
        self.id = id
        self.name = name

    @property
    def display_name(self):
        name = self.name
        if name:
            return name
        id = self.id
        return id

    @property
    def k8s_provider_type(self):
        return self.provider_type
