from typing import Any, List, Optional, Union

from pydantic import BaseModel
import os

import shutil


from getdeck import configuration
from getdeck.deckfile.file import (
    DeckfileDirectorySource,
    DeckfileFileSource,
    DeckfileHelmSource,
    DeckfileInlineSource,
    DeckfileKustomizeSource,
)


class TemporaryData(BaseModel):
    data: str
    is_file: bool = False
    is_folder: bool = False


class SourceAux(BaseModel):
    location: Optional[str] = None
    path: Optional[str] = None
    name: Optional[str] = None
    temporary_data: Optional[TemporaryData] = None

    source: Optional[
        Union[
            DeckfileInlineSource,
            DeckfileFileSource,
            DeckfileDirectorySource,
            DeckfileHelmSource,
            DeckfileKustomizeSource,
        ]
    ] = None

    def __del__(self):
        if not self.temporary_data:
            return

        if self.temporary_data.is_file:
            os.remove(self.temporary_data.data)
            return

        if self.temporary_data.is_folder:
            shutil.rmtree(self.temporary_data.data)


class DeckfileAux(BaseModel):
    location: str
    cwd: str = os.getcwd()
    path: Optional[str] = None
    name: str = configuration.DECKFILE_FILE
    temporary_data: Optional[TemporaryData] = None

    def __del__(self):
        if not self.temporary_data:
            return

        if self.temporary_data.is_file:
            os.remove(self.temporary_data.data)
            return

        if self.temporary_data.is_folder:
            shutil.rmtree(self.temporary_data.data)


class DataAux(BaseModel):
    deckfile: Any = None
    deckfile_aux: Optional[DeckfileAux] = None
    source_auxs: List[SourceAux] = None

    def __del__(self):
        if self.deckfile_aux:
            del self.deckfile_aux

        if self.source_auxs:
            del self.source_auxs[:]
