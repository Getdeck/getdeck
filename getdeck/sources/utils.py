import logging
from typing import Union, List

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.file import (
    DeckfileHelmSource,
    DeckfileDirectorySource,
    Deckfile,
    DeckfileFileSource,
    DeckfileKustomizeSource,
)
from getdeck.sources.file import FileFetcher, Fetcher
from getdeck.sources.helm import HelmFetcher
from getdeck.sources.kustomize import KustomizeFetcher
from getdeck.sources.types import GeneratedDeck, K8sSourceFile

logger = logging.getLogger("deck")


def fetch_deck_source(
    config: ClientConfiguration,
    source: Union[
        DeckfileFileSource,
        DeckfileHelmSource,
        DeckfileDirectorySource,
        DeckfileKustomizeSource,
    ],
    namespace: str = "default",
) -> List[K8sSourceFile]:
    logger.info(
        "Processing source "
        f"{source.__class__.__name__}: {'no ref' if not source.ref else source.ref}"
    )
    if isinstance(source, DeckfileHelmSource):
        fetcher = HelmFetcher(source, config, namespace)
    elif isinstance(source, DeckfileFileSource):
        fetcher = FileFetcher(source, config, namespace)
    elif isinstance(source, DeckfileKustomizeSource):
        fetcher = KustomizeFetcher(source, config, namespace)
    else:
        logger.info(
            "Skipping source "
            f"{source.__class__.__name__}: {'no ref' if not source.ref else source.ref}"
        )
        fetcher = Fetcher(source, config, namespace)
    return fetcher.fetch()


def prepare_k8s_workload_for_deck(
    config: ClientConfiguration, deckfile: Deckfile, deck_name: str
) -> GeneratedDeck:
    deck = deckfile.get_deck(deck_name)
    logger.debug(deck)
    # fetch all sources
    namespace = deck.namespace or "default"
    generated_deck = GeneratedDeck(name=deck.name, namespace=namespace, files=[])
    logger.info(f"Processing {len(deck.sources)} source(s)")
    for source in deck.sources:
        # if a source, such as Helm, specifies another namespace
        logger.debug(source)
        if hasattr(source, "namespace"):
            namespace = source.namespace or deck.namespace or "default"
        else:
            namespace = deck.namespace or "default"
        generated_deck.files.extend(fetch_deck_source(config, source, namespace))
    return generated_deck
