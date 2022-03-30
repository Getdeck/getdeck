import logging

from semantic_version import Version

from deck.api import stopwatch
from deck.configuration import default_configuration
from deck.utils import read_deckfile_from_location, ensure_cluster

logger = logging.getLogger("deck")

@stopwatch
def remove_cluster(deckfile_location: str, config=default_configuration) -> bool:
    deckfile = read_deckfile_from_location(deckfile_location, config)
    k8s_provider = ensure_cluster(deckfile, config, do_install=False)
    if k8s_provider.exists():
        k8s_provider.delete()
    else:
        logger.info("Cluster does not exist")
    return True
