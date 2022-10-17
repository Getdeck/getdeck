import logging
import os
import shutil
from typing import List

from getdeck.api.utils import stopwatch
from getdeck.configuration import default_configuration

logger = logging.getLogger("deck")


@stopwatch
def get_available_decks(deckfile_location: str, config=default_configuration) -> List:
    from getdeck.utils import read_deckfile_from_location

    deckfile, working_dir_path, is_temp_dir = read_deckfile_from_location(
        deckfile_location, config
    )
    available_decks = deckfile.get_decks()
    logger.debug(available_decks)

    # TODO: refactor/remove?
    if is_temp_dir and os.path.isdir(working_dir_path):
        shutil.rmtree(working_dir_path)

    return available_decks
