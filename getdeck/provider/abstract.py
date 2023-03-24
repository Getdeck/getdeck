from abc import ABC, abstractmethod
from typing import List

from semantic_version import Version

import logging

logger = logging.getLogger("deck")


class AbstractProvider(ABC):
    provider_type = None
    kubernetes_cluster_type = None

    def __init__(
        self,
        name: str = None,
    ) -> None:
        self.name = name
        self.config = None

    @property
    def display_name(self):
        name = self.name
        if name:
            return name
        return name

    def get_config(self):
        return self.config

    def start_or_create(self) -> bool:
        if self.exists():
            self.start()
            created = False
        else:
            self.create()
            created = True
        return created

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

    def create_namespace(self, name: str) -> None:
        from kubernetes.client.rest import ApiException
        from kubernetes.client import V1Namespace, V1ObjectMeta

        logger.debug(f"Creating namespace {name}")
        try:
            self.config.K8S_CORE_API.create_namespace(
                body=V1Namespace(metadata=V1ObjectMeta(name=name))
            )
        except ApiException as e:
            if e.status == 409:
                # namespace does already exist
                pass
            else:
                raise e
