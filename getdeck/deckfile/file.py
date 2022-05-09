import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Union

from pydantic import BaseModel

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.errors import DeckfileError
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
    type: str = "helm"
    ref: str
    targetRevision: str = ""
    path: str = None
    chart: str = None  # this is set when pulling directly from a Helm repo
    parameters: List[Dict] = None  # Helm value overrides (take precedence)
    releaseName: str
    valueFiles: List[str] = ["values.yaml"]
    helmArgs: List[str] = None
    helmPlugins: List[str] = None


class DeckfileFileSource(BaseModel):
    type: str = "file"
    ref: str = None
    content: Dict = None


class DeckfileKustomizeSource(BaseModel):
    type: str = "kustomize"
    ref: str
    targetRevision: str = ""
    path: str = ""


class DeckfileDirectorySource(BaseModel):
    type: str = "directory"
    ref: str
    targetRevision: str = ""
    path: str
    recursive: bool


class DeckfileDeck(BaseModel):
    name: str
    namespace: str = "default"
    notes: str = ""
    sources: List[
        Union[
            DeckfileHelmSource,
            DeckfileDirectorySource,
            DeckfileFileSource,
            DeckfileKustomizeSource,
        ]
    ]

    def __init__(self, *args, **data):
        super(DeckfileDeck, self).__init__(*args, **data)
        tsources = data.get("sources")
        self.sources = []
        if tsources:
            try:
                for source in tsources:
                    if source["type"].lower() == "helm":
                        self.sources.append(DeckfileHelmSource(**source))
                    elif source["type"].lower() == "file":
                        self.sources.append(DeckfileFileSource(**source))
                    elif source["type"].lower() == "directory":
                        self.sources.append(DeckfileDirectorySource(**source))
                    elif source["type"].lower() == "kustomize":
                        self.sources.append(DeckfileKustomizeSource(**source))
            except KeyError:
                raise DeckfileError(
                    f"A source from Deck {data.get('name')} did not specify the 'type' argument."
                )


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
