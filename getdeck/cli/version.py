import logging


logger = logging.getLogger("deck")


def version_command(args):
    from getdeck import configuration

    logger.info(f"Deck version: {configuration.__VERSION__}")
