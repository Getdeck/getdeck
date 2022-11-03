#!/usr/bin/env python3
import argparse
import logging
import os
import traceback

os.environ["PYOXIDIZER"] = "1"

logger = logging.getLogger("deck")

ARGUMENT_DECKFILE_HELP = "the deck.yaml location (as file, git or https)"


def check_positive(value):
    try:
        ivalue = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError("timeout must be a positive integer value")
    if ivalue <= 0:
        raise argparse.ArgumentTypeError("timeout must be a positive integer value")
    return ivalue


parser = argparse.ArgumentParser(
    prog="deck",
    description="The Deck CLI. For more help please visit: https://getdeck.dev",
)
action = parser.add_subparsers(dest="action", help="the action to be performed")
parser.add_argument("-d", "--debug", action="store_true", help="add debug output")

# list
list_parser = action.add_parser("list")
list_parser.add_argument(
    "Deckfile", help=ARGUMENT_DECKFILE_HELP, nargs="?", default="."
)

# get
get_parser = action.add_parser("get")
get_parser.add_argument("--name", help="the Deck that you want to run", required=False)
get_parser.add_argument(
    "-I",
    "--no-cluster",
    help="Do not set up the cluster, use current kubectl context",
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

get_parser.add_argument(
    "-T",
    "--timeout",
    help="Timeout (in seconds, default 120) for the Pods of the Deck to become ready; if exceeded the run fails",
    default=120,
    type=check_positive,
    required=False,
)
get_parser.add_argument(
    "-y",
    "--no-input",
    help="Disable prompting for input",
    action="store_true",
    default=False,
    required=False,
)
get_parser.add_argument("Deckfile", help=ARGUMENT_DECKFILE_HELP, nargs="?", default=".")

# remove
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
    help="Do not set up the cluster, use current kubectl context",
    action="store_true",
    default=False,
    required=False,
)
remove_parser.add_argument(
    "Deckfile", help=ARGUMENT_DECKFILE_HELP, nargs="?", default="."
)

# stop
stop_parser = action.add_parser("stop")
stop_parser.add_argument(
    "-I",
    "--no-cluster",
    help="Do not set up the cluster, use current kubectl context",
    action="store_true",
    required=False,
)
stop_parser.add_argument(
    "Deckfile", help=ARGUMENT_DECKFILE_HELP, nargs="?", default="."
)

# version
version_parser = action.add_parser("version")

# hosts
hosts_parser = action.add_parser("hosts")
hosts_parser.add_argument("host_action", help="list/write/remove")
hosts_parser.add_argument(
    "Deckfile", help=ARGUMENT_DECKFILE_HELP, nargs="?", default="."
)
hosts_parser.add_argument(
    "--name", help="The Deck whose hosts will be considered", required=False
)

# telemetry
telemetry_parser = action.add_parser("telemetry")
telemetry_parser.add_argument("--off", help="Turn off telemetry", action="store_true")
telemetry_parser.add_argument("--on", help="Turn on telemetry", action="store_true")


def main():
    from getdeck.cli.console import console_setup
    from getdeck.cli.get import get_command
    from getdeck.cli.hosts import hosts_command
    from getdeck.cli.list import list_command
    from getdeck.cli.remove import remove_command
    from getdeck.cli.stop import stop_command
    from getdeck.cli.telemetry import telemetry_command
    from getdeck.cli.version import version_command

    args = parser.parse_args()
    debug = args.debug

    try:
        console_setup(debug=debug)

        command = {
            "list": list_command,
            "get": get_command,
            "remove": remove_command,
            "stop": stop_command,
            "version": version_command,
            "hosts": hosts_command,
            "telemetry": telemetry_command,
        }.get(args.action, None)

        # unknown / invalid command
        if not command:
            parser.print_help()
            exit(0)

        command(args=args)
        exit(0)
    except Exception as e:
        if debug:
            traceback.print_exc()
        logger.critical(f"There was an error running deck: {e}")
        exit(1)


if __name__ == "__main__":  # noqa
    main()
