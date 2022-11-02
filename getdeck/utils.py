import logging
import os
import subprocess
from time import sleep

from semantic_version import Version

from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.file import Deckfile
from getdeck.provider.abstract import AbstractProvider
from getdeck.provider.errors import NotSupportedError
from getdeck.provider.types import ProviderType


logger = logging.getLogger("deck")


def ensure_cluster(
    deckfile: Deckfile,
    config: ClientConfiguration,
    ignore_cluster: bool = False,
    do_install: bool = True,
    no_input: bool = False,
) -> AbstractProvider:
    from kubernetes.client.rest import ApiException
    from getdeck.provider.factory import cluster_factory

    cluster_config = deckfile.get_cluster()
    if ignore_cluster or cluster_config is None:
        # no cluster is set in the Deckfile
        from kubernetes.config import kube_config

        _, active_context = kube_config.list_kube_config_contexts()

        try:
            logger.warning(
                "The current cluster context is not created with this Deckfile"
            )
            confirm = input(
                f"You are operating with context '{active_context['name']}'. "
                f"Do you want to continue? [y/N] "
            )
            if confirm.lower() != "y":
                logger.info("Operation aborted")
                exit()
        except ApiException:
            logger.critical(
                "There is no valid cluster connection available and no cluster is defined in the Deckfile"
            )
        return cluster_factory.get(
            ProviderType("kubectlctx"),
            config,
            name=active_context["name"],
            native_config=None,
        )
    else:
        k8s_provider = cluster_config.get_provider(config)
        try:
            try:
                try:
                    version = k8s_provider.version()
                except NotSupportedError:
                    version = None

                if cluster_config.minVersion and version:
                    if Version(cluster_config.minVersion) > version:
                        logger.warning(
                            f"{cluster_config.provider} is installed in version {version}, "
                            f"but minVersion is {cluster_config.minVersion}"
                        )
                        if do_install:
                            if not no_input:
                                confirm = input(
                                    f"Do you want to update your local {cluster_config.provider}? [y/N] "
                                )
                                if confirm.lower() != "y":
                                    logger.info("Operation aborted")
                                    exit()
                            k8s_provider.update()
                else:
                    logger.debug(
                        f"{cluster_config.provider} is installed in version {version}"
                    )
            except FileNotFoundError:
                #  this K8s provider is not yet installed
                logger.warning(
                    f"The required cluster provider {cluster_config.provider} is currently not "
                    f"installed on your system"
                )
                if do_install:
                    if not no_input:
                        confirm = input(
                            f"Do you want to install {cluster_config.provider} on your local system? [y/N] "
                        )
                        if confirm.lower() != "y":
                            logger.info("Operation aborted")
                            exit()
                    k8s_provider.install()
        except KeyboardInterrupt:
            print()  # add a newline
            raise RuntimeError("Operation aborted")
        return k8s_provider


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
