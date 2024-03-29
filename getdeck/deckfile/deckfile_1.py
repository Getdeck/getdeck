import logging
from typing import List, Optional

from pydantic import BaseModel

from getdeck.deckfile.file import Deckfile, DeckfileCluster, DeckfileDeck

logger = logging.getLogger("deck")


class Deckfile_1_0(Deckfile, BaseModel):
    # meta
    file_path: str
    file_name: str

    # content
    version: Optional[str]
    cluster: DeckfileCluster = None
    decks: List[DeckfileDeck]

    def get_deck(self, name: str = None) -> DeckfileDeck:
        if name is None and len(self.decks) >= 1:
            for deck in self.decks:
                if deck.name.lower() == "default":
                    return deck
            return self.decks[0]
        else:
            for deck in self.decks:
                if deck.name.lower() == name.lower():
                    return deck
            else:
                raise ValueError(
                    f"Name of Deck {name.lower()} is not part of this Deckfile or is missing"
                )

    def get_cluster(self):
        return self.cluster

    def get_decks(self):
        return self.decks
