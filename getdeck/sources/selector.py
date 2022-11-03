from typing import Union, Optional
from getdeck.deckfile.file import (
    DirectorySource,
    FileSource,
    HelmSource,
    InlineSource,
    KustomizeSource,
)
from getdeck.sources.generator import RenderBehavior
from getdeck.sources.file import File
from getdeck.sources.helm import Helm
from getdeck.sources.inline import Inline
from getdeck.sources.kustomize import Kustomize


def select_render_behavior(
    source: Union[
        InlineSource,
        FileSource,
        DirectorySource,
        HelmSource,
        KustomizeSource,
    ],
) -> Optional[RenderBehavior]:
    render_behavior = {
        InlineSource: Inline,
        FileSource: File,
        DirectorySource: File,
        HelmSource: Helm,
        KustomizeSource: Kustomize,
    }.get(type(source), None)
    return render_behavior
