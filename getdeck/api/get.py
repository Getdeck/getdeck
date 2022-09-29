import logging
import shutil
from typing import Callable

from getdeck.api import stopwatch, remove
from getdeck.api.hosts import verify_all_hosts
from getdeck.configuration import default_configuration
from getdeck.k8s import create_namespace
from getdeck.provider.types import ProviderType

logger = logging.getLogger("deck")


@stopwatch
def run_deck(  # noqa: C901
    deckfile_location: str,
    deck_name: str = None,
    ignore_cluster: bool = False,
    wait: bool = False,
    timeout: int = 120,
    config=default_configuration,
    progress_callback: Callable = None,
) -> bool:
    from getdeck.sources.utils import prepare_k8s_workload_for_deck
    from getdeck.utils import read_deckfile_from_location, ensure_cluster
    from getdeck.k8s import k8s_create_or_patch, get_ingress_rules

    cluster_created = False
    if progress_callback:
        progress_callback(0)

    deckfile, working_dir_path, is_temp_dir = read_deckfile_from_location(
        deckfile_location, config
    )
    if progress_callback:
        progress_callback(5)
    #
    # 1. set up a local K8s cluster
    #
    k8s_provider = ensure_cluster(deckfile, config, ignore_cluster, do_install=True)
    if progress_callback:
        progress_callback(10)
    #  1.b check or set up local cluster
    if not k8s_provider.exists():
        k8s_provider.create()
        cluster_created = True
    else:
        logger.info("Cluster already exists, starting it")
        k8s_provider.start()

    if progress_callback:
        progress_callback(20)

    # change api for beiboot
    if k8s_provider.kubernetes_cluster_type == ProviderType.BEIBOOT:
        _old_kubeconfig = config.kubeconfig
        config.kubeconfig = k8s_provider.get_kubeconfig()
        config._init_kubeapi(context="default")

    #
    # 2. generate the Deck's workload
    #
    try:
        generated_deck = prepare_k8s_workload_for_deck(
            config, deckfile, deck_name, working_dir_path
        )
    except Exception as e:
        if cluster_created:
            # remove this just created cluster as it probably is in an inconsistent state from the beginning
            if k8s_provider.kubernetes_cluster_type == ProviderType.BEIBOOT:
                config.kubeconfig = _old_kubeconfig
                config._init_kubeapi()
            remove.remove_cluster(deckfile_location, config)
        raise e

    logger.info(f"Applying Deck {generated_deck.name}")
    if progress_callback:
        progress_callback(30)
    #
    # 3. send the manifests to this cluster
    #
    logger.info("Installing the workload to the cluster")

    if generated_deck.namespace != "default":
        create_namespace(config, generated_deck.namespace)

    if progress_callback:
        progress_callback(50)

    total = len(generated_deck.files)
    logger.info(f"Installing {total} files(s)")
    _available_namespace = [generated_deck, "default"]
    for i, file in enumerate(generated_deck.files):
        try:
            logger.debug(file.name)
            logger.debug(file.content)
            logger.debug(file.namespace)
            if file.namespace and file.namespace not in _available_namespace:
                create_namespace(config, file.namespace)
                _available_namespace.append(file.namespace)
            k8s_create_or_patch(
                config, file.content, file.namespace or generated_deck.namespace
            )
            if progress_callback:
                progress_callback(max(50, int(i / total * 50) - 1))
        except Exception as e:
            logger.error(
                "There was an error installing the workload. Now removing the cluster."
            )
            if cluster_created:
                if k8s_provider.kubernetes_cluster_type == ProviderType.BEIBOOT:
                    config.kubeconfig = _old_kubeconfig
                    config._init_kubeapi()
                # remove this just created cluster as it probably is in an inconsistent state from the beginning
                remove.remove_cluster(deckfile_location, config)
            raise e

    if progress_callback:
        progress_callback(100)
    logger.info(f"All workloads from Deck {generated_deck.name} applied")

    ingress_rules = get_ingress_rules(config, generated_deck.namespace)
    if ingress_rules:
        for host, path in ingress_rules:
            logger.info(f"Ingress: {host} -> {path}")
        handle_hosts_resolution(deckfile_location, deckfile, deck_name)
    logger.info(f"Published ports are: {k8s_provider.get_ports()}")
    if notes := deckfile.get_deck(deck_name).notes:
        logger.info(notes)

    if is_temp_dir:
        shutil.rmtree(working_dir_path)
    if wait:
        _wait_ready(config, generated_deck, timeout)
    return True


def handle_hosts_resolution(deckfile_location, deckfile, deck_name):
    deck = deckfile.get_deck(deck_name)
    deck_hosts = deck.hosts
    deck_flag = " "
    if deck_name:
        deck_flag = f" --name {deck_name} "
    if not verify_all_hosts(*deck_hosts):
        logger.warning("Some of your deck hosts do not resolve to localhost.")
        logger.info(
            f"If these ingress hosts do not resolve to localhost, you can configure them manually "
            f"by executing\n"
            f"'deck hosts write{deck_flag}{deckfile_location}'.\n"
            f"with admin rights."
        )


def _wait_ready(config, generated_deck, timeout):
    from getdeck.utils import wait_for_pods_ready

    logger.info(
        f"Now waiting for all Pods in namespace '{generated_deck.namespace}' to become "
        f"ready within {timeout} seconds."
    )
    ready = wait_for_pods_ready(
        config, namespace=generated_deck.namespace, timeout=timeout
    )
    if not ready:
        raise RuntimeError(
            f"The Pods of this Deck did not become ready in time (timout was {timeout} s)."
        )
