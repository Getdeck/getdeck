import logging
import socket

from python_hosts import Hosts, HostsEntry

from getdeck.cli import stopwatch
from getdeck.fetch.fetch import fetch_data

logger = logging.getLogger("deck")


@stopwatch
def run_hosts(
    deckfile_location: str,
    host_action: str,
    deck_name: str = None,
) -> bool:
    data_aux = fetch_data(deckfile_location, deck_name=deck_name)
    deck = data_aux.deckfile.get_deck(deck_name)
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

    del data_aux
    return True


def verify_host(host) -> bool:
    try:
        ip = socket.gethostbyname(host)
    except socket.gaierror:
        return False
    return ip == "127.0.0.1"


def verify_all_hosts(*hosts):
    return all(verify_host(host) for host in hosts)


def hosts_command(args):
    run_hosts(
        args.Deckfile,
        args.host_action,
        deck_name=args.name,
    )
