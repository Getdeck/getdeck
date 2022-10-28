import os
from typing import Optional, Tuple

from getdeck import configuration


def detect_deckfile() -> Optional[str]:
    for extension in [".yaml", ".yml"]:
        name = os.path.splitext(configuration.DECKFILE_FILE)[0] + extension
        location = os.path.join(os.getcwd(), name)
        if os.path.isfile(location):
            return name
    else:
        return None


def get_path_and_name(location: Optional[str]) -> Tuple[str, str]:
    # None
    if location is None:
        location = ""

    # "~"
    if location.startswith("~"):
        location = os.path.expanduser(location)

    # ".", ""
    if location in [".", ""]:
        name = detect_deckfile()
        if not name:
            name = configuration.DECKFILE_FILE
        location = os.path.join(os.getcwd(), name)

    name = os.path.basename(location)
    dirname = os.path.dirname(location)
    path = os.path.abspath(dirname)

    return path, name
