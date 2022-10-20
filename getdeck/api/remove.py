import logging
import os
import shutil
from typing import Callable

from getdeck.configuration import default_configuration
from getdeck.api import stopwatch


logger = logging.getLogger("deck")


@stopwatch
def remove_cluster(
    deckfile_location: str,
    config=default_configuration,
    ignore_cluster: bool = False,
) -> bool:
    from getdeck.utils import fetch_data, ensure_cluster

    deckfile, working_dir_path, is_temp_dir = fetch_data(deckfile_location)
    k8s_provider = ensure_cluster(deckfile, config, ignore_cluster, do_install=False)
    if k8s_provider.exists():
        k8s_provider.delete()
    else:
        logger.info("Cluster does not exist")

    # TODO: refactor/remove?
    if is_temp_dir and os.path.isdir(working_dir_path):
        shutil.rmtree(working_dir_path)

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

    from getdeck.utils import fetch_data, ensure_cluster
    from getdeck.k8s import k8s_delete_object
    from getdeck.sources.utils import prepare_k8s_workload_for_deck

    deckfile, working_dir_path, is_temp_dir = fetch_data(
        deckfile_location, deck_name=deck_name
    )
    if progress_callback:
        progress_callback(10)
    k8s_provider = ensure_cluster(deckfile, config, ignore_cluster, do_install=False)
    if progress_callback:
        progress_callback(20)

    config.kubeconfig = k8s_provider.get_kubeconfig()
    if k8s_provider.exists():
        generated_deck = prepare_k8s_workload_for_deck(
            config, deckfile, deck_name, working_dir_path
        )
        logger.info(f"Removing Deck {generated_deck.name}")
        if progress_callback:
            progress_callback(30)
        config.kubeconfig = k8s_provider.get_kubeconfig()
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

    # TODO: refactor/remove?
    if is_temp_dir and os.path.isdir(working_dir_path):
        shutil.rmtree(working_dir_path)

    return True
