import logging
from typing import Union, List

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.file import DeckfileHelmSource, DeckfileDirectorySource, Deckfile, DeckfileFileSource
from getdeck.sources.file import generate_file_source
from getdeck.sources.helm import generate_helm_source
from getdeck.sources.types import GeneratedDeck, K8sSourceFile

logger = logging.getLogger("deck")


def fetch_deck_source(
    config: ClientConfiguration,
    source: Union[DeckfileFileSource, DeckfileHelmSource, DeckfileDirectorySource],
    namespace: str = "default",
) -> List[K8sSourceFile]:
    logger.info(f"Processing source {source.__class__.__name__}: {'no ref' if not getattr(source, 'ref') else getattr(source, 'ref')}")
    if type(source) == DeckfileHelmSource:
        return generate_helm_source(config, source, namespace)
    if type(source) == DeckfileFileSource:
        return generate_file_source(config, source, namespace)

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
        generated_deck.files.extend(fetch_deck_source(config, source, namespace))
    return generated_deck
