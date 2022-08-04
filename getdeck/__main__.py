#!/usr/bin/env python3.10
import argparse
import logging
import os

from getdeck.api import stop_cluster

os.environ["PYOXIDIZER"] = "1"

logger = logging.getLogger("deck")
parser = argparse.ArgumentParser(
    prog="deck",
    description="The Deck CLI. For more help please visit: https://getdeck.dev",
)
action = parser.add_subparsers(dest="action", help="the action to be performed")
parser.add_argument("-d", "--debug", action="store_true", help="add debug output")

# list all decks of the given deck.yaml
list_parser = action.add_parser("list")
list_parser.add_argument(
    "Deckfile", help="the deck.yaml location (as file, git or https)"
)

# rollout the cluster and install the deck from the given deck.yaml
get_parser = action.add_parser("get")
get_parser.add_argument("--name", help="the Deck that you want to run", required=False)
get_parser.add_argument(
    "-I",
    "--no-cluster",
    help="do not set up the cluster, use current kubectl context",
    action="store_true",
    required=False,
)
get_parser.add_argument(
    "-W",
    "--wait",
    help="Wait for the Pods of the Deck to become ready",
    action="store_true",
    required=False,
)


def check_positive(value):
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("timeout must be a positive integer value")
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("timeout must be a positive integer value")
    return ivalue


get_parser.add_argument(
    "-T",
    "--timeout",
    help="Timeout (in seconds, default 120) for the Pods of the Deck to become ready; if exceeded the run fails",
    default=120,
    type=check_positive,
    required=False,
)
get_parser.add_argument(
    "Deckfile", help="the deck.yaml location (as file, git or https)"
)

remove_parser = action.add_parser("remove")
remove_parser.add_argument(
    "--name", help="the Deck that you want to remove", required=False
)
remove_parser.add_argument(
    "--cluster",
    help="Remove the local Kubernetes cluster",
    action="store_true",
    required=False,
)
remove_parser.add_argument(
    "-I",
    "--no-cluster",
    help="do not set up the cluster, use current kubectl context",
    action="store_true",
    default=False,
    required=False,
)
remove_parser.add_argument(
    "Deckfile", help="the deck.yaml location (as file, git or https)"
)

stop_parser = action.add_parser("stop")
stop_parser.add_argument(
    "-I",
    "--no-cluster",
    help="do not set up the cluster, use current kubectl context",
    action="store_true",
    required=False,
)
stop_parser.add_argument(
    "Deckfile", help="the deck.yaml location (as file, git or https)"
)

version_parser = action.add_parser("version")


def main():
    from getdeck import configuration
    from getdeck.api import get_available_decks, run_deck, remove_cluster, remove_deck

    try:
        args = parser.parse_args()
        if args.debug:
            logger.setLevel(logging.DEBUG)
        else:
            logger.setLevel(logging.INFO)

        logger.addHandler(configuration.console)
        if args.action == "list":
            decks = get_available_decks(args.Deckfile)
            names = [deck.name for deck in decks]
            logger.info(names)
        elif args.action == "get":
            if args.wait:
                run_deck(
                    args.Deckfile,
                    args.name,
                    ignore_cluster=args.no_cluster,
                    wait=True,
                    timeout=int(args.timeout),
                )
            else:
                run_deck(args.Deckfile, args.name, ignore_cluster=args.no_cluster)
        elif args.action == "remove":
            if args.cluster:
                remove_cluster(args.Deckfile, ignore_cluster=args.no_cluster)
            else:
                remove_deck(args.Deckfile, args.name, ignore_cluster=args.no_cluster)
        elif args.action == "stop":
            stop_cluster(args.Deckfile, ignore_cluster=args.no_cluster)
        elif args.action == "version":
            logger.info(f"Deck version: {configuration.__VERSION__}")
        else:
            parser.print_help()
        exit(0)
    except Exception as e:
        logger.fatal(f"There was an error running Deck: {e}")
        exit(1)


if __name__ == "__main__":  # noqa
    main()
