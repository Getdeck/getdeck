import logging

from getdeck.fetch.types import DeckfileAux, SourceAux

from getdeck.sources.generator import RenderBehavior, RenderError
from getdeck.sources.types import K8sSourceFile

logger = logging.getLogger("deck")


class Inline(RenderBehavior):
    def render(self, deckfile_aux: DeckfileAux, source_aux: SourceAux):
        try:
            # optional arguments
            arguments = {}
            if self.namespace:
                arguments["namespace"] = self.namespace

            source_file = K8sSourceFile(
                name="Deckfile",
                content=source_aux.source.content,
                **arguments,
            )
            return [source_file]
        except Exception as e:
            logger.error(f"Processing inline source failed: {deckfile_aux.location}")
            logger.debug(e)
            raise RenderError(str(e))
