import logging
from typing import Callable
from getdeck import api
from getdeck.cli.utils import get_cluster_initialize_arguments

from getdeck.configuration import default_configuration
from getdeck.cli import stopwatch
from getdeck.fetch.fetch import fetch_data


logger = logging.getLogger("deck")


@stopwatch
def remove_cluster(
    deckfile_location: str,
    config=default_configuration,
    ignore_cluster: bool = False,
) -> bool:
    data_aux = fetch_data(deckfile_location)
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

    if cluster.exists():
        cluster.delete()
    else:
        logger.info("Cluster does not exist")

    return True


@stopwatch
def remove_deck(
    deckfile_location: str,
    deck_name: str,
    ignore_cluster: bool = False,
    config=default_configuration,
    progress_callback: Callable = None,
) -> bool:
    if progress_callback:
        progress_callback(0)

    from getdeck.k8s import k8s_delete_object
    from getdeck.sources.utils import prepare_k8s_workload_for_deck

    data_aux = fetch_data(deckfile_location, deck_name=deck_name)
    cluster_config = data_aux.deckfile.get_cluster()

    if progress_callback:
        progress_callback(10)

    provider_type, name, native_config = get_cluster_initialize_arguments(
        cluster_config=cluster_config, ignore_cluster=ignore_cluster, no_input=False
    )

    cluster = api.cluster.initialize(
        provider_type=provider_type,
        name=name,
        native_config=native_config,
        config=config,
    )

    if progress_callback:
        progress_callback(20)

    config.kubeconfig = cluster.get_kubeconfig()
    if cluster.exists():
        generated_deck = prepare_k8s_workload_for_deck(config, data_aux, deck_name)
        logger.info(f"Removing Deck {generated_deck.name}")
        if progress_callback:
            progress_callback(30)
        config.kubeconfig = cluster.get_kubeconfig()
        if progress_callback:
            progress_callback(50)
        total = len(generated_deck.files)
        for i, file in enumerate(generated_deck.files):
            try:
                k8s_delete_object(config, file.content, generated_deck.namespace)
                if progress_callback:
                    progress_callback(max(50, int(i / total * 50) - 1))
            except RuntimeError as e:
                logger.error(f"There was an error removing a workload: {e}")
                continue
            except Exception as e:
                logger.error(f"There was an error removing the workload: {e}")
                raise e
        if progress_callback:
            progress_callback(100)
        logger.info(f"All workloads from Deck {generated_deck.name} removed")
    else:
        logger.info("Cluster does not exist")

    del data_aux
    return True


def remove_command(args):
    if args.cluster:
        remove_cluster(args.Deckfile, ignore_cluster=args.no_cluster)
    else:
        remove_deck(args.Deckfile, args.name, ignore_cluster=args.no_cluster)
