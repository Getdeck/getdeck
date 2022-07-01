import logging
from typing import Callable

from getdeck.api import stopwatch, remove
from getdeck.configuration import default_configuration

logger = logging.getLogger("deck")


@stopwatch
def run_deck(
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
    from kubernetes.client import V1Namespace, V1ObjectMeta
    from kubernetes.client.rest import ApiException
    from getdeck.k8s import k8s_create_or_patch
    from getdeck.k8s import get_ingress_display

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
        logger.info("Cluster already exists, starting it")
        k8s_provider.start()
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
            logger.debug(file.name)
            logger.debug(file.content)
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
        logger.info(
            f"If these ingress hosts do not resolve to localhost, you can configure them manually "
            f"by executing\n"
            f"'deck hosts write {deckfile_location}'.\n"
            f"This command may require administrative rights, e.g. under linux"
            f"'sudo -E deck hosts write {deckfile_location}'"
        )
    logger.info(f"Published ports are: {k8s_provider.get_ports()}")
    if notes := deckfile.get_deck(deck_name).notes:
        logger.info(notes)

    if wait:
        _wait_ready(config, generated_deck, timeout)
    return True


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
