import logging
from typing import List

from deck.api.utils import stopwatch
from deck.configuration import default_configuration
from deck.utils import read_deckfile_from_location

logger = logging.getLogger("deck")


@stopwatch
def get_available_decks(location: str, config=default_configuration) -> List[str]:
    deckfile = read_deckfile_from_location(location, config)
    available_decks = deckfile.get_decks()
    deck_names = [deck.name for deck in available_decks]
    logger.info(deck_names)
    return deck_names

