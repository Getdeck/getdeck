import logging
import os
import shutil
from typing import List

from getdeck.api.utils import stopwatch
from getdeck.configuration import default_configuration

logger = logging.getLogger("deck")


@stopwatch
def get_available_decks(deckfile_location: str, config=default_configuration) -> List:
    from getdeck.utils import fetch_data

    deckfile, working_dir_path, is_temp_dir = fetch_data(deckfile_location)
    available_decks = deckfile.get_decks()
    logger.debug(available_decks)

    # TODO: refactor/remove?
    if is_temp_dir and os.path.isdir(working_dir_path):
        shutil.rmtree(working_dir_path)

    return available_decks
