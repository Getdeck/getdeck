import logging
from typing import Union, List

from deck.configuration import ClientConfiguration
from deck.deckfile.file import DeckfileHelmSource, DeckfileDirectorySource, Deckfile
from deck.sources.helm import generate_helm_source
from deck.sources.types import GeneratedDeck, K8sSourceFile

logger = logging.getLogger("deck")


def fetch_deck_source(
    config: ClientConfiguration,
    source: Union[DeckfileHelmSource, DeckfileDirectorySource],
    namespace: str = "default",
) -> List[K8sSourceFile]:
    if isinstance(source, DeckfileHelmSource):
        return generate_helm_source(config, source, namespace)


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
        logger.info(f"Processing source {source.ref}")
        generated_deck.files.extend(fetch_deck_source(config, source, namespace))
    return generated_deck
