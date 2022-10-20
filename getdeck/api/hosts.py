import logging
import os
import shutil
import socket

from python_hosts import Hosts, HostsEntry

from getdeck.api import stopwatch
from getdeck.configuration import default_configuration
from getdeck.fetch.fetch import fetch_data

logger = logging.getLogger("deck")


@stopwatch
def run_hosts(
    deckfile_location: str,
    host_action: str,
    deck_name: str = None,
    config=default_configuration,
) -> bool:
    deckfile, working_dir_path, is_temp_dir = fetch_data(
        deckfile_location, deck_name=deck_name
    )
    deck = deckfile.get_deck(deck_name)
    deck_hosts = deck.hosts

    hosts = Hosts()
    if deck_hosts:
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
            new_entry = HostsEntry(
                entry_type="ipv4", address="127.0.0.1", names=deck_hosts
            )
            hosts.add([new_entry])
            hosts.write()
            logger.info("Hosts should resolve to '127.0.0.1' now.")

        else:
            logger.error(f"Unknown host action '{host_action}'")
    else:
        logger.info("No hosts specified in Deckfile")

    # TODO: refactor/remove?
    if is_temp_dir and os.path.isdir(working_dir_path):
        shutil.rmtree(working_dir_path)

    return True


def verify_host(host) -> bool:
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        return False
    return ip == "127.0.0.1"


def verify_all_hosts(*hosts):
    return all(verify_host(host) for host in hosts)
