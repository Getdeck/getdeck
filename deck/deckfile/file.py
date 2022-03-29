from abc import ABC, abstractmethod


class DeckfileNotFoundError(Exception):
    pass


class DeckfileVersionError(Exception):
    pass


class DeckfileError(Exception):
    pass


class Deckfile(ABC):
    @abstractmethod
    def get_cluster(self):
        raise NotImplementedError

    @abstractmethod
    def get_decks(self):
        raise NotImplementedError
