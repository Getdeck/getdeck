import logging
from typing import List

from getdeck.cli.utils import stopwatch
from getdeck.fetch.fetch import fetch_data

logger = logging.getLogger("deck")


@stopwatch
def get_available_decks(deckfile_location: str) -> List:
    data_aux = fetch_data(deckfile_location, fetch_sources_flag=False)
    available_decks = data_aux.deckfile.get_decks()
    del data_aux

    logger.debug(available_decks)
    return available_decks


def list_command(args):
    decks = get_available_decks(args.Deckfile)
    names = [deck.name for deck in decks]
    logger.info(names)
