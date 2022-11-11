import logging
from getdeck import api

from getdeck.cli import stopwatch
from getdeck.cli.utils import get_cluster_initialize_arguments
from getdeck.configuration import default_configuration
from getdeck.fetch.fetch import fetch_data

logger = logging.getLogger("deck")


@stopwatch
def stop_command(args):
    location = args.Deckfile
    ignore_cluster = args.no_cluster
    config = default_configuration

    data_aux = fetch_data(location)
    cluster_config = data_aux.deckfile.get_cluster()
    del data_aux

    provider_type, name, native_config = get_cluster_initialize_arguments(
        cluster_config=cluster_config, ignore_cluster=ignore_cluster, no_input=False
    )

    cluster = api.cluster.initialize(
        provider_type=provider_type,
        name=name,
        native_config=native_config,
        config=config,
    )

    logger.info("Stopping cluster")
    cluster.stop()
