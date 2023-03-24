import logging
from typing import Callable
from getdeck import api

from getdeck.cli import stopwatch, remove
from getdeck.cli.hosts import verify_all_hosts
from getdeck.cli.utils import get_cluster_initialize_arguments, install_provider
from getdeck.configuration import default_configuration

logger = logging.getLogger("deck")


@stopwatch
def run_deck(  # noqa: C901
    deckfile_location: str,
    deck_name: str = None,
    ignore_cluster: bool = False,
    wait: bool = False,
    timeout: int = 120,
    no_input: bool = False,
    progress_callback: Callable = None,
) -> bool:
    from getdeck.sources.utils import prepare_k8s_workload_for_deck
    from getdeck.k8s import k8s_create_or_patch, get_ingress_rules
    from getdeck.fetch.fetch import fetch_data

    if progress_callback:
        progress_callback(0)

    data_aux = fetch_data(deckfile_location, deck_name=deck_name)
    cluster_config = data_aux.deckfile.get_cluster()

    if progress_callback:
        progress_callback(5)

    # 1. set up a local K8s cluster
    provider_type, name, native_config = get_cluster_initialize_arguments(
        cluster_config=cluster_config, ignore_cluster=ignore_cluster, no_input=no_input
    )

    cluster = api.cluster.initialize(
        provider_type=provider_type,
        name=name,
        native_config=native_config,
        config=default_configuration,
    )

    install_provider(cluster, cluster_config, do_install=True, no_input=no_input)

    if progress_callback:
        progress_callback(10)

    #  1.b check or set up local cluster
    if not ignore_cluster:
        logger.info("Cluster already exists, starting it")
        cluster_created = cluster.start_or_create()
    else:
        cluster_created = False

    if progress_callback:
        progress_callback(20)

    # # change kubeconfig for beiboot
    # if cluster.kubernetes_cluster_type == ProviderType.BEIBOOT:
    #     _old_kubeconfig = config.kubeconfig
    #     config.kubeconfig = cluster.get_kubeconfig()
    #     config._init_kubeapi(context="default")

    #
    # 2. generate the Deck's workload
    #
    try:
        generated_deck = prepare_k8s_workload_for_deck(
            cluster.get_config(), data_aux, deck_name
        )
    except Exception as e:
        if cluster_created:
            # remove this just created cluster as it probably is in an inconsistent state from the beginning
            # if cluster.kubernetes_cluster_type == ProviderType.BEIBOOT:
            #     config.kubeconfig = _old_kubeconfig
            #     config._init_kubeapi()
            remove.remove_cluster(deckfile_location, cluster.get_config())
        raise e

    if progress_callback:
        progress_callback(30)

    # 3. send the manifests to this cluster
    logger.info(f"Applying Deck {generated_deck.name}")
    logger.info("Installing the workload to the cluster")

    if generated_deck.namespace != "default":
        cluster.create_namespace(generated_deck.namespace)

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
                cluster.create_namespace(file.namespace)
                _available_namespace.append(file.namespace)

            k8s_create_or_patch(
                cluster.get_config(),
                file.content,
                file.namespace or generated_deck.namespace,
            )
            if progress_callback:
                progress_callback(max(50, int(i / total * 50) - 1))
        except Exception as e:
            logger.error("There was an error installing the workload.")
            if cluster_created:
                logger.info("Now removing the cluster.")
                # remove this just created cluster as it probably is in an inconsistent state from the beginning
                remove.remove_cluster(deckfile_location, cluster.get_config())
            raise e

    if progress_callback:
        progress_callback(100)
    logger.info(f"All workloads from Deck {generated_deck.name} applied")

    ingress_rules = get_ingress_rules(cluster.get_config(), generated_deck.namespace)
    if ingress_rules:
        for host, path in ingress_rules:
            logger.info(f"Ingress: http://{host} -> {path}")
        handle_hosts_resolution(deckfile_location, data_aux.deckfile, deck_name)
    logger.info(f"Published ports are: {cluster.get_ports()}")
    if notes := data_aux.deckfile.get_deck(deck_name).notes:
        logger.info(notes)

    del data_aux

    if wait:
        _wait_ready(cluster.get_config(), generated_deck, timeout)

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


def get_command(args):
    if args.wait:
        wait = True
        timeout = int(args.timeout)
    else:
        wait = False
        timeout = None

    run_deck(
        args.Deckfile,
        args.name,
        ignore_cluster=args.no_cluster,
        wait=wait,
        timeout=timeout,
        no_input=args.no_input,
    )
