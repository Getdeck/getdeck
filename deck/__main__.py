#!/usr/bin/env python3.10
import argparse
import logging

from deck import configuration
from deck.api import get_available_decks, run_deck, remove_cluster

logger = logging.getLogger("deck")
parser = argparse.ArgumentParser(
    prog="deck",
    description="The Deck CLI. For more help please visit: https://getdeck.dev",
)
action = parser.add_subparsers(dest="action", help="the action to be performed")
parser.add_argument("-d", "--debug", action="store_true", help="add debug output")
parser.add_argument("Deckfile", help="the deck.yaml location (as file, git or https)")

# list all decks of the given deck.yaml
list_parser = action.add_parser("list")

# rollout the cluster and install the deck from the given deck.yaml
get_parser = action.add_parser("get")
get_parser.add_argument("--name", help="the Deck that you want to run", required=False)

remove_parser = action.add_parser("remove")
remove_parser.add_argument("--name", help="the Deck that you want to remove", required=False)
remove_parser.add_argument("--cluster", help="Remove the local Kubernetes cluster", action="store_true", required=False)

check_parser = action.add_parser("check")

version_parser = action.add_parser("version")


def main():
    args = parser.parse_args()
    if args.debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
    logger.addHandler(configuration.console)
    match args.action:
        case "list":
            decks = get_available_decks(args.Deckfile)
            names = [deck.name for deck in decks]
            logger.info(names)

        case "get":
            run_deck(args.Deckfile, args.name)
        case "remove":
            if args.cluster:
                remove_cluster(args.Deckfile)
        case "check":
            logger.info("check action")
        case "version":
            logger.info("version action")
        case _:
            parser.print_help()


if __name__ == "__main__":  # noqa
    try:
        main()
        exit(0)
    except Exception as e:
        logger.fatal(f"There was an error running Deck: {e}")
        exit(1)
