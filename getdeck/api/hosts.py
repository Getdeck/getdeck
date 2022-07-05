import logging
import socket

from python_hosts import Hosts, HostsEntry

from getdeck.api import stopwatch
from getdeck.configuration import default_configuration
from getdeck.k8s import get_ingress_hosts
from getdeck.utils import read_deckfile_from_location

logger = logging.getLogger("deck")


@stopwatch
def run_hosts(
    deckfile_location: str,
    host_action: str,
    config=default_configuration,
) -> bool:
    deckfile = read_deckfile_from_location(deckfile_location, config)
    namespace = deckfile.get_deck().namespace or "default"
    deck_hosts = get_ingress_hosts(config, namespace)
    hosts = Hosts()

    if host_action == "list":

        logger.info("Ingress hosts:")
        for host in deck_hosts:
            logger.info(f"{host}")

    elif host_action == "remove":
        logger.debug("Removing hosts from hosts file...")
        for host in deck_hosts:
            hosts.remove_all_matching(name=host)
        hosts.write()
        logger.info("Hosts have been removed from hosts file...")

    elif host_action == "write":

        logger.info("Writing hosts to hosts file...")
        new_entry = HostsEntry(entry_type="ipv4", address="127.0.0.1", names=deck_hosts)
        hosts.add([new_entry])
        hosts.write()
        logger.info("Hosts should resolve to '127.0.0.1' now.")

    else:
        logger.error(f"Unknown host action '{host_action}'")

    return True


def verify_host(host) -> bool:
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        return False
    return ip == "127.0.0.1"


def verify_all_hosts(*hosts):
    return all(verify_host(host) for host in hosts)
