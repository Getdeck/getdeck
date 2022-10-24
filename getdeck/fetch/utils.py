import os
from typing import Optional, Tuple

from getdeck import configuration


def get_path_and_name(location: Optional[str]) -> Tuple[str, str]:
    # None
    if location is None:
        location = ""

    # "~"
    if location.startswith("~"):
        location = os.path.expanduser(location)

    # ".", ""
    if location in [".", ""]:
        for extension in [".yaml", ".yml"]:
            location_default = os.path.join(
                os.getcwd(),
                os.path.splitext(configuration.DECKFILE_FILE)[0] + extension,
            )
            if os.path.isfile(location_default):
                location = location_default
                break
        else:
            location = os.path.join(os.getcwd(), configuration.DECKFILE_FILE)

    name = os.path.basename(location)
    dirname = os.path.dirname(location)
    path = os.path.abspath(dirname)

    return path, name
