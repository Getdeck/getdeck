import logging
import os
from typing import Union

import yaml

from deck import configuration
from deck.deckfile.file import Deckfile
from deck.deckfile.deckfile_1 import Deckfile_1_0

logger = logging.getLogger("deck")


class DeckfileSelector:
    def __init__(self, options: dict):
        self.options = options

    def get(self, path_deckfile: str = None) -> Union[Deckfile, Deckfile_1_0, None]:
        # default file path
        if not path_deckfile:
            path_deckfile = os.path.join(os.getcwd(), configuration.DECKFILE_FILE)

        # load deck file + get version
        try:
            logger.debug(f"Trying to open file at {path_deckfile}")
            with open(path_deckfile) as deckfile:
                data = yaml.load(deckfile, Loader=yaml.FullLoader)
        except FileNotFoundError:
            raise DeckfileNotFoundError(
                f"The Deckfile at the location {path_deckfile} does not exist."
            )

        # version
        version = str(data.get("version", "latest"))
        data["version"] = version

        # get class
        deckfile_class = self.options.get(version)
        if not deckfile_class:
            raise DeckfileVersionError
        logger.debug("The raw Deckfile data: " + str(data))
        return deckfile_class(**data)


deckfile_selector = DeckfileSelector(
    options={
        "latest": Deckfile_1_0,
        "1": Deckfile_1_0,
        "1.0": Deckfile_1_0,
    }
)
