import logging

from getdeck.fetch.types import DeckfileAux, SourceAux

from getdeck.sources.generator import RenderBehavior
from getdeck.sources.types import K8sSourceFile

logger = logging.getLogger("deck")


class Inline(RenderBehavior):
    def render(self, deckfile_aux: DeckfileAux, source_aux: SourceAux, **kwargs):
        try:
            source_file = K8sSourceFile(
                name="Deckfile",
                content=source_aux.source.content,
                namespace=self.namespace,
            )
            return [source_file]
        except Exception as e:
            logger.error(f"Error processing file: {e}")
            raise e
