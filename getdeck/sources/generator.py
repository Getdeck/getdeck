from abc import ABC, abstractmethod
import logging
from typing import List, Union

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.file import (
    DeckfileDirectorySource,
    DeckfileFileSource,
    DeckfileInlineSource,
    DeckfileKustomizeSource,
    DeckfileHelmSource,
)
from getdeck.fetch.types import DeckfileAux, SourceAux
from getdeck.sources.types import K8sSourceFile

logger = logging.getLogger("deck")


class RenderError(Exception):
    pass


class RenderBehavior(ABC):
    def __init__(
        self,
        path: str,
        source: Union[
            DeckfileInlineSource,
            DeckfileFileSource,
            DeckfileDirectorySource,
            DeckfileHelmSource,
            DeckfileKustomizeSource,
        ],
        config: ClientConfiguration,
        namespace: str,
    ):
        self.path = path
        self.source = source
        self.config = config
        self.namespace = namespace

    @property
    def not_supported_message(self):
        return "Could not render source"

    @abstractmethod
    def render(self, **kwargs) -> List[K8sSourceFile]:
        raise NotImplementedError


class ResourceGenerator:
    def __init__(self, render_behavior: RenderBehavior) -> None:
        self._render_behavior = render_behavior

    @property
    def render_behavior(self) -> RenderBehavior:
        return self._render_behavior

    @render_behavior.setter
    def render_behavior(self, render_behavior: RenderBehavior) -> None:
        self._render_behavior = render_behavior

    def render(
        self, deckfile_aux: DeckfileAux, source_aux: SourceAux
    ) -> List[K8sSourceFile]:
        source_files = self._render_behavior.render(
            deckfile_aux=deckfile_aux, source_aux=source_aux
        )
        return source_files
