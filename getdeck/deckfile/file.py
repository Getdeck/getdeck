import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union

from pydantic import BaseModel

from getdeck.deckfile.errors import DeckfileError
from getdeck.provider.abstract import AbstractProvider

logger = logging.getLogger("deck")


class DeckfileCluster(BaseModel):
    provider: str
    minVersion: str = None
    name: str
    nativeConfig: dict = None

    def get_provider(self, config) -> AbstractProvider:
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


class InlineSource(BaseModel):
    type: str = "inline"
    content: Dict = None


class FileSource(BaseModel):
    type: str = "file"
    ref: str = None
    targetRevision: Optional[str] = None
    path: str = ""


class HelmSource(BaseModel):
    type: str = "helm"
    ref: str
    targetRevision: Optional[str] = None
    namespace: str = ""
    path: str = None
    chart: str = None  # this is set when pulling directly from a Helm repo
    parameters: List[Dict] = None  # Helm value overrides (take precedence)
    releaseName: str
    valueFiles: List[str] = ["values.yaml"]
    helmArgs: List[str] = None
    helmPlugins: List[str] = None


class KustomizeSource(BaseModel):
    type: str = "kustomize"
    ref: str
    targetRevision: Optional[str] = None
    path: str = ""


class DirectorySource(BaseModel):
    type: str = "directory"
    ref: str
    targetRevision: Optional[str] = None
    path: str
    recursive: bool


class DeckfileDeck(BaseModel):
    name: str
    namespace: str = "default"
    notes: str = ""
    hosts: List[str] = []
    sources: List[
        Union[
            InlineSource,
            FileSource,
            DirectorySource,
            HelmSource,
            KustomizeSource,
        ]
    ]

    def __init__(self, *args, **data):
        super(DeckfileDeck, self).__init__(*args, **data)
        tsources = data.get("sources")
        self.sources = []
        if tsources:
            try:
                for source in tsources:
                    # inline deprecated warning
                    source_type = source["type"].lower()
                    if source_type == "file" and source.get("content", None):
                        logger.warning(
                            "'type: file' is deprecated for inline sources, "
                            "use 'type: inline' instead",
                        )
                        source_type = "inline"

                    source_class = {
                        "inline": InlineSource,
                        "file": FileSource,
                        "directory": DirectorySource,
                        "kustomize": KustomizeSource,
                        "helm": HelmSource,
                    }.get(source_type)
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
