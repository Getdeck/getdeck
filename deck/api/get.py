import logging

from semantic_version import Version

from deck.api import stopwatch
from deck.configuration import default_configuration
from deck.sources.utils import prepare_k8s_workload_for_deck
from deck.utils import read_deckfile_from_location, ensure_cluster

logger = logging.getLogger("deck")

@stopwatch
def run_deck(deckfile_location: str, deck_name: str = None, config=default_configuration) -> bool:
    deckfile = read_deckfile_from_location(deckfile_location, config)
    #
    # 1. set up a local K8s cluster
    #
    k8s_provider = ensure_cluster(deckfile, config, do_install=True)

    #  1.b check or set up local cluster
    if not k8s_provider.exists():
        k8s_provider.create()
    else:
        logger.info("Cluster already exists")

    #
    # 2. generate the Deck's workload
    #
    generated_deck = prepare_k8s_workload_for_deck(config, deckfile, deck_name)

    #
    # 3. send the manifests to this cluster
    #
    config.kubeconfig = k8s_provider.get_kubeconfig()
    print(config.K8S_CORE_API.list_namespace())




    return True