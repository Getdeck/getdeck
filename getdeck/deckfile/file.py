import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Union

from pydantic import BaseModel

from getdeck.configuration import ClientConfiguration
from getdeck.provider.abstract import AbstractK8sProvider

logger = logging.getLogger("deck")


class DeckfileCluster(BaseModel):
    provider: str
    minVersion: str = None
    name: str
    nativeConfig: dict = None

    def get_provider(self, config: ClientConfiguration) -> AbstractK8sProvider:
        from getdeck.provider.factory import kubernetes_cluster_factory
        from getdeck.provider.types import K8sProviderType

        # get selected kubernetes cluster from factory
        try:
            kubernetes_cluster = kubernetes_cluster_factory.get(
                K8sProviderType(self.provider.lower()),
                config,
                name=self.name,
                native_config=self.nativeConfig,
            )
            return kubernetes_cluster
        except Exception as e:
            logger.error(e)
            raise e


class DeckfileHelmSource(BaseModel):
    ref: str
    targetRevision: str = None
    path: str = None
    chart: str = None  # this is set when pulling directly from a Helm repo
    parameters: List[Dict] = None  # Helm value overrides (take precedence)
    releaseName: str
    valueFiles: List[str] = ["values.yaml"]
    helmArgs: List[str] = None


class DeckfileDirectorySource(BaseModel):
    ref: str
    targetRevision: str
    path: str
    recursive: bool


class DeckfileDeck(BaseModel):
    name: str
    namespace: str
    sources: List[Union[DeckfileHelmSource, DeckfileDirectorySource]]


class Deckfile(ABC):
    @abstractmethod
    def get_cluster(self) -> DeckfileCluster:
        raise NotImplementedError

    @abstractmethod
    def get_decks(self) -> List[DeckfileDeck]:
        raise NotImplementedError

    @abstractmethod
    def get_deck(self) -> DeckfileDeck:
        raise NotImplementedError
