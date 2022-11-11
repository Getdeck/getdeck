import logging
import os
import subprocess
from time import sleep

from getdeck.configuration import ClientConfiguration

logger = logging.getLogger("deck")


class CMDWrapper(object):
    base_command = None

    class CMDException(Exception):
        pass

    def __init__(self, debug_output=False):
        self._debug_output = debug_output

    def _execute(
        self,
        arguments,
        stdin: str = None,
        print_output: bool = False,
        base_command: str = None,
    ) -> subprocess.Popen:
        if base_command:
            cmd = [base_command] + arguments
        else:
            cmd = [self.base_command] + arguments
        kwargs = self._get_kwargs()
        process = subprocess.Popen(cmd, **kwargs)
        if stdin:
            process.communicate(stdin)
        try:
            if print_output:
                try:
                    for stdout_line in iter(process.stdout.readline, ""):
                        print(stdout_line, end="", flush=True)
                except Exception as e:
                    logger.warning(f"Failed to display process output: {str(e)}")
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


def wait_for_pods_ready(
    config: ClientConfiguration, namespace: str = "default", timeout: int = 120
):
    _ready = False
    i = 0

    def _pod_ready(_pod):
        if not _pod.status.conditions:
            return False
        return (
            sorted(_pod.status.conditions, key=lambda x: x.last_transition_time)[
                -1
            ].type
            == "ContainersReady"
        )

    def _print_message():
        if i % 10 == 0:
            #  print a notification after 10s
            logger.info(
                f"Waiting for all Pods of the Deck to become ready ({i} s / {timeout} s)"
            )

    while i <= timeout:
        try:
            pods = config.K8S_CORE_API.list_namespaced_pod(namespace)
            if len(pods.items) == 0:
                sleep(1)
                i = i + 1
                _print_message()
                continue
            for pod in pods.items:
                if not _pod_ready(pod):
                    sleep(1)
                    i = i + 1
                    _print_message()
                    break
            else:
                _ready = True
                break
        except Exception as e:
            logger.debug(e)
            continue
    return _ready
