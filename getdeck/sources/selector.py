from typing import Union, Optional
from getdeck.deckfile.file import (
    DeckfileDirectorySource,
    DeckfileFileSource,
    DeckfileHelmSource,
    DeckfileInlineSource,
    DeckfileKustomizeSource,
)
from getdeck.sources.generator import RenderBehavior
from getdeck.sources.file import File
from getdeck.sources.helm import Helm
from getdeck.sources.inline import Inline
from getdeck.sources.kustomize import Kustomize


def select_render_behavior(
    source: Union[
        DeckfileInlineSource,
        DeckfileFileSource,
        DeckfileDirectorySource,
        DeckfileHelmSource,
        DeckfileKustomizeSource,
    ],
) -> Optional[RenderBehavior]:
    render_behavior = {
        DeckfileInlineSource: Inline,
        DeckfileFileSource: File,
        DeckfileDirectorySource: File,
        DeckfileHelmSource: Helm,
        DeckfileKustomizeSource: Kustomize,
    }.get(type(source), None)
    return render_behavior
