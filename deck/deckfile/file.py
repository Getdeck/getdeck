from abc import ABC, abstractmethod
from typing import List, Dict, Union

from pydantic import BaseModel

from deck.configuration import ClientConfiguration
from deck.provider.abstract import AbstractK8sProvider


class DeckfileCluster(BaseModel):
    provider: str
    minVersion: str = None
    name: str
    nativeConfig: dict = None

    def get_provider(self, config: ClientConfiguration) -> AbstractK8sProvider:
        from deck.provider.factory import kubernetes_cluster_factory
        from deck.provider.types import K8sProviderType
        # get selected kubernetes cluster from factory
        try:
            kubernetes_cluster = kubernetes_cluster_factory.get(
                K8sProviderType(self.provider.lower()), config, name=self.name, native_config=self.nativeConfig
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
    releaseName: str = None  # Helm release name override
    valueFiles: List[str] = ["values.yaml"]


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
