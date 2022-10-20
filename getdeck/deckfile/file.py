import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Union

from pydantic import BaseModel

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.errors import DeckfileError
from getdeck.provider.abstract import AbstractProvider

logger = logging.getLogger("deck")


class DeckfileCluster(BaseModel):
    provider: str
    minVersion: str = None
    name: str
    nativeConfig: dict = None

    def get_provider(self, config: ClientConfiguration) -> AbstractProvider:
        from getdeck.provider.factory import cluster_factory
        from getdeck.provider.types import ProviderType

        # get selected kubernetes cluster from factory
        try:
            cluster = cluster_factory.get(
                ProviderType(self.provider.lower()),
                config,
                name=self.name,
                native_config=self.nativeConfig,
            )
            return cluster
        except Exception as e:
            logger.error(e)
            raise e


class DeckfileHelmSource(BaseModel):
    type: str = "helm"
    ref: str
    targetRevision: str = ""
    namespace: str = ""
    path: str = None
    chart: str = None  # this is set when pulling directly from a Helm repo
    parameters: List[Dict] = None  # Helm value overrides (take precedence)
    releaseName: str
    valueFiles: List[str] = ["values.yaml"]
    helmArgs: List[str] = None
    helmPlugins: List[str] = None


class DeckfileInlineSource(BaseModel):
    type: str = "inline"
    content: Dict = None


class DeckfileFileSource(BaseModel):
    type: str = "file"
    ref: str = None
    targetRevision: str = ""
    path: str = ""


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
    hosts: List[str] = []
    sources: List[
        Union[
            DeckfileInlineSource,
            DeckfileFileSource,
            DeckfileDirectorySource,
            DeckfileHelmSource,
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
                    source_class = {
                        "inline": DeckfileInlineSource,
                        "file": DeckfileFileSource,
                        "directory": DeckfileDirectorySource,
                        "kustomize": DeckfileKustomizeSource,
                        "helm": DeckfileHelmSource,
                    }.get(source["type"].lower())
                    self.sources.append(source_class(**source))
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
    def get_deck(self, name: str = None) -> DeckfileDeck:
        raise NotImplementedError
