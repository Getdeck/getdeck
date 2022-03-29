import logging
from typing import List, Optional, Dict, Union, Any, Type

from pydantic import BaseModel

from deck.deckfile.file import Deckfile

logger = logging.getLogger("deck")


class DeckfileCluster(BaseModel):
    provider: str
    name: str
    config: dict = None


class DeckfileHelmSource(BaseModel):
    ref: str
    targetRevision: str
    path: str
    chart: str = None  # this is set when pulling directly from a Helm repo
    parameters: List[Dict]
    releaseName: str  # Helm release name override
    valueFiles: List[str]


class DeckfileDirectorySource(BaseModel):
    ref: str
    targetRevision: str
    path: str
    recursive: bool


class DeckfileDeck(BaseModel):
    name: str
    namespace: str
    sources: List[Union[DeckfileHelmSource, DeckfileDirectorySource]]


class Deckfile_1_0(Deckfile, BaseModel):
    version: Optional[str]
    cluster: DeckfileCluster
    decks: List[DeckfileDeck]

    def get_deck(self, name: str = None) -> DeckfileDeck:
        # default name
        if not name:
            name = "default"

        for deck in self.deck:
            if deck.name == name:
                return deck

        if name != "default":
            raise ValueError("Name of Deck is not part of this Deckfile")

        return self.decks[0]

    def get_cluster(self):
        return self.cluster

    def get_decks(self):
        return self.decks
