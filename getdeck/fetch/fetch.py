import logging
import os
from typing import List


from getdeck.fetch.deck_fetcher import (
    DeckFetcher,
    DeckfileAux,
    select_deck_fetch_behavior,
)
from getdeck.fetch.types import DataAux
from getdeck.fetch.utils import get_path_and_name
from getdeck.deckfile.file import DeckfileDeck

from getdeck.deckfile.selector import deckfile_selector
from getdeck.fetch.source_fetcher import (
    SourceAux,
    SourceFetcher,
    select_source_fetch_behavior,
)


logger = logging.getLogger("deck")


class FetchError(Exception):
    pass


def _fetch_deck(data_aux: DataAux, location: str) -> DataAux:
    deckfile_aux = DeckfileAux(location=location)
    fetch_behavior = select_deck_fetch_behavior(location=location)
    if fetch_behavior:
        deck_fetcher = DeckFetcher(fetch_behavior=fetch_behavior)
        deckfile_aux = deck_fetcher.fetch(data=deckfile_aux)
    else:
        # local path and name
        path, name = get_path_and_name(location=location)
        deckfile_aux.path = path
        deckfile_aux.name = name

    data_aux.deckfile_aux = deckfile_aux
    return data_aux


def _fetch_sources(deck: DeckfileDeck) -> List[SourceAux]:
    source_fetcher = SourceFetcher(fetch_behavior=None)

    source_auxs = []
    for source in deck.sources:
        ref = getattr(source, "ref", None)
        logger.info(
            "Fetching source " f"{source.__class__.__name__}: {ref or 'no ref'}"
        )

        source_aux = SourceAux(location=ref)
        # assigning source during SourceAux initialization changes DeckfileHelmSource to DeckfileInlineSource.. ???
        source_aux.source = source

        fetch_behavior = select_source_fetch_behavior(source=source)
        source_fetcher.fetch_behavior = fetch_behavior
        if not fetch_behavior:
            source_auxs.append(source_aux)
            continue

        try:
            source_dict = source.dict()
            source_aux = source_fetcher.fetch(data=source_aux, **source_dict)
        except Exception as e:
            logger.debug(str(e))
            del source_aux, source_auxs[:]
            raise FetchError(f"Source fetching error: {str(e)}")

        source_auxs.append(source_aux)  # noqa: F821

    return source_auxs


def fetch_data(
    location: str, deck_name: str = None, fetch_sources: bool = True
) -> DataAux:
    """
    delete returned DataAux to clean up temporary resources
    """

    logger.info(f"Reading Deckfile from: {location}")
    data_aux = DataAux()
    data_aux = _fetch_deck(data_aux=data_aux, location=location)

    # validate
    file = os.path.join(data_aux.deckfile_aux.path, data_aux.deckfile_aux.name)
    if not os.path.isfile(file):
        del data_aux
        raise RuntimeError(f"Cannot identify Deckfile at location: '{location}'")

    deckfile = deckfile_selector.get(file)
    data_aux.deckfile = deckfile

    # parse + fetch sources
    if fetch_sources:
        deck = deckfile.get_deck(deck_name)
        source_auxs = _fetch_sources(deck=deck)
        data_aux.source_auxs = source_auxs

    return data_aux
