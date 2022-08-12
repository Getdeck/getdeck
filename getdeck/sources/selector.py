from typing import Union, Optional
from getdeck.deckfile.file import (
    DeckfileFileSource,
    DeckfileHelmSource,
    DeckfileKustomizeSource,
)
from getdeck.sources.fetcher import Fetcher
from getdeck.sources.file import FileFetcher
from getdeck.sources.helm import HelmFetcher
from getdeck.sources.kustomize import KustomizeFetcher


def select_fetcher_strategy(
    source: Union[DeckfileFileSource, DeckfileHelmSource, DeckfileKustomizeSource]
) -> Optional[Fetcher]:
    fetcher_strategy = {
        DeckfileFileSource: FileFetcher,
        DeckfileHelmSource: HelmFetcher,
        DeckfileKustomizeSource: KustomizeFetcher,
    }.get(type(source), None)
    return fetcher_strategy
