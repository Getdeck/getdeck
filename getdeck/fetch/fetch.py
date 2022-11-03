import logging
import os
from typing import List, Union


from getdeck.fetch.deck_fetcher import (
    DeckFetcher,
    DeckfileAux,
    select_deck_fetch_behavior,
)
from getdeck.fetch.types import DataAux
from getdeck.fetch.utils import detect_deckfile, get_path_and_name
from getdeck.deckfile.file import (
    DeckfileDeck,
    DirectorySource,
    FileSource,
    HelmSource,
    InlineSource,
    KustomizeSource,
)

from getdeck.deckfile.selector import deckfile_selector
from getdeck.fetch.source_fetcher import (
    SourceAux,
    SourceFetcher,
    select_source_fetch_behavior,
)


logger = logging.getLogger("deck")


class FetchError(Exception):
    pass


def fetch_deck(data_aux: DataAux, location: str) -> DataAux:
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


def fetch_source(
    source: Union[
        InlineSource,
        FileSource,
        DirectorySource,
        HelmSource,
        KustomizeSource,
    ],
    source_fetcher: SourceFetcher = None,
) -> SourceAux:
    ref = getattr(source, "ref", None)
    source_aux = SourceAux(location=ref)
    source_aux.source = source  # does not work during SourceAux initialization

    fetch_behavior = select_source_fetch_behavior(source=source)
    if not fetch_behavior:
        return source_aux

    if not source_fetcher:
        source_fetcher = SourceFetcher(fetch_behavior=fetch_behavior)
    else:
        source_fetcher.fetch_behavior = fetch_behavior

    try:
        source_dict = source.dict()
        source_aux = source_fetcher.fetch(data=source_aux, **source_dict)
    except Exception as e:
        logger.debug(str(e))
        del source_aux
        raise FetchError(f"Source fetching error: {str(e)}")

    return source_aux  # noqa: F821


def fetch_all_sources(deck: DeckfileDeck) -> List[SourceAux]:
    source_fetcher = SourceFetcher(fetch_behavior=None)

    source_auxs = []
    for source in deck.sources:
        ref = getattr(source, "ref", None)
        logger.info(f"Fetching {source.__class__.__name__}: {ref or '-'}")
        source_aux = fetch_source(source=source, source_fetcher=source_fetcher)
        source_auxs.append(source_aux)

    return source_auxs


def fetch_data(
    location: str, deck_name: str = None, fetch_sources_flag: bool = True
) -> DataAux:
    """
    delete returned DataAux to clean up temporary resources
    """

    # info
    display_location = location
    if display_location == ".":
        display_location = detect_deckfile()

    logger.info(f"Reading Deckfile: {display_location}")

    # fetch deck
    data_aux = DataAux()
    data_aux = fetch_deck(data_aux=data_aux, location=location)

    # validate
    file_detected = os.path.join(data_aux.deckfile_aux.path, data_aux.deckfile_aux.name)
    if not os.path.isfile(file_detected):
        logger.debug(f"Absolute file location: {file_detected}")
        del data_aux
        raise RuntimeError(f"Cannot identify Deckfile at location: {display_location}")

    deckfile = deckfile_selector.get(file_detected)
    data_aux.deckfile = deckfile

    # fetch sources
    if not fetch_sources_flag:
        return data_aux

    deck = deckfile.get_deck(deck_name)
    source_auxs = fetch_all_sources(deck=deck)
    data_aux.source_auxs = source_auxs

    return data_aux
