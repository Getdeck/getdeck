from getdeck.telemetry.telemetry import CliTelemetry
import logging


logger = logging.getLogger("deck")

try:
    telemetry = CliTelemetry()
except Exception:
    telemetry = False


def telemetry_command(args):
    if not telemetry:
        logger.info("Telemetry is not working on your machine. No action taken.")
        return
    if args.off and not args.on:
        telemetry.off()
    elif args.on and not args.off:
        telemetry.on()
    else:
        logger.info("Invalid flags. Please use either --off or --on.")
