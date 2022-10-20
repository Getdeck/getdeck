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
    location: str = None
    path: str = None
    name: str = None
    temporary_data: Optional[TemporaryData] = None

    source: Union[
        DeckfileInlineSource,
        DeckfileFileSource,
        DeckfileDirectorySource,
        DeckfileHelmSource,
        DeckfileKustomizeSource,
    ] = None

    def __del__(self):
        if not self.temporary_data:
            return

        if self.temporary_data.is_file:
            os.remove(self.temporary_data.data)
            return

        if self.temporary_data.is_folder:
            shutil.rmtree(self.temporary_data.data)
            return


class DeckfileAux(BaseModel):
    argument_location: str  # TODO: rename
    cwd: str = os.getcwd()
    path: str = None
    name: str = configuration.DECKFILE_FILE
    working_dir_path: str = None
    temporary_data: Optional[TemporaryData] = None

    def __del__(self):
        if not self.temporary_data:
            return

        if self.temporary_data.is_file:
            os.remove(self.temporary_data.data)
            return

        if self.temporary_data.is_folder:
            shutil.rmtree(self.temporary_data.data)
            return


class DataAux(BaseModel):
    deckfile: Any = None  # TODO: typing?
    deckfile_aux: DeckfileAux = None
    source_auxs: List[SourceAux] = []

    def __del__(self):
        del self.deckfile_aux
        del self.source_auxs[:]
