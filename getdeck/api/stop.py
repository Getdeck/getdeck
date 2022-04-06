import logging
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
    from getdeck.utils import read_deckfile_from_location, ensure_cluster

    deckfile = read_deckfile_from_location(deckfile_location, config)
    k8s_provider = ensure_cluster(deckfile, config, ignore_cluster, do_install=False)
    logger.info("Stopping cluster")
    k8s_provider.stop()
