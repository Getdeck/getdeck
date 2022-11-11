import logging

from getdeck.configuration import ClientConfiguration
from getdeck.fetch.types import DataAux
from getdeck.sources.generator import ResourceGenerator

from getdeck.sources.selector import select_render_behavior
from getdeck.sources.types import GeneratedDeck

logger = logging.getLogger("deck")


def sniff_protocol(ref: str):
    if "#" in ref:
        ref, rev = ref.split("#")
    ref_lo = ref.lower()
    if ref_lo.startswith("git") or ref_lo.endswith(".git"):
        return "git"
    if ref_lo.startswith("https"):
        return "https"
    if ref_lo.startswith("http"):
        return "http"
    if ref_lo[0] in "./~":
        return "local"
    return None


def prepare_k8s_workload_for_deck(
    config: ClientConfiguration,
    data_aux: DataAux,
    deck_name: str,
) -> GeneratedDeck:
    deck = data_aux.deckfile.get_deck(deck_name)
    logger.debug(deck)

    namespace = deck.namespace or "default"
    generated_deck = GeneratedDeck(name=deck.name, namespace=namespace, files=[])

    logger.info(f"Processing {len(deck.sources)} source(s)")
    resource_generator = ResourceGenerator(render_behavior=None)

    for source_aux in data_aux.source_auxs:
        ref = getattr(source_aux.source, "ref", None)
        logger.info(
            "Processing source "
            f"{source_aux.source.__class__.__name__}: {ref or 'no ref'}"
        )

        # update current render behavior
        render_behavior = select_render_behavior(source=source_aux.source)
        if not render_behavior:
            logger.info(
                "Skipping source "
                f"{source_aux.source.__class__.__name__}: {ref or 'no ref'}"
            )
            continue

        # if a source, such as Helm, specifies another namespace
        logger.debug(source_aux.source)
        if hasattr(source_aux.source, "namespace"):
            namespace = source_aux.source.namespace or deck.namespace or "default"
        else:
            namespace = deck.namespace or "default"

        # render source files
        resource_generator.render_behavior = render_behavior(config)
        source_files = resource_generator.render(
            deckfile_aux=data_aux.deckfile_aux,
            source_aux=source_aux,
            namespace=namespace,
        )
        generated_deck.files.extend(source_files)

    return generated_deck
