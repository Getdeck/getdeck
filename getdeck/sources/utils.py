import logging

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.file import Deckfile
from getdeck.sources.fetcher import FetcherContext

from getdeck.sources.selector import select_fetcher_strategy
from getdeck.sources.types import GeneratedDeck

logger = logging.getLogger("deck")


def prepare_k8s_workload_for_deck(
    config: ClientConfiguration, deckfile: Deckfile, deck_name: str
) -> GeneratedDeck:
    deck = deckfile.get_deck(deck_name)
    logger.debug(deck)

    # fetch all sources
    namespace = deck.namespace or "default"
    generated_deck = GeneratedDeck(name=deck.name, namespace=namespace, files=[])

    logger.info(f"Processing {len(deck.sources)} source(s)")
    fetcher_context = FetcherContext(strategy=None)

    for source in deck.sources:
        logger.info(
            "Processing source "
            f"{source.__class__.__name__}: {'no ref' if not source.ref else source.ref}"
        )

        # update current fetcher strategy
        strategy = select_fetcher_strategy(source=source)
        if not strategy:
            logger.info(
                "Skipping source "
                f"{source.__class__.__name__}: {'no ref' if not source.ref else source.ref}"
            )
            continue

        fetcher_context.strategy = strategy(
            deckfile.file_path, source, config, namespace
        )

        # if a source, such as Helm, specifies another namespace
        logger.debug(source)
        if hasattr(source, "namespace"):
            namespace = source.namespace or deck.namespace or "default"
        else:
            namespace = deck.namespace or "default"

        # fetch source files
        source_files = fetcher_context.fetch_source_files()
        generated_deck.files.extend(source_files)

    return generated_deck
