import logging
import os
import subprocess
import tempfile

import requests
from git import Repo
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
    if ref.lower().startswith("git") or ref.lower().endswith(".git"):
        return "git"
    if ref.lower().startswith("http"):
        return "http"
    if ref.lower().startswith("https"):
        return "https"
    return None


def read_deckfile_from_location(location: str, config: ClientConfiguration) -> Deckfile:
    protocol = sniff_protocol(location)
    if location == ".":
        # load default file from this location
        return config.deckfile_selector.get(
            os.path.join(os.getcwd(), configuration.DECKFILE_FILE)
        )
    elif protocol is None:
        # this is probably a file system location
        if os.path.isfile(location):
            logger.debug("Is file location")
            return config.deckfile_selector.get(location)
        else:
            raise RuntimeError(f"Cannot identify {location} as Deckfile")
    elif protocol == "git":
        if "#" in location:
            ref, rev = location.split("#")
        else:
            ref = location
            rev = "HEAD"
        tmp_dir = tempfile.TemporaryDirectory()
        try:
            repo = Repo.clone_from(ref, tmp_dir.name)
            repo.git.checkout(rev)
            deckfile = config.deckfile_selector.get(
                os.path.join(tmp_dir.name, configuration.DECKFILE_FILE)
            )
            tmp_dir.cleanup()
            return deckfile
        except Exception:
            tmp_dir.cleanup()
            raise RuntimeError(f"Cannot checkout {rev} from {ref}")
    elif protocol in ["http", "https"]:
        download = tempfile.NamedTemporaryFile()
        try:
            logger.debug(f"Requesting {location}")
            with requests.get(location, stream=True, timeout=10.0) as res:
                res.raise_for_status()
                for chunk in res.iter_content(chunk_size=4096):
                    if chunk:
                        download.write(chunk)
                download.flush()
            deckfile = config.deckfile_selector.get(download.name)
            download.close()
            return deckfile
        except Exception as e:
            download.close()
            raise RuntimeError(
                f"Cannot read Deckfile from http(s) location {location}: {e}"
            )
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
        version = k8s_provider.version()

        try:
            if cluster_config.minVersion:
                if Version(cluster_config.minVersion) > version:
                    logger.warning(
                        f"{cluster_config.provider} is installed in version {version}, "
                        f"but minVersion is {cluster_config.minVersion}"
                    )
                    if do_install:
                        k8s_provider.update()
            else:
                logger.info(
                    f"{cluster_config.provider} is installed in version {version}"
                )
        except FileNotFoundError:
            if do_install:
                logger.info(
                    f"{cluster_config.provider} is not installed, going to install now"
                )
                #  this K8s provider is not yet installed
                k8s_provider.install()
        return k8s_provider


class CMDWrapper(object):
    base_command = None

    class CMDException(Exception):
        pass

    def __init__(self, debug_output=False):
        self._debug_output = debug_output

    def _execute(
        self, arguments, stdin: str = None, print_output: bool = False
    ) -> subprocess.Popen:
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
