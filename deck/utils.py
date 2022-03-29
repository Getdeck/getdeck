import logging
import os
import subprocess

from deck import configuration
from deck.configuration import ClientConfiguration
from deck.deckfile.file import Deckfile

logger = logging.getLogger("deck")


def sniff_protocol():
    return None


def read_deckfile_from_location(location: str, config: ClientConfiguration) -> Deckfile:
    protocol = sniff_protocol()
    if location == ".":
        # load default file from this location
        return config.deckfile_selector.get(os.path.join(os.getcwd(), configuration.DECKFILE_FILE))
    elif protocol is None:
        # this is probably a file system location
        if os.path.isfile(location):
            logger.debug("Is file location")
            return config.deckfile_selector.get(location)


class CMDWrapper(object):
    base_command = None

    class CMDException(Exception):
        pass

    def __init__(self, debug_output=False):
        self._debug_output = debug_output

    def _execute(self, arguments, stdin: str = None, print_output: bool = False) -> subprocess.Popen:
        cmd = [self.base_command] + arguments
        kwargs = self._get_kwargs()
        process = subprocess.Popen(cmd, **kwargs)
        if stdin:
            process.communicate(stdin)
        try:
            if print_output:
                for stdout_line in iter(process.stdout.readline, ""):
                    print(stdout_line, end="", flush=True)
            process.wait()
        except KeyboardInterrupt:
            try:
                process.terminate()
            except OSError:
                pass
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                pass
        return process

    def _run(self, arguments) -> subprocess.CompletedProcess:
        cmd = [self.base_command] + arguments
        return subprocess.run(cmd, env=self._get_environment())

    def _get_kwargs(self):
        kwargs = {"env": self._get_environment(), "encoding": "utf-8"}
        if not self._debug_output:
            kwargs.update(
                {
                    "stdout": subprocess.PIPE,
                    "close_fds": True,
                    "stderr": subprocess.STDOUT,
                }
            )
        return kwargs

    def _get_environment(self):
        env = os.environ.copy()
        return env