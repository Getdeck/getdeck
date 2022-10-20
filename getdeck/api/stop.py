import logging
import os
import shutil
from typing import Callable

from getdeck.api import stopwatch
from getdeck.configuration import default_configuration

logger = logging.getLogger("deck")


@stopwatch
def stop_cluster(
    deckfile_location: str,
    ignore_cluster: bool = False,
    config=default_configuration,
    progress_callback: Callable = None,
) -> bool:
    from getdeck.utils import fetch_data, ensure_cluster

    deckfile, working_dir_path, is_temp_dir = fetch_data(deckfile_location)
    k8s_provider = ensure_cluster(deckfile, config, ignore_cluster, do_install=False)
    logger.info("Stopping cluster")

    # TODO: refactor/remove?
    if is_temp_dir and os.path.isdir(working_dir_path):
        shutil.rmtree(working_dir_path)

    k8s_provider.stop()
