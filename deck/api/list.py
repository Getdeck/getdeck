import logging
from typing import List

from deck.api.utils import stopwatch
from deck.configuration import default_configuration
from deck.utils import read_deckfile_from_location

logger = logging.getLogger("deck")


@stopwatch
def get_available_decks(deckfile_location: str, config=default_configuration) -> List:
    deckfile = read_deckfile_from_location(deckfile_location, config)
    available_decks = deckfile.get_decks()
    logger.debug(available_decks)
    return available_decks
