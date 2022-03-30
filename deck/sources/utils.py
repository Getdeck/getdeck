import logging
from typing import Union, List

from deck.configuration import ClientConfiguration
from deck.deckfile.file import DeckfileHelmSource, DeckfileDirectorySource, Deckfile
from deck.sources.helm import generate_helm_source
from deck.sources.types import GeneratedDeck, K8sSourceFile

logger = logging.getLogger("deck")


def fetch_deck_source(config: ClientConfiguration,
                      source: Union[DeckfileHelmSource, DeckfileDirectorySource],
                      namespace: str = "default") -> List[K8sSourceFile]:
    if isinstance(source, DeckfileHelmSource):
        return generate_helm_source(config, source, namespace)


def prepare_k8s_workload_for_deck(config: ClientConfiguration, deckfile: Deckfile, deck_name: str) -> GeneratedDeck:
    deck = deckfile.get_deck(deck_name)
    logger.debug(deck)
    # fetch all sources
    generated_deck = GeneratedDeck(files=[])
    namespace = deck.namespace or "default"
    for source in deck.sources:
        generated_deck.files.extend(fetch_deck_source(config, source, namespace))
    return generated_deck
