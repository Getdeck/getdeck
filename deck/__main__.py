#!/usr/bin/env python3.10
import argparse
import logging

from deck import configuration

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

remove_parser = action.add_parser("remove")

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
            logger.info("list action")
        case "get":
            logger.info("get action")
        case "remove":
            logger.info("remove action")
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
