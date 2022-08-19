import logging
import os
import shutil
import subprocess
import tempfile
from time import sleep
from typing import Optional, Tuple

import requests
from git import Repo, GitError
from semantic_version import Version

from getdeck import configuration
from getdeck.configuration import ClientConfiguration
from getdeck.deckfile.file import Deckfile
from getdeck.provider.abstract import AbstractK8sProvider
from getdeck.provider.types import K8sProviderType

logger = logging.getLogger("deck")


def sniff_protocol(ref: str):
    if "#" in ref:
        ref, rev = ref.split("#")
    ref_lo = ref.lower()
    if ref_lo.startswith("git") or ref_lo.endswith(".git"):
        return "git"
    if ref_lo.startswith("https"):
        return "https"
    if ref_lo.startswith("http"):
        return "http"
    if ref_lo[0] in "./~":
        return "local"
    return None


def read_deckfile_from_location(location: str, config: ClientConfiguration) -> Tuple[Deckfile, Optional[str]]:
    protocol = sniff_protocol(location)
    if location == ".":
        # load default file from this location
        return config.deckfile_selector.get(
            os.path.join(os.getcwd(), configuration.DECKFILE_FILE)
        )
    elif protocol == "git":
        if "#" in location:
            ref, rev = location.split("#")
        else:
            ref = location
            rev = "HEAD"
        tmp_dir = tempfile.mkdtemp()
        try:
            repo = Repo.clone_from(ref, tmp_dir)
            repo.git.checkout(rev)
            deckfile = config.deckfile_selector.get(
                os.path.join(tmp_dir, configuration.DECKFILE_FILE)
            )
            return deckfile, tmp_dir
        except GitError as e:
            shutil.rmtree(tmp_dir)
            raise RuntimeError(f"Cannot checkout {rev} from {ref}: {e}")
        except Exception as e:
            shutil.rmtree(tmp_dir)
            raise e
    elif protocol in ["http", "https"]:
        download = tempfile.NamedTemporaryFile(delete=False)
        try:
            logger.debug(f"Requesting {location}")
            with requests.get(location, stream=True, timeout=10.0) as res:
                res.raise_for_status()
                for chunk in res.iter_content(chunk_size=4096):
                    if chunk:
                        download.write(chunk)
                download.flush()
            download.close()
            deckfile = config.deckfile_selector.get(download.name)
            os.remove(download.name)
            return deckfile, None
        except Exception as e:
            download.close()
            os.remove(download.name)
            raise RuntimeError(
                f"Cannot read Deckfile from http(s) location {location}: {e}"
            )
    elif protocol in (None, "local"):
        # this is probably a file system location
        if os.path.isfile(location):
            logger.debug("Is file location")
            return config.deckfile_selector.get(location), os.path.dirname(location)
        else:
            raise RuntimeError(f"Cannot identify {location} as Deckfile")
    else:
        raise RuntimeError("Cannot read Deckfile")


def ensure_cluster(
    deckfile: Deckfile,
    config: ClientConfiguration,
    ignore_cluster: bool = False,
    do_install: bool = True,
) -> AbstractK8sProvider:
    from kubernetes.client.rest import ApiException
    from getdeck.provider.factory import kubernetes_cluster_factory

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
        return kubernetes_cluster_factory.get(
            K8sProviderType("KubectlCtx"),
            config,
            name=active_context["name"],
            native_config=None,
        )
    else:
        k8s_provider = cluster_config.get_provider(config)
        try:
            try:
                version = k8s_provider.version()
                if cluster_config.minVersion:
                    if Version(cluster_config.minVersion) > version:
                        logger.warning(
                            f"{cluster_config.provider} is installed in version {version}, "
                            f"but minVersion is {cluster_config.minVersion}"
                        )
                        if do_install:
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
