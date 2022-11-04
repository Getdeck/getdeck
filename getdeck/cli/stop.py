import logging

from getdeck.cli import stopwatch
from getdeck.configuration import default_configuration
from getdeck.fetch.fetch import fetch_data

logger = logging.getLogger("deck")


@stopwatch
def stop_cluster(
    deckfile_location: str,
    ignore_cluster: bool = False,
    config=default_configuration,
) -> bool:
    from getdeck.utils import ensure_cluster

    data_aux = fetch_data(deckfile_location)
    k8s_provider = ensure_cluster(
        data_aux.deckfile, config, ignore_cluster, do_install=False
    )
    logger.info("Stopping cluster")

    del data_aux
    k8s_provider.stop()


def stop_command(args):
    stop_cluster(args.Deckfile, ignore_cluster=args.no_cluster)
