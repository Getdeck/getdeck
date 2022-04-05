import logging
from typing import Callable

from getdeck.api import stopwatch, remove
from getdeck.configuration import default_configuration
from getdeck.k8s import get_ingress_display

logger = logging.getLogger("deck")


@stopwatch
def run_deck(
    deckfile_location: str,
    deck_name: str = None,
    ignore_cluster: bool = False,
    config=default_configuration,
    progress_callback: Callable = None,
) -> bool:
    from getdeck.sources.utils import prepare_k8s_workload_for_deck
    from getdeck.utils import read_deckfile_from_location, ensure_cluster
    from kubernetes.client import V1Namespace, V1ObjectMeta
    from kubernetes.client.rest import ApiException
    from getdeck.k8s import k8s_create_or_patch

    cluster_created = False
    if progress_callback:
        progress_callback(0)
    deckfile = read_deckfile_from_location(deckfile_location, config)
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
        logger.info("Cluster already exists")
    if progress_callback:
        progress_callback(20)
    #
    # 2. generate the Deck's workload
    #
    try:
        generated_deck = prepare_k8s_workload_for_deck(config, deckfile, deck_name)
    except Exception as e:
        if cluster_created:
            # remove this just created cluster as it probably is in an inconsistent state from the beginning
            remove.remove_cluster(deckfile_location, config)
        raise e
    logger.info(f"Applying Deck {generated_deck.name}")
    if progress_callback:
        progress_callback(30)
    #
    # 3. send the manifests to this cluster
    #
    logger.info("Installing the workload to the cluster")
    config.kubeconfig = k8s_provider.get_kubeconfig()
    if generated_deck.namespace != "default":
        try:
            config.K8S_CORE_API.create_namespace(
                body=V1Namespace(metadata=V1ObjectMeta(name=generated_deck.namespace))
            )
        except ApiException as e:
            if e.status == 409:
                # namespace does already exist
                pass
            else:
                raise e
    if progress_callback:
        progress_callback(50)
    total = len(generated_deck.files)
    logger.info(f"Installing {total} files(s)")
    for i, file in enumerate(generated_deck.files):
        try:
            k8s_create_or_patch(config, file.content, generated_deck.namespace)
            if progress_callback:
                progress_callback(max(50, int(i / total * 50) - 1))
        except Exception as e:
            logger.error(
                "There was an error installing the workload. Now removing the cluster."
            )
            if cluster_created:
                # remove this just created cluster as it probably is in an inconsistent state from the beginning
                remove.remove_cluster(deckfile_location, config)
            raise e
    if progress_callback:
        progress_callback(100)
    logger.info(f"All workloads from Deck {generated_deck.name} applied")

    ingress = get_ingress_display(config, generated_deck.namespace)
    if ingress:
        for path in ingress:
            logger.info(f"Ingress: {path[0]} -> {path[1]}")
    logger.info(f"Published ports are: {k8s_provider.get_ports()}")
    return True
