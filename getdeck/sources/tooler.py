import io
import logging
import os
import subprocess
import sys
import tempfile
from functools import cached_property
from typing import List, Union

from git import Repo

from getdeck.configuration import ClientConfiguration
from getdeck.sources import tooler
from getdeck.sources.file import FileFetcher
from getdeck.sources.types import K8sSourceFile

logger = logging.getLogger("deck")


def run(
    config: ClientConfiguration, cmd: Union[str, List], volume_mounts: List[str] = None
) -> str:
    import docker

    # check if this image is already present on this machine
    try:
        config.DOCKER.images.get(config.TOOLER_USER_IMAGE)
    except docker.errors.ImageNotFound:
        build_user_container(config)
    if type(cmd) == list:
        cmd = " ".join(cmd)

    if gnupg_socket := gnupg_agent_socket_path():
        volume_mounts.extend(
            [
                f"{gnupg_socket}:{gnupg_socket}",
                f"{gnupg_home_path()}:/home/tooler/.gnupg",
            ]
        )

    exec_cmd = f'bash -c "{cmd}"'
    logger.debug("Tooler running with: " + str(exec_cmd))
    logger.debug("Tooler mounted: " + str(volume_mounts))
    content = config.DOCKER.containers.run(
        config.TOOLER_USER_IMAGE,
        exec_cmd,
        volumes=volume_mounts,
        remove=True,
        oom_kill_disable=True,
    )
    return content


def gnupg_home_path() -> str:
    result = subprocess.run("echo $GNUPGHOME", shell=True, stdout=subprocess.PIPE)
    if result.stdout.decode("utf-8").strip():
        return result.stdout.decode("utf-8").strip()
    else:
        return os.path.expanduser("~/.gnupg")


def gnupg_agent_socket_path() -> str:
    """
    :return: the agent socket to mount
    """
    try:
        result = subprocess.run(
            ["gpgconf", "--list-dir", "agent-extra-socket"], stdout=subprocess.PIPE
        )
        return result.stdout.decode("utf-8").strip()
    except FileNotFoundError:
        # gnupg is not installed
        return ""


def build_user_container(config: ClientConfiguration):
    logger.info("Building a local Tooler image for source generation")
    if sys.platform != "win32":
        uid = os.getuid()
        gid = os.getgid()
    else:
        uid = 1000
        gid = 1000

    if sys.platform in ["darwin", "win32"]:
        user_group_add = "RUN addgroup -S tooler && adduser -S tooler -G tooler"
    else:
        user_group_add = "RUN addgroup -g ${GROUP_ID} -S tooler && adduser -u ${USER_ID} -S tooler -G tooler"

    Dockerfile = io.BytesIO(
        (
            f"FROM {config.TOOLER_BASE_IMAGE}\n"
            "ARG USER_ID\n"
            "ARG GROUP_ID\n"
            f"{user_group_add}\n"
            "RUN chown ${USER_ID}:${GROUP_ID} /sources\n"
            "RUN chown ${USER_ID}:${GROUP_ID} /output\n"
            "WORKDIR /sources\n"
            "USER tooler\n"
            "ENV HELM_DATA_HOME=/usr/local/share/helm\n"
        ).encode("utf-8")
    )
    build_args = {"USER_ID": str(uid), "GROUP_ID": str(gid)}
    logger.debug(Dockerfile.read().decode("utf-8"))
    # update tooler base image
    # config.DOCKER.images.pull("tooler")
    image, build_logs = config.DOCKER.images.build(
        fileobj=Dockerfile,
        rm=True,
        forcerm=True,
        buildargs=build_args,
        tag=config.TOOLER_USER_IMAGE,
    )


class ToolerFetcher(FileFetcher):
    SOURCES = "/sources"
    OUTPUT = "/output"

    def fetch_content(self, **kwargs) -> List[K8sSourceFile]:
        raise NotImplementedError

    def fetch_local(self, **kwargs):
        raise NotImplementedError

    def fetch_remote(self, git=False):
        cmd = self.build_command()
        try:
            if git:
                self._checkout_git()
            self.run_tooler(cmd)
            return self.collect_workload_files()
        finally:
            self.cleanup()

    def fetch_http(self, **kwargs) -> List[K8sSourceFile]:
        return self.fetch_remote(git=False)

    def fetch_git(self, **kwargs) -> List[K8sSourceFile]:
        return self.fetch_remote(git=True)

    def _checkout_git(self):
        logger.debug(f"Cloning from {self.source.ref} to {self.tmp_source.name}")
        repo = Repo.clone_from(self.source.ref, self.tmp_source.name)
        if self.source.targetRevision:
            repo.git.checkout(self.source.targetRevision)

    @cached_property
    def tmp_output(self):
        return tempfile.TemporaryDirectory()

    @cached_property
    def tmp_source(self):
        return tempfile.TemporaryDirectory()

    def cleanup(self):
        self.tmp_output.cleanup()
        self.tmp_source.cleanup()

    def build_command(self) -> List[str]:
        raise NotImplementedError

    def run_tooler(self, cmd):
        tooler.run(
            self.config,
            cmd,
            volume_mounts=[
                f"{self.tmp_source.name}:{self.SOURCES}",
                f"{self.tmp_output.name}:{self.OUTPUT}",
            ],
        )

    def collect_workload_files(self):
        raise NotImplementedError
