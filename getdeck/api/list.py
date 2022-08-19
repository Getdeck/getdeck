import logging
from typing import List

from getdeck.api.utils import stopwatch
from getdeck.configuration import default_configuration

logger = logging.getLogger("deck")


@stopwatch
def get_available_decks(deckfile_location: str, config=default_configuration) -> List:
    from getdeck.utils import read_deckfile_from_location

    deckfile, _ = read_deckfile_from_location(deckfile_location, config)
    available_decks = deckfile.get_decks()
    logger.debug(available_decks)
    return available_decks
